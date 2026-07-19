#!/usr/bin/env python3
"""Capture an allowlisted, read-only macOS preference baseline."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import plistlib
import platform
import shutil
import socket
import subprocess
import xml.etree.ElementTree as ET
from xml.parsers.expat import ExpatError
from pathlib import Path

HOME = Path.home()
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "state"
DEFAULT_VALUES = Path(__file__).resolve().parents[1] / "settings/system-preferences-values.json"
ALLOWLIST = {
    "NSGlobalDomain": {"AppleSelectedInputSources", "AppleLocale", "AppleLanguages", "AppleICUForce24HourTime", "AppleMeasurementUnits", "AppleMetricUnits", "AppleCalendar", "AppleFirstWeekday", "AppleInterfaceStyle", "AppleAccentColor", "AppleHighlightColor", "NSNavPanelExpandedStateForSaveMode", "AppleSymbolicHotKeys", "NSUserKeyEquivalents", "NSUserDictionaryReplacementItems", "NSAutomaticSpellingCorrectionEnabled", "NSAutomaticCapitalizationEnabled", "NSAutomaticPeriodSubstitutionEnabled", "NSAutomaticTextCompletionEnabled", "NSAutomaticQuoteSubstitutionEnabled", "NSAutomaticDashSubstitutionEnabled", "com.apple.keyboard.fnState"},
    "com.apple.finder": {"FXPreferredViewStyle", "AppleShowAllFiles", "FXDefaultSearchScope", "ShowPathbar", "ShowStatusBar", "FXEnableExtensionChangeWarning"},
    "com.apple.dock": {"autohide", "tilesize", "orientation", "mineffect", "show-recents", "showhidden", "show-process-indicators", "expose-group-apps"},
    "com.apple.HIToolbox": {"AppleDictationAutoEnable"},
    "com.apple.WindowManager": {"GloballyEnabled", "AppWindowGroupingBehavior", "StageManagerHideWidgets", "AutoHide", "ShowDesktop"},
    "com.apple.screencapture": {"type", "show-thumbnail", "disable-shadow", "include-date", "location"},
    "com.apple.spaces": {"spans-displays"},
    "com.apple.screensaver": {"idleTime", "askForPassword", "askForPasswordDelay"},
}


def export_domain(domain: str) -> dict[str, object]:
    result = subprocess.run(["defaults", "export", domain, "-"], capture_output=True, check=False)
    if result.returncode != 0:
        return {"status": "unavailable", "error": result.stderr.decode(errors="replace").strip()}
    try:
        values = plistlib.loads(result.stdout)
    except (plistlib.InvalidFileException, ValueError) as error:
        return {"status": "unavailable", "error": f"invalid plist: {error}"}
    selected = {}
    for key in ALLOWLIST[domain]:
        if key not in values:
            continue
        value = values[key]
        if key in {"NSUserDictionaryReplacementItems", "NSUserKeyEquivalents"}:
            selected[key] = {"redacted": True, "count": len(value) if hasattr(value, "__len__") else None}
        elif key == "location":
            selected[key] = {"redacted": True, "present": bool(value)}
        elif key == "AppleSymbolicHotKeys" and isinstance(value, dict):
            selected[key] = {
                "redacted": True,
                "count": len(value),
                "enabled_ids": sorted(str(item) for item, config in value.items() if isinstance(config, dict) and config.get("enabled")),
            }
        else:
            selected[key] = value
    return {"status": "verified", "values": selected}


def dock_order() -> dict[str, object]:
    result = subprocess.run(["defaults", "export", "com.apple.dock", "-"], capture_output=True, check=False)
    if result.returncode != 0:
        return {"status": "unavailable", "error": result.stderr.decode(errors="replace").strip()}
    try:
        values = plistlib.loads(result.stdout)
    except (plistlib.InvalidFileException, ValueError) as error:
        return {"status": "unavailable", "error": f"invalid plist: {error}"}
    apps = []
    for order, tile in enumerate(values.get("persistent-apps", []), start=1):
        data = tile.get("tile-data", {})
        apps.append({"order": order, "label": data.get("file-label"), "bundle_identifier": data.get("bundle-identifier")})
    return {"status": "verified", "persistent_apps": apps}


def login_items() -> dict[str, object]:
    result = subprocess.run(["osascript", "-e", 'tell application "System Events" to get name of every login item'], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return {"status": "unavailable", "error": result.stderr.strip()}
    return {"status": "verified", "names": [name.strip() for name in result.stdout.split(",") if name.strip()]}


def keyboard_hid_mapping() -> dict[str, object]:
    result = subprocess.run(["hidutil", "property", "--get", "UserKeyMapping"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return {"status": "unavailable", "error": result.stderr.strip()}
    return {"status": "verified", "redacted_output": result.stdout.strip()}


def display_profile() -> dict[str, object]:
    result = subprocess.run(["system_profiler", "SPDisplaysDataType", "-json"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return {"status": "unavailable", "error": result.stderr.strip()}
    try:
        raw = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        return {"status": "unavailable", "error": str(error)}
    displays = []
    controllers = []
    for controller in raw.get("SPDisplaysDataType", []):
        controllers.append({
            "name": controller.get("_name"),
            "vendor": controller.get("spdisplays_vendor"),
            "model": controller.get("sppci_model"),
            "built_in": controller.get("sppci_bus") == "spdisplays_builtin",
        })
        for display in controller.get("spdisplays_ndrvs", []) or []:
            displays.append({
                "name": display.get("_name"),
                "resolution": display.get("spdisplays_resolution"),
                "pixel_resolution": display.get("spdisplays_pixelresolution"),
                "main": display.get("spdisplays_main"),
                "connection": display.get("spdisplays_connection_type"),
            })
    return {"status": "verified" if displays else "no_display_data", "controllers": controllers, "displays": displays}


def sound_profile() -> dict[str, object]:
    return {"status": "unavailable", "error": "The current macOS AppleScript volume-settings interface is not available in this execution context."}


def power_profile() -> dict[str, object]:
    result = subprocess.run(["pmset", "-g", "custom"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return {"status": "unavailable", "error": result.stderr.strip()}
    sections = {}
    current = None
    for line in result.stdout.splitlines():
        text = line.strip()
        if not text:
            continue
        if text.endswith(" Power") or text in {"Battery Power:", "AC Power:"}:
            current = text.rstrip(":")
            sections[current] = {}
            continue
        if current:
            parts = text.split()
            if len(parts) >= 2:
                key = " ".join(parts[:-1])
                sections[current][key] = parts[-1]
    return {"status": "verified", "profiles": sections}


def export_plist_domain(domain: str) -> dict[str, object]:
    result = subprocess.run(["defaults", "export", domain, "-"], capture_output=True, check=False)
    if result.returncode != 0:
        return {"status": "unavailable", "error": result.stderr.decode(errors="replace").strip()}
    try:
        return {"status": "verified", "values": plistlib.loads(result.stdout)}
    except (plistlib.InvalidFileException, ValueError) as error:
        return {"status": "unavailable", "error": str(error)}


def notification_profile() -> dict[str, object]:
    exported = export_plist_domain("com.apple.ncprefs")
    if exported["status"] != "verified":
        return exported
    values = exported["values"]
    apps = []
    for item in values.get("apps", []) if isinstance(values, dict) else []:
        if not isinstance(item, dict):
            continue
        apps.append({
            "bundle_identifier": item.get("bundle-id"),
            "authorization_flags": item.get("auth"),
            "content_visibility": item.get("content_visibility"),
            "grouping": item.get("grouping"),
        })
    return {
        "status": "verified",
        "app_count": len(apps),
        "apps": apps,
        "global": {key: values.get(key) for key in ("content_visibility", "play_forwarded_notifications_sounds", "sort_order", "summarize_previews") if key in values},
        "focus_or_dnd_data_present": bool(values.get("dnd_prefs")),
        "focus_rules": "redacted_not_exported",
    }


def control_center_profile() -> dict[str, object]:
    exported = export_plist_domain("com.apple.controlcenter")
    if exported["status"] != "verified":
        return exported
    values = exported["values"]
    visible = {}
    positions = {}
    for key, value in values.items():
        if key.startswith("NSStatusItem Visible") or key.startswith("NSStatusItem VisibleCC"):
            visible[key] = value
        elif key.startswith("NSStatusItem Preferred Position"):
            positions[key] = value
    return {"status": "verified", "visible_items": visible, "preferred_positions": positions}


def focus_profile() -> dict[str, object]:
    directory = HOME / "Library/DoNotDisturb/DB"
    if not directory.exists():
        return {"status": "not_present", "rules": "not_exported"}
    try:
        entries = sorted(path.name for path in directory.iterdir())
    except PermissionError as error:
        return {
            "status": "unavailable_permission_denied",
            "error": str(error),
            "rules": "not_exported",
        }
    return {
        "status": "present_manual_review_required",
        "database_entries": entries,
        "rules": "redacted_not_exported",
    }


def display_effects_profile() -> dict[str, object]:
    return {
        "night_shift_domain": export_plist_domain("com.apple.CoreBrightness")["status"],
        "windowserver_domain": export_plist_domain("com.apple.windowserver")["status"],
        "note": "Current domains may be empty or unavailable; no display effect is inferred from absence.",
    }


def audio_profile() -> dict[str, object]:
    result = subprocess.run(["system_profiler", "SPAudioDataType", "-json"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return {"status": "unavailable", "error": result.stderr.strip()}
    try:
        raw = json.loads(result.stdout)
    except json.JSONDecodeError as error:
        return {"status": "unavailable", "error": str(error)}
    devices = []
    for section in raw.get("SPAudioDataType", []):
        for key, value in section.items():
            if not isinstance(value, list):
                continue
            for item in value:
                if not isinstance(item, dict):
                    continue
                devices.append({
                    "name": item.get("_name") or key,
                    "type": item.get("coreaudio_device_type"),
                    "default_input": item.get("coreaudio_default_audio_input_device"),
                    "default_output": item.get("coreaudio_default_audio_output_device"),
                    "input_channels": item.get("coreaudio_device_input_channels"),
                    "output_channels": item.get("coreaudio_device_output_channels"),
                })
    return {"status": "verified", "devices": devices}


DEFAULT_APP_CATEGORIES = {
    "browser": {"schemes": {"http", "https"}, "types": set()},
    "mail": {"schemes": {"mailto"}, "types": set()},
    "images": {"schemes": set(), "types": {"public.jpeg", "public.png", "public.tiff", "public.heic"}},
    "video": {"schemes": set(), "types": {"public.movie", "public.mpeg-4", "com.apple.quicktime-movie"}},
    "pdf": {"schemes": set(), "types": {"com.adobe.pdf"}},
    "archives": {"schemes": set(), "types": {"public.zip-archive", "com.pkware.zip-archive", "org.gnu.gnu-zip-archive", "public.tar-archive"}},
    "ssh": {"schemes": {"ssh"}, "types": set()},
    "editor_text": {"schemes": set(), "types": {"public.plain-text", "net.daringfireball.markdown", "public.source-code", "public.shell-script", "public.json", "public.yaml"}},
}
# "terminal" and "git" have no LaunchServices content-type/URL-scheme surface
# on macOS; they are default-application preferences without an LSHandler
# record and are intentionally excluded from this scan.


def launchservices_profile() -> dict[str, object]:
    domain = "com.apple.LaunchServices/com.apple.launchservices.secure"
    exported = export_plist_domain(domain)
    if exported["status"] != "verified":
        return exported

    all_types = {t for category in DEFAULT_APP_CATEGORIES.values() for t in category["types"]}
    all_schemes = {s for category in DEFAULT_APP_CATEGORIES.values() for s in category["schemes"]}

    raw_handlers = [item for item in exported["values"].get("LSHandlers", []) if isinstance(item, dict)]

    def roles_of(item: dict) -> dict[str, object]:
        return {key: value for key, value in item.items() if key.startswith("LSHandlerRole")}

    by_type = {item.get("LSHandlerContentType"): roles_of(item) for item in raw_handlers if item.get("LSHandlerContentType")}
    by_scheme = {item.get("LSHandlerURLScheme"): roles_of(item) for item in raw_handlers if item.get("LSHandlerURLScheme")}

    categories = {}
    for name, spec in DEFAULT_APP_CATEGORIES.items():
        entries = []
        for content_type in sorted(spec["types"]):
            if content_type in by_type:
                entries.append({"content_type": content_type, "roles": by_type[content_type]})
            else:
                entries.append({"content_type": content_type, "status": "system_default_no_override"})
        for scheme in sorted(spec["schemes"]):
            if scheme in by_scheme:
                entries.append({"url_scheme": scheme, "roles": by_scheme[scheme]})
            else:
                entries.append({"url_scheme": scheme, "status": "system_default_no_override"})
        categories[name] = entries

    # Custom app-registered URL schemes (e.g. vendor deep links) outside the
    # standard web/mail/ssh set. Bundle identifiers only, never paths/tokens.
    custom_scheme_handlers = sorted(
        (
            {"url_scheme": scheme, "roles": roles}
            for scheme, roles in by_scheme.items()
            if scheme not in all_schemes
        ),
        key=lambda entry: entry["url_scheme"],
    )

    return {
        "status": "verified",
        "categories": categories,
        "custom_url_scheme_handlers": custom_scheme_handlers,
        "excluded_categories": {
            "terminal": "no LaunchServices content-type/URL-scheme surface",
            "git": "no LaunchServices content-type/URL-scheme surface",
        },
        "scope": sorted(all_types | all_schemes),
    }


def developer_environment_profile() -> dict[str, object]:
    files = []
    for path in [HOME / ".zshrc", HOME / ".zprofile", HOME / ".bash_profile", HOME / ".ssh/config"]:
        if not path.exists():
            files.append({"path": str(path), "present": False})
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        files.append({"path": str(path), "present": True, "bytes": path.stat().st_size, "sha256": digest})
    git = subprocess.run(["git", "config", "--global", "--list", "--name-only"], capture_output=True, text=True, check=False)
    git_keys = sorted({line.strip() for line in git.stdout.splitlines() if line.strip()}) if git.returncode == 0 else []
    commands = ["brew", "git", "node", "npm", "deno", "java", "mvn", "gcloud", "wrangler", "agy", "studio"]
    versions = {}
    for command in commands:
        resolved = shutil.which(command)
        if not resolved:
            continue
        result = subprocess.run([command, "--version"], capture_output=True, text=True, check=False)
        versions[command] = {"path": resolved, "version_output": (result.stdout or result.stderr).splitlines()[:1]}
    return {
        "status": "verified",
        "shell": os.environ.get("SHELL"),
        "path_entry_count": len(os.environ.get("PATH", "").split(":")),
        "startup_and_ssh_files": files,
        "git_config_keys": git_keys,
        "cli_versions": versions,
        "secrets_policy": "File contents, Git identity values, SSH keys, and tokens are not collected.",
    }


def network_profile() -> dict[str, object]:
    services_result = subprocess.run(["networksetup", "-listallnetworkservices"], capture_output=True, text=True, check=False)
    if services_result.returncode != 0 or "AuthorizationCreate() failed" in services_result.stdout:
        return {"status": "unavailable", "error": services_result.stderr.strip() or services_result.stdout.strip()}
    services = [line.strip() for line in services_result.stdout.splitlines() if line.strip() and not line.startswith("An asterisk")]
    dns = {}
    for service in services:
        result = subprocess.run(["networksetup", "-getdnsservers", service], capture_output=True, text=True, check=False)
        dns[service] = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    proxy = subprocess.run(["scutil", "--proxy"], capture_output=True, text=True, check=False)
    vpn = subprocess.run(["scutil", "--nc", "list"], capture_output=True, text=True, check=False)
    smartdns = ROOT / "config/smartdns.conf"
    return {
        "status": "verified",
        "services": services,
        "dns_by_service": dns,
        "proxy": proxy.stdout.strip() if proxy.returncode == 0 else {"status": "unavailable", "error": proxy.stderr.strip()},
        "vpn_profiles": vpn.stdout.strip() if vpn.returncode == 0 else {"status": "unavailable", "error": vpn.stderr.strip()},
        "smartdns_policy_file_present": smartdns.is_file(),
        "secrets_policy": "No Wi-Fi passwords, VPN credentials, certificates, private keys, or live addresses are collected.",
    }


def browser_continuity_profile() -> dict[str, object]:
    local_state = HOME / "Library/Application Support/Google/Chrome/Local State"
    profiles = []
    if local_state.exists():
        try:
            state = json.loads(local_state.read_text())
        except (OSError, json.JSONDecodeError):
            state = {}
        for directory, info in state.get("profile", {}).get("info_cache", {}).items():
            preferences = HOME / "Library/Application Support/Google/Chrome" / directory / "Preferences"
            row = {"profile_directory": directory, "account_email": info.get("user_name", ""), "extensions": []}
            try:
                preference_path = preferences
                secure_preferences = preferences.with_name("Secure Preferences")
                if secure_preferences.exists():
                    preference_path = secure_preferences
                data = json.loads(preference_path.read_text())
                for extension_id, extension in data.get("extensions", {}).get("settings", {}).items():
                    if not isinstance(extension, dict):
                        continue
                    manifest = extension.get("manifest", {}) if isinstance(extension.get("manifest"), dict) else {}
                    row["extensions"].append({
                        "id": extension_id,
                        "name": manifest.get("name"),
                        "version": manifest.get("version"),
                        "state": extension.get("state"),
                        "enabled": (extension.get("state") == 1) if extension.get("state") is not None else None,
                    })
            except (OSError, json.JSONDecodeError):
                row["extensions_status"] = "unavailable"
            profiles.append(row)
    return {
        "status": "verified" if local_state.exists() else "unavailable",
        "profiles": profiles,
        "safari_obsidian_web_clipper_app": Path("/Applications/Obsidian Web Clipper.app").exists(),
        "webcatalog_apps_directory": (HOME / "Applications/WebCatalog Apps").is_dir(),
        "playcover_apps_directory": (HOME / "Applications/PlayCover").is_dir(),
        "enabled_state_note": "null means Chrome did not expose the enabled state in this profile file; it is not interpreted as disabled.",
        "secrets_policy": "No cookies, passwords, tokens, history, or page content are collected.",
    }


def security_profile() -> dict[str, object]:
    def output(command: list[str]) -> dict[str, object]:
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        return {
            "status": "verified" if result.returncode == 0 else "unavailable",
            "output": (result.stdout or result.stderr).strip(),
            "returncode": result.returncode,
        }
    firewall = "/usr/libexec/ApplicationFirewall/socketfilterfw"
    return {
        "gatekeeper": output(["spctl", "--status"]),
        "firewall": output([firewall, "--getglobalstate"]) if Path(firewall).exists() else {"status": "unavailable"},
        "filevault": output(["fdesetup", "status"]),
        "sip": output(["csrutil", "status"]),
        "mdm_enrollment": output(["profiles", "status", "-type", "enrollment"]),
        "vpn_client_presence": {
            "tailscale_app": Path("/Applications/Tailscale.app").exists(),
            "zerotier_app": Path("/Applications/ZeroTier.app").exists(),
            "adguard_vpn_app": Path("/Applications/AdGuard VPN.app").exists(),
        },
        "secrets_policy": "No certificates, recovery keys, VPN credentials, or private keys are collected.",
    }


def user_launch_agents() -> dict[str, object]:
    directory = Path.home() / "Library/LaunchAgents"
    if not directory.exists():
        return {"status": "verified", "agents": []}
    agents = []
    for path in sorted(directory.glob("*.plist")):
        row = {"path": str(path), "name": path.stem}
        try:
            with path.open("rb") as stream:
                plistlib.load(stream)
        except (OSError, plistlib.InvalidFileException, ET.ParseError, ExpatError, ValueError) as error:
            row.update({"status": "parse_error", "error": str(error)})
        else:
            row["status"] = "verified"
        agents.append(row)
    return {"status": "verified", "agents": agents}


def scan() -> dict[str, object]:
    disk = shutil.disk_usage(Path.home())
    return {
        "schema_version": 1,
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "user": os.environ.get("USER", "unknown"),
        "source": "read-only allowlisted defaults exports and login-item query",
        "machine_baseline": {
            "macos": platform.platform(),
            "architecture": platform.machine(),
            "memory_bytes": _memory_bytes(),
            "home_volume_total_bytes": disk.total,
            "home_volume_free_bytes": disk.free,
        },
        "domains": {domain: export_domain(domain) for domain in ALLOWLIST},
        "dock_order": dock_order(),
        "login_items": login_items(),
        "user_launch_agents": user_launch_agents(),
        "keyboard_hid_mapping": keyboard_hid_mapping(),
        "display_profile": display_profile(),
        "sound_profile": sound_profile(),
        "power_profile": power_profile(),
        "notification_profile": notification_profile(),
        "control_center_profile": control_center_profile(),
        "focus_profile": focus_profile(),
        "display_effects_profile": display_effects_profile(),
        "audio_profile": audio_profile(),
        "launchservices_profile": launchservices_profile(),
        "developer_environment_profile": developer_environment_profile(),
        "network_profile": network_profile(),
        "security_profile": security_profile(),
        "browser_continuity_profile": browser_continuity_profile(),
        "secrets_policy": "No credentials, tokens, recent documents, or private paths are collected.",
    }


def _memory_bytes() -> int | None:
    result = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, check=False)
    try:
        return int(result.stdout.strip())
    except ValueError:
        return None


def apply_values() -> list[dict[str, object]]:
    desired = json.loads(DEFAULT_VALUES.read_text())
    changed = []
    for domain, values in desired.get("domains", {}).items():
        for key, value in values.items():
            if isinstance(value, bool):
                flag = "-bool"
                encoded = "true" if value else "false"
            elif isinstance(value, (int, float)):
                flag = "-float"
                encoded = str(value)
            elif isinstance(value, str):
                flag = "-string"
                encoded = value
            else:
                raise ValueError(f"unsupported preference type: {domain}.{key}")
            result = subprocess.run(["defaults", "write", domain, key, flag, encoded], capture_output=True, text=True, check=False)
            changed.append({"domain": domain, "key": key, "value": value, "status": "applied" if result.returncode == 0 else "failed", "error": result.stderr.strip()})
    subprocess.run(["killall", "Finder"], capture_output=True, check=False)
    subprocess.run(["killall", "Dock"], capture_output=True, check=False)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture an allowlisted macOS preference baseline")
    parser.add_argument("--output", type=Path, help="write the JSON result to this path")
    parser.add_argument("--check", action="store_true", help="compare the capture with tracked desired values")
    parser.add_argument("--apply", action="store_true", help="apply tracked values after explicit confirmation")
    args = parser.parse_args()
    if args.apply:
        print("This will change only the tracked values in settings/system-preferences-values.json and restart Finder and Dock.")
        if input("Type APPLY to continue: ").strip() != "APPLY":
            print("Cancelled; no changes made.")
            return 0
        print(json.dumps({"apply": apply_values()}, ensure_ascii=False, indent=2))
    result = scan()
    output = args.output or DEFAULT_OUTPUT_DIR / f"preferences-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    report = {"output": str(output), "domains": result["domains"], "dock_order": result["dock_order"], "login_items": result["login_items"], "user_launch_agents": result["user_launch_agents"]}
    if args.check:
        desired = json.loads(DEFAULT_VALUES.read_text())
        mismatches = []
        for domain, expected in desired.get("domains", {}).items():
            actual = result["domains"].get(domain, {}).get("values", {})
            for key, value in expected.items():
                if actual.get(key) != value:
                    mismatches.append({"domain": domain, "key": key, "expected": value, "actual": actual.get(key)})
        report["check"] = {"status": "match" if not mismatches else "mismatch", "mismatches": mismatches}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("check", {}).get("status", "match") == "match" else 1


if __name__ == "__main__":
    raise SystemExit(main())
