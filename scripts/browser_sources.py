#!/usr/bin/env python3
"""Validate browser-source policy and inspect Safari capability metadata only."""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "references" / "browser-data-sources.json"
EXPECTED_SOURCE_IDS = {
    "icloud_safari_sync",
    "macos_data_cli",
    "safari_apple_events",
    "safari_export_zip",
    "safari_internal_bookmarks_plist",
    "safari_web_extension_bookmarks",
    "safari_webdriver",
    "ssreadinglist",
}
ALLOWED_SUPPORT = {
    "add_only_no_enumeration",
    "native_sync_and_bookmark_restore",
    "supported_cli_adapter",
    "supported_user_mediated",
    "ui_and_add_only",
    "unsupported_internal",
    "unverified_on_current_release",
    "web_content_automation_only",
}

Runner = Callable[..., subprocess.CompletedProcess[str]]
MACOS_DATA_MINIMUM_READ_VERSION = (0, 8, 0)
MACOS_DATA_MINIMUM_LOCAL_WRITE_VERSION = (0, 8, 1)


class BrowserSourceError(RuntimeError):
    """Raised when a browser-source contract is unsafe or inconsistent."""


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BrowserSourceError(f"cannot read browser source contract: {exc}") from exc
    if not isinstance(value, dict):
        raise BrowserSourceError("browser source contract must be an object")
    return value


def validate_contract(contract: dict[str, Any]) -> None:
    if contract.get("schema_version") != 1:
        raise BrowserSourceError("schema_version must be 1")
    if contract.get("kind") != "browser_data_source_contract":
        raise BrowserSourceError("kind must be browser_data_source_contract")
    scope = contract.get("scope")
    if not isinstance(scope, dict) or scope.get("browsers") != ["safari"]:
        raise BrowserSourceError("BR-01 current scope must contain Safari only")
    if scope.get("content_kinds") != ["bookmark", "reading_list"]:
        raise BrowserSourceError("Safari scope must contain bookmark and reading_list")
    privacy = contract.get("privacy")
    if not isinstance(privacy, dict):
        raise BrowserSourceError("privacy boundary is required")
    prohibited = set(privacy.get("prohibited_inputs", []))
    required_prohibited = {"cookies", "history", "passwords", "payment cards", "session material"}
    if not required_prohibited.issubset(prohibited):
        raise BrowserSourceError("privacy boundary omits prohibited Safari data classes")
    if privacy.get("export_selection") != "bookmarks_and_reading_list_only":
        raise BrowserSourceError(
            "Safari export selection must be bookmarks_and_reading_list_only"
        )
    if privacy.get("raw_export_git_policy") != "never_track":
        raise BrowserSourceError("raw Safari exports must never be tracked")

    native_gates = contract.get("native_api_gates")
    if not isinstance(native_gates, dict):
        raise BrowserSourceError("Safari native API gates are required")
    if native_gates.get("settings_class") != "SFSafariSettings":
        raise BrowserSourceError("Safari settings class gate is invalid")
    if native_gates.get("export_sheet_method") != "openExportBrowsingDataSettingsWithCompletionHandler:":
        raise BrowserSourceError("Safari export-sheet method gate is invalid")
    if native_gates.get("selected_sdk_status") != "documented_but_symbol_absent":
        raise BrowserSourceError("selected SDK status must preserve the verified API mismatch")
    if native_gates.get("runtime_selector_status") != "absent_on_verified_beta":
        raise BrowserSourceError("runtime selector status must preserve the verified beta mismatch")
    if native_gates.get("item_enumeration_supported") is not False:
        raise BrowserSourceError("SFSafariSettings must not become an item source")
    if native_gates.get("fallback") != "safari_file_export_browsing_data_bookmarks_and_reading_list_only":
        raise BrowserSourceError("Safari native API fallback is invalid")

    sources = contract.get("sources")
    if not isinstance(sources, list):
        raise BrowserSourceError("sources must be a list")
    seen: set[str] = set()
    for source in sources:
        if not isinstance(source, dict) or not isinstance(source.get("id"), str):
            raise BrowserSourceError("every source requires an id")
        source_id = source["id"]
        if source_id in seen:
            raise BrowserSourceError(f"duplicate source id: {source_id}")
        seen.add(source_id)
        if source.get("browser") != "safari":
            raise BrowserSourceError(f"{source_id} must remain Safari-scoped")
        if source.get("support") not in ALLOWED_SUPPORT:
            raise BrowserSourceError(f"{source_id} has unsupported classification")
        if not isinstance(source.get("item_enumeration_supported"), bool):
            raise BrowserSourceError(f"{source_id} requires item_enumeration_supported")
        if source.get("support") == "supported_user_mediated":
            evidence = source.get("official_evidence")
            if not isinstance(evidence, list) or not evidence:
                raise BrowserSourceError(f"{source_id} requires official Apple evidence")
            if not all(url.startswith(("https://developer.apple.com/", "https://support.apple.com/")) for url in evidence):
                raise BrowserSourceError(f"{source_id} evidence must use official Apple domains")

    if seen != EXPECTED_SOURCE_IDS:
        raise BrowserSourceError("source ids must match the reviewed Safari source set")
    by_id = {source["id"]: source for source in sources}
    export = by_id["safari_export_zip"]
    if export.get("content_kinds") != ["bookmark", "reading_list"]:
        raise BrowserSourceError("official export must carry bookmarks and Reading List")
    if export.get("selection_policy") != ["bookmarks", "reading_list"]:
        raise BrowserSourceError("official export must select bookmarks and Reading List only")
    if export.get("supported_archive_layouts") != [
        "single_bookmarks_html_with_reading_list_subfolder",
        "separate_bookmarks_and_reading_list_html",
    ]:
        raise BrowserSourceError("official selected export archive layouts are invalid")
    if export.get("ignorable_auxiliary_members") != ["appledouble_metadata"]:
        raise BrowserSourceError("official selected export metadata boundary is invalid")
    if export.get("reading_list_container_id") != "com.apple.ReadingList":
        raise BrowserSourceError("Reading List container id is invalid")
    if export.get("profile_scope") != "shared_across_safari_profiles":
        raise BrowserSourceError("Safari bookmark profile scope is invalid")
    for source_id, source in by_id.items():
        if source_id not in {"macos_data_cli", "safari_export_zip"} and source.get("item_enumeration_supported"):
            raise BrowserSourceError(f"{source_id} must not be selected for item enumeration")
    adapter = by_id["macos_data_cli"]
    if adapter.get("support") != "supported_cli_adapter":
        raise BrowserSourceError("macos-data must remain the preferred supported CLI adapter")
    if adapter.get("content_kinds") != ["bookmark", "reading_list"]:
        raise BrowserSourceError("macos-data must enumerate bookmarks and Reading List")
    if adapter.get("minimum_read_version") != "0.8.0":
        raise BrowserSourceError("macos-data minimum read version must be 0.8.0")
    if adapter.get("direct_internal_store_access") != "forbidden":
        raise BrowserSourceError("the skill must not bypass the macos-data Safari adapter")
    if adapter.get("minimum_local_write_version") != "0.8.1":
        raise BrowserSourceError("macos-data minimum local write version must be 0.8.1")
    if adapter.get("ordinary_bookmark_write_status") != "available_local_only":
        raise BrowserSourceError("macos-data ordinary bookmark writes must preserve the local-only boundary")
    if adapter.get("cross_device_sync_status") != "not_verified":
        raise BrowserSourceError("local plist mutation must not claim cross-device sync")
    internal = by_id["safari_internal_bookmarks_plist"]
    if internal.get("support") != "unsupported_internal" or internal.get("content_access") != "forbidden":
        raise BrowserSourceError("internal Safari plist must remain forbidden")
    webdriver = by_id["safari_webdriver"]
    if webdriver.get("mcp_mode") != "/usr/bin/safaridriver --mcp":
        raise BrowserSourceError("Safari MCP mode declaration is invalid")
    if webdriver.get("personal_information_access") != "none":
        raise BrowserSourceError("Safari MCP must not claim personal-information access")


def validate(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    try:
        contract = load_contract(path)
        validate_contract(contract)
    except BrowserSourceError as exc:
        return {"schema_version": 1, "status": "failed", "errors": [str(exc)]}
    return {
        "schema_version": 1,
        "status": "passed",
        "browsers": contract["scope"]["browsers"],
        "content_kinds": contract["scope"]["content_kinds"],
        "preferred_live_read_source": "macos_data_cli",
        "immutable_evidence_source": "safari_export_zip",
        "errors": [],
    }


def _version_tuple(value: str) -> tuple[int, int, int] | None:
    match = re.search(r"(?<!\d)(\d+)\.(\d+)\.(\d+)(?!\d)", value)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def inspect_macos_data(
    *,
    binary: Path | None = None,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    """Probe only the public macos-data CLI contract; never emit Safari items."""

    configured = os.environ.get("MACOS_DATA_CLI")
    command = str(binary) if binary is not None else configured or shutil.which("macos-data")
    base = {
        "adapter": "macos-data",
        "privacy_boundary": "public_cli_capability_metadata_only",
        "private_item_content_emitted": False,
        "ordinary_bookmark_write_status": "unavailable_public_cli",
        "sync_status": "not_verified",
        "selected_read_source": "safari_export_zip",
    }
    if not command:
        return {**base, "present": False, "version": None, "read_status": "binary_unavailable"}
    try:
        version_result = runner(
            [command, "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
        help_result = runner(
            [command, "--help"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return {**base, "present": False, "version": None, "read_status": "probe_failed"}

    raw_version = (version_result.stdout or version_result.stderr).strip()
    parsed = _version_tuple(raw_version)
    version = ".".join(str(part) for part in parsed) if parsed else None
    if version_result.returncode != 0 or parsed is None:
        status = "version_unknown"
    elif parsed < MACOS_DATA_MINIMUM_READ_VERSION:
        status = "version_too_old"
    else:
        help_text = f"{help_result.stdout}\n{help_result.stderr}"
        required = ("bookmarks list", "bookmarks query", "bookmarks get", "reading-list list")
        status = "available" if help_result.returncode == 0 and all(marker in help_text for marker in required) else "contract_missing"
    help_text = f"{help_result.stdout}\n{help_result.stderr}"
    local_write_markers = (
        "bookmarks create|edit|move|delete",
        "folders create|rename|move|delete",
        "Guarded local-only",
    )
    local_write_available = (
        status == "available"
        and parsed is not None
        and parsed >= MACOS_DATA_MINIMUM_LOCAL_WRITE_VERSION
        and all(marker in help_text for marker in local_write_markers)
    )
    return {
        **base,
        "present": True,
        "version": version,
        "read_status": status,
        "selected_read_source": "macos_data_cli" if status == "available" else "safari_export_zip",
        "ordinary_bookmark_write_status": (
            "available_local_only" if local_write_available else "unavailable_public_cli"
        ),
        "sync_status": "local_only" if local_write_available else "not_verified",
    }


def inspect_safari(
    *,
    app_path: Path = Path("/Applications/Safari.app"),
    home: Path | None = None,
    safaridriver_path: Path = Path("/usr/bin/safaridriver"),
    macos_data_binary: Path | None = None,
    runner: Runner = subprocess.run,
) -> dict[str, Any]:
    """Inspect app/interface presence without opening Safari bookmark content."""

    home = home or Path.home()
    info_path = app_path / "Contents" / "Info.plist"
    sdef_path = app_path / "Contents" / "Resources" / "Safari.sdef"
    info: dict[str, Any] = {}
    if info_path.is_file():
        try:
            loaded = plistlib.loads(info_path.read_bytes())
            info = loaded if isinstance(loaded, dict) else {}
        except (OSError, plistlib.InvalidFileException):
            info = {}
    try:
        sdef = sdef_path.read_text(encoding="utf-8") if sdef_path.is_file() else ""
    except OSError:
        sdef = ""
    internal_path = home / "Library" / "Safari" / "Bookmarks.plist"
    macos_data = inspect_macos_data(binary=macos_data_binary, runner=runner)
    read_priority = ["macos_data_cli", "safari_export_zip", "manual_safari_export_ui"]
    if macos_data["read_status"] != "available":
        read_priority = ["safari_export_zip", "manual_safari_export_ui"]
    local_write_priority = (
        ["macos_data_cli"]
        if macos_data["ordinary_bookmark_write_status"] == "available_local_only"
        else []
    )
    return {
        "schema_version": 1,
        "kind": "safari_source_capability_inspection",
        "privacy_boundary": "capability_metadata_only",
        "safari": {
            "present": app_path.is_dir(),
            "version": info.get("CFBundleShortVersionString"),
            "build": info.get("CFBundleVersion"),
        },
        "official_export": {
            "support": "supported_user_mediated",
            "local_ui_verification": "manual_or_computer_use_required",
            "selected_categories": "bookmarks_and_reading_list_only",
            "content_read": False,
        },
        "macos_data": macos_data,
        "execution_priority": {
            "live_read": read_priority,
            "immutable_evidence": ["safari_export_zip"],
            "cross_device_write": ["safari_owned_html_import", "supervised_computer_use"],
            "local_only_write": local_write_priority,
            "direct_plist_access_by_skill": "forbidden",
        },
        "apple_events": {
            "dictionary_present": sdef_path.is_file(),
            "show_bookmarks_ui": 'name="show bookmarks"' in sdef,
            "add_reading_list_item": 'name="add reading list item"' in sdef,
            "item_enumeration_supported": False,
        },
        "webdriver": {
            "present": safaridriver_path.is_file(),
            "item_enumeration_supported": False,
        },
        "internal_store": {
            "path_alias": "~/Library/Safari/Bookmarks.plist",
            "present": internal_path.is_file(),
            "readable": os.access(internal_path, os.R_OK),
            "support": "unsupported_internal",
            "content_read": False,
        },
        "private_item_content": "not_read",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate the tracked Safari source contract")
    inspect_parser = subparsers.add_parser("inspect-safari", help="inspect Safari and macos-data capability metadata without reading items")
    inspect_parser.add_argument("--macos-data", type=Path, help="explicit macos-data binary; otherwise use MACOS_DATA_CLI or PATH")
    args = parser.parse_args()
    result = validate() if args.command == "validate" else inspect_safari(macos_data_binary=args.macos_data)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("status", "passed") == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
