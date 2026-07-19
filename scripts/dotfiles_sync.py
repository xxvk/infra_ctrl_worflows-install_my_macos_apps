#!/usr/bin/env python3
"""Symlink-based dotfiles reproduction.

Reads tracked files from dotfiles/home/<relative-path> and links them to
$HOME/<relative-path>. Never copies file contents into state/ or anywhere
else; never overwrites an existing non-symlink destination without backing
it up first. See dotfiles/README.md for the population convention.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOTFILES_HOME = ROOT / "dotfiles/home"
HOME = Path.home()


def tracked_files() -> list[Path]:
    if not DOTFILES_HOME.is_dir():
        return []
    return sorted(path for path in DOTFILES_HOME.rglob("*") if path.is_file())


def status() -> dict[str, object]:
    entries = []
    for tracked in tracked_files():
        relative = tracked.relative_to(DOTFILES_HOME)
        destination = HOME / relative
        if not destination.exists() and not destination.is_symlink():
            state = "missing_at_destination"
        elif destination.is_symlink():
            state = "linked_correctly" if destination.resolve() == tracked.resolve() else "linked_elsewhere"
        else:
            state = "unlinked_file_present"
        entries.append({
            "relative_path": str(relative),
            "tracked_path": str(tracked),
            "destination_path": str(destination),
            "state": state,
        })
    return {"status": "verified", "entries": entries}


def link(apply: bool) -> dict[str, object]:
    report = status()
    actions = []
    for entry in report["entries"]:
        if entry["state"] == "linked_correctly":
            continue
        destination = Path(entry["destination_path"])
        tracked = Path(entry["tracked_path"])
        action = {"relative_path": entry["relative_path"], "previous_state": entry["state"]}
        if not apply:
            action["planned"] = "backup_then_symlink" if destination.exists() or destination.is_symlink() else "symlink"
            actions.append(action)
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists() or destination.is_symlink():
            backup = destination.with_name(destination.name + f".pre-dotfiles-backup-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}")
            destination.rename(backup)
            action["backup_path"] = str(backup)
        destination.symlink_to(tracked)
        action["applied"] = True
        actions.append(action)
    return {"apply_requested": apply, "actions": actions}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("status", help="Preview tracked-vs-destination state (read-only)")
    link_parser = subparsers.add_parser("link", help="Symlink tracked files into $HOME")
    link_parser.add_argument("--apply", action="store_true", help="actually create symlinks; default is dry-run preview")
    args = parser.parse_args()

    if args.command == "status":
        print(json.dumps(status(), ensure_ascii=False, indent=2))
    elif args.command == "link":
        print(json.dumps(link(args.apply), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
