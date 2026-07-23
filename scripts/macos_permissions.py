#!/usr/bin/env python3
"""Read-only inventory of macOS permission prerequisites.

macOS does not provide a supported, portable API for reading every TCC grant.
This script therefore records direct capability checks where possible and
marks the remaining permissions for visible System Settings verification. It
never reads or copies the TCC database and never changes a permission.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import plistlib
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
from pathlib import Path

from state_paths import add_state_dir_argument, resolve_state_dir


HOME = Path.home()
CHROME_LOCAL_STATE = HOME / "Library/Application Support/Google/Chrome/Local State"
APP_SCRIPT_DIR = Path(__file__).resolve().parent
TCC_DATABASE = Path("/Library/Application Support/com.apple.TCC/TCC.db")

SERVICE_NAMES = {
    "kTCCServiceAccessibility": "Accessibility",
    "kTCCServiceAppleEvents": "Automation/Apple Events",
    "kTCCServiceBluetoothAlways": "Bluetooth",
    "kTCCServiceCalendar": "Calendars",
    "kTCCServiceCamera": "Camera",
    "kTCCServiceContacts": "Contacts",
    "kTCCServiceDeveloperTool": "Developer Tools",
    "kTCCServiceFileProviderDomain": "Files and Folders",
    "kTCCServiceListenEvent": "Input Monitoring",
    "kTCCServiceMicrophone": "Microphone",
    "kTCCServiceLocation": "Location Services",
    "kTCCServiceMotion": "Motion & Fitness",
    "kTCCServicePhotos": "Photos",
    "kTCCServiceReminders": "Reminders",
    "kTCCServicePostEvent": "Accessibility Post Events",
    "kTCCServiceRemovableVolumes": "Removable Volumes",
    "kTCCServiceScreenCapture": "Screen Recording",
    "kTCCServiceSpeechRecognition": "Speech Recognition",
    "kTCCServiceSystemPolicyAllFiles": "Full Disk Access",
    "kTCCServiceSystemPolicyDesktopFolder": "Desktop Folder",
    "kTCCServiceSystemPolicyDocumentsFolder": "Documents Folder",
    "kTCCServiceSystemPolicyDownloadsFolder": "Downloads Folder",
    "kTCCServiceSystemPolicyNetworkVolumes": "Network Volumes",
    "kTCCServiceSystemPolicySysAdminFiles": "System Administration Files",
    "kTCCServiceSystemPolicyVolumes": "Volumes",
    "kTCCServiceSystemPolicyAppBundles": "App Bundles",
}

ENTITLEMENT_HINTS = {
    "com.apple.security.device.camera": "Camera",
    "com.apple.security.device.audio-input": "Microphone",
    "com.apple.security.device.bluetooth": "Bluetooth",
    "com.apple.security.personal-information.calendars": "Calendars",
    "com.apple.security.personal-information.contacts": "Contacts",
    "com.apple.security.personal-information.location": "Location Services",
    "com.apple.security.personal-information.photos-library": "Photos",
    "com.apple.security.personal-information.reminders": "Reminders",
    "com.apple.security.files.user-selected.read-only": "Files and Folders",
    "com.apple.security.files.user-selected.read-write": "Files and Folders",
    "com.apple.security.files.downloads.read-write": "Downloads Folder",
    "com.apple.security.files.bookmarks.app-scope": "Files and Folders",
    "com.apple.security.network.client": "Network Client",
    "com.apple.security.network.server": "Network Server",
}

CLIENT_CLASSIFICATIONS = {
    "com.logi.cp-dev-mgr": ("Logi Options+ helper", "current_helper"),
    "com.logi.pluginservice": ("Logi Options+ helper", "current_helper"),
    "org.openlogi.agent": ("OpenLogi legacy helper", "legacy_or_removed"),
    "com.openai.chat": ("ChatGPT bundle/helper identity", "current_helper"),
    "com.openai.sky.CUAService": ("ChatGPT Computer Use helper", "current_helper"),
    "ai.perplexity.macv3.perplexityd": ("Perplexity helper", "current_helper"),
    "ai.elementlabs.lmstudio": ("LM Studio helper", "current_helper"),
    "com.google.GoogleUpdater": ("Google updater helper", "current_helper"),
    "com.apple.Terminal": ("macOS Terminal", "system_component"),
    "com.electron.lark": ("Lark/Feishu", "unlisted_or_manual"),
    "com.tencent.meeting": ("Tencent Meeting", "unlisted_or_manual"),
    "com.titanium.OnyX": ("OnyX", "unlisted_or_manual"),
    "com.aspyr.civ5xp.steam": ("Civilization V Steam component", "legacy_or_removed"),
    "com.aspyr.civbe.steam": ("Civilization Beyond Earth Steam component", "legacy_or_removed"),
    "com.atebits.Tweetie2": ("Tweetie/X legacy component", "legacy_or_removed"),
    "com.adguard.mac.vpn": ("AdGuard VPN", "current_app_identity_variant"),
    "com.valvesoftware.steam": ("Steam", "unlisted_or_manual"),
    "com.ayangweb.BongoCat": ("BongoCat", "unlisted_or_manual"),
    "com.electron.wispr-flow": ("Wispr Flow", "legacy_or_removed"),
    "com.serpentiseijapan.LiveTranslation": ("Live Translation", "unlisted_or_manual"),
    "jp.go.nta.CLeTaxWEB": ("Japan e-Tax client", "unlisted_or_manual"),
    "com.xingin.discover": ("RedNote/Xiaohongshu", "current_app_identity_variant"),
    "com.trae.app": ("Trae legacy identity", "legacy_or_removed"),
}

HINT_TO_TCC_SERVICES = {
    "Camera": {"kTCCServiceCamera"},
    "Microphone": {"kTCCServiceMicrophone"},
    "Bluetooth": {"kTCCServiceBluetoothAlways"},
    "Calendars": {"kTCCServiceCalendar"},
    "Contacts": {"kTCCServiceContacts"},
    "Location Services": {"kTCCServiceLocation"},
    "Photos": {"kTCCServicePhotos"},
    "Reminders": {"kTCCServiceReminders"},
    "Downloads Folder": {"kTCCServiceSystemPolicyDownloadsFolder"},
    "Files and Folders": {
        "kTCCServiceSystemPolicyAllFiles",
        "kTCCServiceSystemPolicyDesktopFolder",
        "kTCCServiceSystemPolicyDocumentsFolder",
        "kTCCServiceSystemPolicyDownloadsFolder",
        "kTCCServiceSystemPolicyNetworkVolumes",
    },
}


def readable_file(path: Path) -> dict[str, object]:
    result: dict[str, object] = {"path": str(path), "exists": path.exists()}
    if not path.exists():
        result["status"] = "not_present"
        return result
    try:
        with path.open("rb") as stream:
            stream.read(1)
    except OSError as error:
        result["status"] = "blocked"
        result["error"] = str(error)
    else:
        result["status"] = "verified"
    return result


def permission_rows() -> list[dict[str, object]]:
    chrome_check = readable_file(CHROME_LOCAL_STATE)
    return [
        {
            "id": "full_disk_access",
            "target": "Codex/ChatGPT host process or terminal running this skill",
            "purpose": "Read protected Chrome profile metadata for profile integrity checks",
            "requirement": "required_for_chrome_profile_audit",
            "status": "verified" if chrome_check["status"] == "verified" else "blocked",
            "direct_check": chrome_check,
            "apply_method": "System Settings > Privacy & Security > Full Disk Access",
            "verify_method": "read Chrome Local State without Operation not permitted",
        },
        {
            "id": "accessibility",
            "target": "GUI automation host and selected keyboard/listener tools",
            "purpose": "Allow approved UI automation and accessibility-controlled actions",
            "requirement": "ask_when_required",
            "status": "manual_verification_required",
            "apply_method": "System Settings > Privacy & Security > Accessibility",
            "verify_method": "run the specific UI or listener workflow and record the result",
        },
        {
            "id": "input_monitoring",
            "target": "K240 listener or other approved keyboard tool",
            "purpose": "Receive external keyboard HID events for the documented K240 mappings",
            "requirement": "ask_when_required",
            "status": "manual_verification_required",
            "apply_method": "System Settings > Privacy & Security > Input Monitoring",
            "verify_method": "run the listener and test the documented function keys",
        },
        {
            "id": "screen_recording",
            "target": "approved screenshot or computer-use host",
            "purpose": "Capture the screen only for an explicitly requested visual workflow",
            "requirement": "ask_when_required",
            "status": "manual_verification_required",
            "apply_method": "System Settings > Privacy & Security > Screen Recording",
            "verify_method": "perform the requested screenshot or computer-use test",
        },
        {
            "id": "automation",
            "target": "approved controller and target application",
            "purpose": "Permit Apple Events only for a documented app workflow",
            "requirement": "ask_when_required",
            "status": "manual_verification_required",
            "apply_method": "System Settings > Privacy & Security > Automation",
            "verify_method": "run the named Apple Events workflow and record success",
        },
        {
            "id": "files_and_folders",
            "target": "approved application",
            "purpose": "Allow access to a specifically named user folder when required",
            "requirement": "ask_when_required",
            "status": "manual_verification_required",
            "apply_method": "System Settings > Privacy & Security > Files and Folders",
            "verify_method": "run the named folder read/write check",
        },
        {
            "id": "microphone",
            "target": "approved voice or dictation application",
            "purpose": "Enable voice input only when the selected workflow needs it",
            "requirement": "ask_when_required",
            "status": "manual_verification_required",
            "apply_method": "System Settings > Privacy & Security > Microphone",
            "verify_method": "run the selected voice-input test",
        },
        {
            "id": "camera",
            "target": "approved video application",
            "purpose": "Enable camera access only when the selected workflow needs it",
            "requirement": "ask_when_required",
            "status": "manual_verification_required",
            "apply_method": "System Settings > Privacy & Security > Camera",
            "verify_method": "run the selected camera test",
        },
    ]


def code_signature(path: str) -> dict[str, object]:
    codesign = shutil.which("codesign")
    if not codesign:
        return {"status": "unavailable"}
    result = subprocess.run([codesign, "-dv", "--verbose=4", path], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return {"status": "unavailable", "error": result.stderr.strip()}
    evidence = {}
    for line in result.stderr.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            if key in {"Identifier", "TeamIdentifier", "Authority"}:
                evidence.setdefault(key, []).append(value)
    return {"status": "verified", **evidence}


def entitlements(path: str) -> dict[str, object]:
    codesign = shutil.which("codesign")
    if not codesign:
        return {"status": "unavailable"}
    result = subprocess.run([codesign, "-d", "--entitlements", "-", path], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return {"status": "unavailable", "error": result.stderr.strip()}
    keys = sorted({match.group(1).strip() for match in re.finditer(r"^\s*\[Key\]\s+(.+?)\s*$", result.stdout, re.MULTILINE)})
    if not keys:
        return {"status": "verified", "keys": [], "permission_hints": []}
    return {
        "status": "verified",
        "keys": keys,
        "permission_hints": sorted({ENTITLEMENT_HINTS[key] for key in keys if key in ENTITLEMENT_HINTS}),
    }


def application_inventory() -> list[dict[str, object]]:
    """Reuse the app scanner's complete bundle search and add signing evidence."""
    sys.path.insert(0, str(APP_SCRIPT_DIR))
    try:
        import macos_apps
        applications = macos_apps.installed_apps()
    finally:
        if sys.path and sys.path[0] == str(APP_SCRIPT_DIR):
            sys.path.pop(0)
    rows = []
    for app in applications:
        row = {
            "name": app.get("name"),
            "catalog_name": app.get("catalog_name"),
            "bundle_identifier": app.get("bundle_identifier"),
            "version": app.get("version"),
            "path": app.get("path"),
            "source": app.get("source"),
            "authorization_status": "not_scanned",
            "authorization_evidence": "App discovery completed; per-service authorization scan is the next phase",
        }
        if app.get("path"):
            row["code_signature"] = code_signature(str(app["path"]))
            row["entitlements"] = entitlements(str(app["path"]))
        rows.append(row)
    return rows


def tcc_inventory(applications: list[dict[str, object]]) -> dict[str, object]:
    """Read current TCC rows without copying or modifying the database."""
    if not TCC_DATABASE.is_file():
        return {"status": "unavailable", "reason": "system TCC database not present"}
    try:
        connection = sqlite3.connect(f"file:{TCC_DATABASE}?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT service, client, client_type, auth_value, auth_reason, last_modified "
            "FROM access WHERE client_type = 0"
        ).fetchall()
        connection.close()
    except sqlite3.Error as error:
        return {"status": "unavailable", "reason": str(error)}

    bundle_ids = {str(app.get("bundle_identifier")) for app in applications if app.get("bundle_identifier")}
    matched: dict[str, list[dict[str, object]]] = {bundle: [] for bundle in bundle_ids}
    unmatched = []
    for row in rows:
        client = str(row["client"])
        status = {0: "verified_denied", 1: "verified_limited", 2: "verified_granted"}.get(int(row["auth_value"]), "unknown_value")
        entry = {
            "service": row["service"],
            "service_name": SERVICE_NAMES.get(row["service"], row["service"]),
            "status": status,
            "auth_reason": row["auth_reason"],
            "last_modified": dt.datetime.fromtimestamp(int(row["last_modified"]), dt.timezone.utc).isoformat() if row["last_modified"] else None,
        }
        if client in matched:
            matched[client].append(entry)
        else:
            unmatched.append({"client": client, **entry})
    return {
        "status": "verified",
        "database": str(TCC_DATABASE),
        "application_records": matched,
        "unmatched_clients": unmatched,
        "unmatched_client_classifications": [
            {
                **item,
                "classification": CLIENT_CLASSIFICATIONS.get(item["client"], ("Unknown TCC client", "manual_review"))[0],
                "classification_status": CLIENT_CLASSIFICATIONS.get(item["client"], ("Unknown TCC client", "manual_review"))[1],
            }
            for item in unmatched
        ],
        "note": "No TCC database bytes are copied; rows are read-only evidence and absence of a row is not proof of denial.",
    }


def command_lines(command: list[str]) -> dict[str, object]:
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return {"status": "unavailable", "error": result.stderr.strip(), "returncode": result.returncode}
    return {"status": "verified", "lines": [line for line in result.stdout.splitlines() if line.strip()]}


def path_inventory(*directories: Path) -> dict[str, object]:
    rows = []
    for directory in directories:
        if not directory.is_dir():
            continue
        for path in sorted(directory.iterdir()):
            rows.append(str(path))
    return {"status": "verified", "paths": rows}


def non_app_components() -> dict[str, object]:
    brew = shutil.which("brew")
    brew_data: dict[str, object] = {"status": "unavailable", "reason": "Homebrew not found"}
    if brew:
        formulae = subprocess.run([brew, "list", "--formula", "--versions"], capture_output=True, text=True, check=False)
        casks = subprocess.run([brew, "list", "--cask", "--versions"], capture_output=True, text=True, check=False)
        taps = subprocess.run([brew, "tap"], capture_output=True, text=True, check=False)
        brew_data = {
            "status": "verified" if formulae.returncode == 0 and casks.returncode == 0 and taps.returncode == 0 else "partial",
            "formulae": [line for line in formulae.stdout.splitlines() if line.strip()],
            "casks": [line for line in casks.stdout.splitlines() if line.strip()],
            "taps": [line for line in taps.stdout.splitlines() if line.strip()],
        }
    return {
        "homebrew": brew_data,
        "user_launch_agents": path_inventory(HOME / "Library/LaunchAgents"),
        "system_launch_agents": path_inventory(Path("/Library/LaunchAgents")),
        "system_launch_daemons": path_inventory(Path("/Library/LaunchDaemons")),
        "privileged_helper_tools": path_inventory(Path("/Library/PrivilegedHelperTools")),
        "system_extensions": command_lines(["systemextensionsctl", "list"]),
        "network_services": command_lines(["networksetup", "-listallnetworkservices"]),
        "vpn_connections": command_lines(["scutil", "--nc", "list"]),
        "background_tasks": command_lines(["sfltool", "dumpbtm"]),
    }


def reconcile_entitlements(applications: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for app in applications:
        hints = set(app.get("entitlements", {}).get("permission_hints", []))
        actual = {
            record["service"]: record["status"]
            for record in app.get("tcc_authorizations", [])
        }
        requested_services = {
            service
            for hint in hints
            for service in HINT_TO_TCC_SERVICES.get(hint, set())
        }
        rows.append({
            "bundle_identifier": app.get("bundle_identifier"),
            "name": app.get("name"),
            "requested_hints": sorted(hints),
            "requested_tcc_services": sorted(requested_services),
            "requested_without_record": sorted(service for service in requested_services if service not in actual),
            "requested_and_granted": sorted(service for service in requested_services if actual.get(service) == "verified_granted"),
            "requested_and_denied": sorted(service for service in requested_services if actual.get(service) == "verified_denied"),
            "actual_tcc_records": actual,
        })
    return rows


def permission_summary(applications: list[dict[str, object]], tcc: dict[str, object]) -> dict[str, object]:
    service_counts = {}
    apps_with_denials = []
    apps_with_grants = []
    for app in applications:
        records = app.get("tcc_authorizations", [])
        statuses = {record["service_name"]: record["status"] for record in records}
        for service in app.get("tcc_matrix", {}):
            status = app["tcc_matrix"][service]
            service_counts.setdefault(service, {"verified_granted": 0, "verified_denied": 0, "no_record": 0, "other": 0})
            bucket = status if status in service_counts[service] else "other"
            service_counts[service][bucket] += 1
        denied = sorted(name for name, status in statuses.items() if status == "verified_denied")
        granted = sorted(name for name, status in statuses.items() if status == "verified_granted")
        if denied:
            apps_with_denials.append({"name": app.get("name"), "bundle_identifier": app.get("bundle_identifier"), "services": denied})
        if granted:
            apps_with_grants.append({"name": app.get("name"), "bundle_identifier": app.get("bundle_identifier"), "services": granted})
    return {
        "tcc_database_status": tcc.get("status"),
        "application_count": len(applications),
        "service_counts": service_counts,
        "apps_with_denials": apps_with_denials,
        "apps_with_grants": apps_with_grants,
        "unmatched_client_count": len(tcc.get("unmatched_clients", [])),
        "cleanup_candidates": [
            {"client": row.get("client"), "classification": row.get("classification"), "service": row.get("service_name")}
            for row in tcc.get("unmatched_client_classifications", [])
            if row.get("classification_status") == "legacy_or_removed"
        ],
    }


def scan() -> dict[str, object]:
    applications = application_inventory()
    tcc = tcc_inventory(applications)
    tcc_by_bundle = tcc.get("application_records", {}) if tcc.get("status") == "verified" else {}
    observed_services = sorted({
        str(record.get("service"))
        for records in tcc_by_bundle.values()
        for record in records
    } | set(SERVICE_NAMES))
    for app in applications:
        bundle = app.get("bundle_identifier")
        records = tcc_by_bundle.get(bundle, [])
        app["tcc_authorizations"] = records
        if tcc.get("status") == "verified":
            app["authorization_status"] = "tcc_records_present" if records else "no_record"
        by_service = {record["service"]: record["status"] for record in records}
        app["tcc_matrix"] = {
            service: by_service.get(service, "no_record")
            for service in observed_services
        }
    return {
        "schema_version": 1,
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "user": os.environ.get("USER", "unknown"),
        "platform": platform.platform(),
        "source": "read-only capability checks and app-bundle inventory; TCC database not read",
        "applications": applications,
        "entitlement_tcc_reconciliation": reconcile_entitlements(applications),
        "permission_summary": permission_summary(applications, tcc),
        "tcc_inventory": tcc,
        "observed_tcc_services": [
            {"id": service, "name": SERVICE_NAMES.get(service, service)}
            for service in observed_services
        ],
        "non_app_components": non_app_components(),
        "permissions": permission_rows(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Read-only macOS permission prerequisite inventory")
    add_state_dir_argument(parser)
    parser.add_argument("--output", type=Path, help="write the JSON result to this path")
    args = parser.parse_args()
    result = scan()
    output = args.output
    if output is None:
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        output = resolve_state_dir(args.state_dir) / f"permissions-{stamp}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(output), "permissions": result["permissions"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
