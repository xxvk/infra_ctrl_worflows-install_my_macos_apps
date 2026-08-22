#!/usr/bin/env python3
# Mutation action IDs: drift-schedule.install, drift-schedule.uninstall
"""Schedule the existing read-only drift checks as a weekly user LaunchAgent.

This never changes preferences or permissions itself. It only installs a
LaunchAgent that periodically re-runs the skill's own existing read-only
commands through `drift_monitor.py`, which adds low-battery deferral,
deduplication, severity cooldowns, and a report-only boundary. Installing/uninstalling
the LaunchAgent always requires --apply; the default is a dry-run preview,
matching the convention used elsewhere in this skill (e.g. the K240
listener LaunchAgent).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
from pathlib import Path

HOME = Path.home()
SKILL_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = SKILL_ROOT / "templates/drift-check.launchagent.plist"
LABEL = "com.xvk.install-my-macos-apps.drift-check"
DESTINATION = HOME / f"Library/LaunchAgents/{LABEL}.plist"
LOG_DIR = HOME / "Library/Logs/macomrade"


def _xml_escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_plist() -> str:
    monitor_script = SKILL_ROOT / "scripts/drift_monitor.py"
    command = f"python3 '{monitor_script}' run"
    content = TEMPLATE.read_text()
    content = content.replace("__HOME__", str(HOME))
    content = content.replace("__DRIFT_CHECK_COMMAND__", _xml_escape(command))
    return content


def status() -> dict[str, object]:
    installed = DESTINATION.is_file()
    loaded = False
    if installed:
        result = subprocess.run(
            ["launchctl", "print", f"gui/{os.getuid()}/{LABEL}"],
            capture_output=True, text=True, check=False,
        )
        loaded = result.returncode == 0
    return {
        "label": LABEL,
        "destination": str(DESTINATION),
        "installed": installed,
        "loaded": loaded,
        "log_dir": str(LOG_DIR),
        "schedule": "Weekly, Monday 09:00 local time",
        "commands": [
            "drift_monitor.py run",
        ],
    }


def install(apply: bool) -> dict[str, object]:
    rendered = render_plist()
    if not apply:
        return {"action_id": "drift-schedule.install", "apply_requested": False, "would_write": str(DESTINATION), "preview": rendered}
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_text(rendered)
    result = subprocess.run(
        ["launchctl", "bootstrap", f"gui/{os.getuid()}", str(DESTINATION)],
        capture_output=True, text=True, check=False,
    )
    return {
        "action_id": "drift-schedule.install",
        "apply_requested": True,
        "written": str(DESTINATION),
        "launchctl_bootstrap": {
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
        },
    }


def uninstall(apply: bool) -> dict[str, object]:
    if not DESTINATION.is_file():
        return {"action_id": "drift-schedule.uninstall", "apply_requested": apply, "status": "not_installed"}
    if not apply:
        return {"action_id": "drift-schedule.uninstall", "apply_requested": False, "would_remove": str(DESTINATION)}
    subprocess.run(
        ["launchctl", "bootout", f"gui/{os.getuid()}/{LABEL}"],
        capture_output=True, text=True, check=False,
    )
    backup = DESTINATION.with_suffix(DESTINATION.suffix + f".removed-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}")
    shutil.move(str(DESTINATION), str(backup))
    return {"action_id": "drift-schedule.uninstall", "apply_requested": True, "unloaded": True, "backup_path": str(backup)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", help="Report install/load state (read-only)")
    install_parser = subparsers.add_parser("install", help="Write and load the weekly drift-check LaunchAgent")
    install_parser.add_argument("--apply", action="store_true", help="actually write and load; default is dry-run preview")
    uninstall_parser = subparsers.add_parser("uninstall", help="Unload and remove the LaunchAgent (kept as a timestamped backup)")
    uninstall_parser.add_argument("--apply", action="store_true", help="actually unload and remove; default is dry-run preview")
    args = parser.parse_args()

    if args.command == "status":
        print(json.dumps(status(), ensure_ascii=False, indent=2))
    elif args.command == "install":
        print(json.dumps(install(args.apply), ensure_ascii=False, indent=2))
    elif args.command == "uninstall":
        print(json.dumps(uninstall(args.apply), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
