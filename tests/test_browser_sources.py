#!/usr/bin/env python3
"""Hermetic contracts for Safari bookmark and Reading List source discovery."""

from __future__ import annotations

import copy
import json
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import browser_sources  # noqa: E402


READ_ROUTES = (
    "/safari/bookmarks/list",
    "/safari/bookmarks/query",
    "/safari/bookmarks/get",
    "/safari/reading-list/list",
)
WRITE_ROUTES = (
    "/safari/bookmarks/create",
    "/safari/bookmarks/edit",
    "/safari/bookmarks/move",
    "/safari/bookmarks/delete",
    "/safari/folders/create",
    "/safari/folders/rename",
    "/safari/folders/move",
    "/safari/folders/delete",
)


def mpia_runner(
    *,
    version: str = "0.9.3",
    routes: tuple[str, ...] = READ_ROUTES + WRITE_ROUTES,
    bookmarks_readable: bool = True,
    schema_error: str | None = None,
):
    """Build a fake mpia runner covering version, manifest, permission, and read."""

    def runner(command, **_kwargs):
        if command[-1] == "--version":
            return subprocess.CompletedProcess(command, 0, stdout=f"{version}\n", stderr="")
        route = command[-1]
        if route == "/agent/manifest":
            body = {"data": {"routes": [{"path": path} for path in routes]}, "ok": True}
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps(body), stderr="")
        if route == "/safari/permission":
            body = {
                "data": {
                    "bookmarksReadable": bookmarks_readable,
                    "automation": "requiresConsent",
                    "readingListAddAvailable": False,
                },
                "ok": True,
            }
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps(body), stderr="")
        if route == "/safari/bookmarks/list":
            if schema_error:
                body = {"error": {"code": schema_error}, "ok": False}
                # mpia emits error envelopes on stderr with a non-zero exit code.
                return subprocess.CompletedProcess(command, 10, stdout="", stderr=json.dumps(body))
            body = {"data": {"items": []}, "ok": True}
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps(body), stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="{}", stderr="")

    return runner


class BrowserSourceTests(unittest.TestCase):
    def test_repository_safari_source_contract_is_valid(self) -> None:
        result = browser_sources.validate()
        self.assertEqual(result["status"], "passed", result["errors"])
        self.assertEqual(result["browsers"], ["safari"])
        self.assertEqual(result["content_kinds"], ["bookmark", "reading_list"])

    def test_safari_guide_documents_macos_27_export_sheet_gate(self) -> None:
        guide = (ROOT / "references/safari-bookmark-reading-list-sources.md").read_text(encoding="utf-8")
        for expected in (
            "SFSafariSettings.openExportBrowsingDataSettings",
            "@available(macOS 27.0, *)",
            "xcrun --sdk macosx --show-sdk-path",
            "-module-cache-path",
            "File → Export Browsing Data to File…",
        ):
            self.assertIn(expected, guide)

    def test_mpia_is_preferred_for_live_reads_and_export_is_evidence_fallback(self) -> None:
        contract = browser_sources.load_contract()
        sources = {item["id"]: item for item in contract["sources"]}
        adapter = sources["mpia_cli"]
        self.assertEqual(adapter["support"], "supported_cli_adapter")
        self.assertTrue(adapter["item_enumeration_supported"])
        self.assertEqual(adapter["minimum_read_version"], "0.9.3")
        self.assertEqual(adapter["direct_internal_store_access"], "forbidden")
        self.assertEqual(adapter["minimum_local_write_version"], "0.9.3")
        self.assertEqual(adapter["ordinary_bookmark_write_status"], "available_local_only")
        self.assertEqual(adapter["cross_device_sync_status"], "not_verified")

        export = sources["safari_export_zip"]
        self.assertEqual(export["support"], "supported_user_mediated")
        self.assertEqual(export["content_kinds"], ["bookmark", "reading_list"])
        self.assertEqual(export["selection_policy"], ["bookmarks", "reading_list"])
        self.assertEqual(
            export["supported_archive_layouts"],
            [
                "single_bookmarks_html_with_reading_list_subfolder",
                "separate_bookmarks_and_reading_list_html",
            ],
        )
        self.assertEqual(export["ignorable_auxiliary_members"], ["appledouble_metadata"])
        self.assertEqual(export["reading_list_container_id"], "com.apple.ReadingList")
        self.assertEqual(export["profile_scope"], "shared_across_safari_profiles")
        for source_id in (
            "icloud_safari_sync",
            "safari_apple_events",
            "safari_web_extension_bookmarks",
            "safari_webdriver",
            "ssreadinglist",
            "safari_internal_bookmarks_plist",
        ):
            self.assertFalse(sources[source_id]["item_enumeration_supported"])

    def test_mpia_probe_accepts_local_only_write_contract(self) -> None:
        result = browser_sources.inspect_mpia(
            binary=Path("/fixture/mpia"),
            runner=mpia_runner(),
        )

        self.assertTrue(result["present"])
        self.assertEqual(result["version"], "0.9.3")
        self.assertEqual(result["read_status"], "available")
        self.assertEqual(result["ordinary_bookmark_write_status"], "available_local_only")
        self.assertEqual(result["sync_status"], "local_only")
        self.assertFalse(result["private_item_content_emitted"])

    def test_mpia_probe_keeps_read_only_without_write_routes(self) -> None:
        result = browser_sources.inspect_mpia(
            binary=Path("/fixture/mpia"),
            runner=mpia_runner(routes=READ_ROUTES),
        )

        self.assertEqual(result["read_status"], "available")
        self.assertEqual(result["ordinary_bookmark_write_status"], "unavailable_public_cli")
        self.assertEqual(result["sync_status"], "not_verified")

    def test_mpia_probe_rejects_old_binary_and_selects_export_fallback(self) -> None:
        result = browser_sources.inspect_mpia(
            binary=Path("/fixture/mpia"),
            runner=mpia_runner(version="0.9.2"),
        )

        self.assertEqual(result["read_status"], "version_too_old")
        self.assertEqual(result["selected_read_source"], "safari_export_zip")

    def test_mpia_probe_requires_authorization_before_claiming_a_live_path(self) -> None:
        """Declared routes plus a denied grant must not be reported as usable."""

        result = browser_sources.inspect_mpia(
            binary=Path("/fixture/mpia"),
            runner=mpia_runner(bookmarks_readable=False),
        )

        self.assertEqual(result["read_status"], "authorization_required")
        self.assertEqual(result["selected_read_source"], "safari_export_zip")
        self.assertEqual(result["ordinary_bookmark_write_status"], "unavailable_public_cli")

    def test_mpia_probe_rejects_an_unparsable_store_schema(self) -> None:
        """An authorized adapter that cannot parse this Mac's store is not a live path."""

        result = browser_sources.inspect_mpia(
            binary=Path("/fixture/mpia"),
            runner=mpia_runner(schema_error="SAFARI_SCHEMA_UNSUPPORTED"),
        )

        self.assertEqual(result["read_status"], "store_schema_unsupported")
        self.assertEqual(result["store_schema"]["error_code"], "SAFARI_SCHEMA_UNSUPPORTED")
        self.assertFalse(result["store_schema"]["parses"])
        self.assertEqual(result["selected_read_source"], "safari_export_zip")
        self.assertEqual(result["ordinary_bookmark_write_status"], "unavailable_public_cli")
        self.assertFalse(result["private_item_content_emitted"])

    def test_safari_27_capabilities_do_not_become_bookmark_sources(self) -> None:
        contract = browser_sources.load_contract()
        gates = contract["native_api_gates"]
        self.assertEqual(gates["settings_class"], "SFSafariSettings")
        self.assertEqual(
            gates["export_sheet_method"],
            "openExportBrowsingDataSettingsWithCompletionHandler:",
        )
        self.assertEqual(gates["selected_sdk_status"], "documented_but_symbol_absent")
        self.assertEqual(gates["runtime_selector_status"], "absent_on_verified_beta")
        self.assertFalse(gates["item_enumeration_supported"])

        sources = {item["id"]: item for item in contract["sources"]}
        webdriver = sources["safari_webdriver"]
        self.assertEqual(webdriver["mcp_mode"], "/usr/bin/safaridriver --mcp")
        self.assertEqual(webdriver["personal_information_access"], "none")
        self.assertFalse(webdriver["item_enumeration_supported"])

    def test_validator_rejects_internal_plist_as_supported_input(self) -> None:
        contract = copy.deepcopy(browser_sources.load_contract())
        source = next(item for item in contract["sources"] if item["id"] == "safari_internal_bookmarks_plist")
        source["support"] = "supported_user_mediated"
        source["item_enumeration_supported"] = True
        with self.assertRaises(browser_sources.BrowserSourceError):
            browser_sources.validate_contract(contract)

    def test_live_inspection_reads_app_metadata_but_not_bookmark_contents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            app = root / "Safari.app"
            resources = app / "Contents" / "Resources"
            resources.mkdir(parents=True)
            (app / "Contents" / "Info.plist").write_bytes(
                plistlib.dumps({"CFBundleShortVersionString": "27.0", "CFBundleVersion": "fixture"})
            )
            (resources / "Safari.sdef").write_text(
                '<command name="add reading list item"/><command name="show bookmarks"/>',
                encoding="utf-8",
            )
            home = root / "home"
            internal = home / "Library" / "Safari" / "Bookmarks.plist"
            internal.parent.mkdir(parents=True)
            internal.write_text("PRIVATE URL CONTENT MUST NOT BE READ", encoding="utf-8")

            result = browser_sources.inspect_safari(
                app_path=app,
                home=home,
                mpia_binary=root / "missing-mpia",
            )

        self.assertEqual(result["privacy_boundary"], "capability_metadata_only")
        self.assertEqual(result["safari"]["version"], "27.0")
        self.assertTrue(result["apple_events"]["show_bookmarks_ui"])
        self.assertTrue(result["apple_events"]["add_reading_list_item"])
        self.assertFalse(result["apple_events"]["item_enumeration_supported"])
        self.assertTrue(result["internal_store"]["present"])
        self.assertFalse(result["internal_store"]["content_read"])
        self.assertEqual(result["execution_priority"]["local_only_write"], [])
        self.assertNotIn("PRIVATE URL", str(result))

    def test_safari_inspection_selects_mpia_for_local_only_write(self) -> None:
        result = browser_sources.inspect_safari(
            app_path=Path("/fixture/Safari.app"),
            home=Path("/fixture/home"),
            mpia_binary=Path("/fixture/mpia"),
            runner=mpia_runner(),
        )

        self.assertEqual(
            result["execution_priority"]["local_only_write"],
            ["mpia_cli"],
        )
        self.assertEqual(
            result["execution_priority"]["live_read"][0],
            "mpia_cli",
        )

    def test_safari_inspection_falls_back_when_the_store_schema_is_unsupported(self) -> None:
        result = browser_sources.inspect_safari(
            app_path=Path("/fixture/Safari.app"),
            home=Path("/fixture/home"),
            mpia_binary=Path("/fixture/mpia"),
            runner=mpia_runner(schema_error="SAFARI_SCHEMA_UNSUPPORTED"),
        )

        self.assertEqual(result["execution_priority"]["local_only_write"], [])
        self.assertEqual(
            result["execution_priority"]["live_read"],
            ["safari_export_zip", "manual_safari_export_ui"],
        )


if __name__ == "__main__":
    unittest.main()
