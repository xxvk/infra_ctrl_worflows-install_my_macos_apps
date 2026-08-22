#!/usr/bin/env python3
# Mutation action ID: skill-runtime.uninstall
"""Uninstall/rollback this skill's own footprint from the current Mac.

Default is a dry-run preview; every removal requires --apply. This never
touches the app catalog's managed apps, Homebrew packages, or any user
data -- only artifacts this skill itself created (LaunchAgents, its own
binary/support directory, dotfiles symlinks it deployed). Logs are kept by
default; pass --remove-logs to also remove them.

This does not delete the repository itself -- that is the user's own
Git/iCloud content, not something this script owns.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_footprint_inventory import inventory, KNOWN_SUPPORT_PATHS, KNOWN_LOG_PATHS

HOME = Path.home()
CONFIRM_UNINSTALL = "UNINSTALL SKILL RUNTIME"


def _timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def _backup_and_remove(path: Path, apply: bool) -> dict[str, object]:
    if not path.exists():
        return {"path": str(path), "status": "absent"}
    if not apply:
        return {"path": str(path), "status": "would_remove"}
    backup = path.with_name(path.name + f".removed-{_timestamp()}")
    shutil.move(str(path), str(backup))
    return {"path": str(path), "status": "removed", "backup_path": str(backup)}


def uninstall_launch_agents(apply: bool) -> list[dict[str, object]]:
    results = []
    for row in inventory()["launch_agents"]:
        if not row["installed"]:
            results.append({"label": row["label"], "status": "not_installed"})
            continue
        if apply:
            subprocess.run(
                ["launchctl", "bootout", f"gui/{os.getuid()}/{row['label']}"],
                capture_output=True, text=True, check=False,
            )
        results.append({"label": row["label"], **_backup_and_remove(Path(row["plist_path"]), apply)})
    return results


def uninstall_support_paths(apply: bool, remove_logs: bool) -> list[dict[str, object]]:
    results = []
    for path in KNOWN_SUPPORT_PATHS:
        results.append({"kind": "support", **_backup_and_remove(path, apply)})
    if remove_logs:
        for path in KNOWN_LOG_PATHS:
            results.append({"kind": "logs", **_backup_and_remove(path, apply)})
    else:
        for path in KNOWN_LOG_PATHS:
            results.append({"kind": "logs", "path": str(path), "status": "kept_by_default"})
    return results


def uninstall_dotfiles_symlinks(apply: bool) -> list[dict[str, object]]:
    results = []
    for row in inventory()["dotfiles_symlinks"]:
        destination = Path(row["destination"])
        if not row["is_symlink_to_tracked"]:
            results.append({**row, "status": "not_a_tracked_symlink_skipped"})
            continue
        if not apply:
            results.append({**row, "status": "would_unlink"})
            continue
        destination.unlink()
        results.append({**row, "status": "unlinked"})
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="actually remove; default is dry-run preview")
    parser.add_argument("--confirm", default="", help=f'exact token: "{CONFIRM_UNINSTALL}"')
    parser.add_argument("--remove-logs", action="store_true", help="also remove ~/Library/Logs/macomrade (kept by default)")
    args = parser.parse_args()
    if args.apply and args.confirm != CONFIRM_UNINSTALL:
        parser.error(f'--apply requires --confirm "{CONFIRM_UNINSTALL}"')

    result = {
        "action_id": "skill-runtime.uninstall",
        "apply_requested": args.apply,
        "launch_agents": uninstall_launch_agents(args.apply),
        "support_and_logs": uninstall_support_paths(args.apply, args.remove_logs),
        "dotfiles_symlinks": uninstall_dotfiles_symlinks(args.apply),
        "note": "The repository itself (this skill's tracked source) is not deleted by this script.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
