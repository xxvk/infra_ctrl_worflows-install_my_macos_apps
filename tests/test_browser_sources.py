#!/usr/bin/env python3
"""Hermetic contracts for Safari bookmark and Reading List source discovery."""

from __future__ import annotations

import copy
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import browser_sources  # noqa: E402


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

    def test_macos_data_is_preferred_for_live_reads_and_export_is_evidence_fallback(self) -> None:
        contract = browser_sources.load_contract()
        sources = {item["id"]: item for item in contract["sources"]}
        adapter = sources["macos_data_cli"]
        self.assertEqual(adapter["support"], "supported_cli_adapter")
        self.assertTrue(adapter["item_enumeration_supported"])
        self.assertEqual(adapter["minimum_read_version"], "0.8.0")
        self.assertEqual(adapter["direct_internal_store_access"], "forbidden")
        self.assertEqual(adapter["minimum_local_write_version"], "0.8.1")
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

    def test_macos_data_probe_accepts_0_8_1_local_only_write_contract(self) -> None:
        def runner(command, **_kwargs):
            if command[-1] == "--version":
                return subprocess.CompletedProcess(command, 0, stdout="0.8.1\n", stderr="")
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=(
                    "Safari 0.8 commands:\n"
                    "  bookmarks list\n  bookmarks query\n  bookmarks get\n"
                    "  reading-list list\n"
                    "  bookmarks create|edit|move|delete\n"
                    "  folders create|rename|move|delete\n"
                    "  Guarded local-only bookmark CRUD\n"
                ),
                stderr="",
            )

        result = browser_sources.inspect_macos_data(
            binary=Path("/fixture/macos-data"),
            runner=runner,
        )

        self.assertTrue(result["present"])
        self.assertEqual(result["version"], "0.8.1")
        self.assertEqual(result["read_status"], "available")
        self.assertEqual(result["ordinary_bookmark_write_status"], "available_local_only")
        self.assertEqual(result["sync_status"], "local_only")
        self.assertFalse(result["private_item_content_emitted"])

    def test_macos_data_probe_keeps_0_8_0_read_only(self) -> None:
        def runner(command, **_kwargs):
            if command[-1] == "--version":
                return subprocess.CompletedProcess(command, 0, stdout="0.8.0\n", stderr="")
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="bookmarks list bookmarks query bookmarks get reading-list list\n",
                stderr="",
            )

        result = browser_sources.inspect_macos_data(
            binary=Path("/fixture/macos-data"),
            runner=runner,
        )

        self.assertEqual(result["read_status"], "available")
        self.assertEqual(result["ordinary_bookmark_write_status"], "unavailable_public_cli")
        self.assertEqual(result["sync_status"], "not_verified")

    def test_macos_data_probe_rejects_old_binary_and_selects_export_fallback(self) -> None:
        def runner(command, **_kwargs):
            stdout = "0.7.2\n" if command[-1] == "--version" else "macos-data 0.7.2\n"
            return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

        result = browser_sources.inspect_macos_data(
            binary=Path("/fixture/macos-data"),
            runner=runner,
        )

        self.assertEqual(result["read_status"], "version_too_old")
        self.assertEqual(result["selected_read_source"], "safari_export_zip")

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
                macos_data_binary=root / "missing-macos-data",
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

    def test_safari_inspection_selects_macos_data_for_local_only_write(self) -> None:
        def runner(command, **_kwargs):
            if command[-1] == "--version":
                return subprocess.CompletedProcess(command, 0, stdout="0.8.1\n", stderr="")
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=(
                    "bookmarks list bookmarks query bookmarks get reading-list list "
                    "bookmarks create|edit|move|delete folders create|rename|move|delete "
                    "Guarded local-only"
                ),
                stderr="",
            )

        result = browser_sources.inspect_safari(
            app_path=Path("/fixture/Safari.app"),
            home=Path("/fixture/home"),
            macos_data_binary=Path("/fixture/macos-data"),
            runner=runner,
        )

        self.assertEqual(
            result["execution_priority"]["local_only_write"],
            ["macos_data_cli"],
        )


if __name__ == "__main__":
    unittest.main()
