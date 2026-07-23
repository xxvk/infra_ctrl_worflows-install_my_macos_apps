#!/usr/bin/env python3
# Mutation action ID: capacities.remove-app
"""Remove the approved Capacities app bundle while preserving user data."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backup_precondition_check import print_precondition_warning
from state_paths import add_state_dir_argument, resolve_state_dir

ROOT = Path(__file__).resolve().parents[1]
APP = Path("/Applications/Capacities.app")
PRESERVED = [
    Path.home() / "Library/Application Support/Capacities",
    Path.home() / "Library/Preferences/io.capacities.app.plist",
    Path.home() / "Library/HTTPStorages/io.capacities.app",
    Path.home() / "Library/Logs/Capacities",
]
CONFIRM_REMOVE = "REMOVE CAPACITIES APP"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_state_dir_argument(parser)
    parser.add_argument("--apply", action="store_true", help="remove the app bundle")
    parser.add_argument("--confirm", default="", help=f'exact token: "{CONFIRM_REMOVE}"')
    args = parser.parse_args()
    if args.apply and args.confirm != CONFIRM_REMOVE:
        parser.error(f'--apply requires --confirm "{CONFIRM_REMOVE}"')

    existed_before = APP.exists()
    removed = False
    if args.apply and existed_before:
        print_precondition_warning("Capacities app bundle removal")
        shutil.rmtree(APP)
        removed = True

    result = {
        "schema_version": 1,
        "action_id": "capacities.remove-app",
        "captured_at": dt.datetime.now().astimezone().isoformat(),
        "app_path": str(APP),
        "existed_before": existed_before,
        "apply_requested": args.apply,
        "removed": removed,
        "exists_after": APP.exists(),
        "preserved_data_paths": [str(path) for path in PRESERVED if path.exists()],
        "policy": "Remove only the app bundle; preserve support data for separate migration cleanup.",
    }
    state_dir = resolve_state_dir(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    output = state_dir / f"capacities-cleanup-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"state_file": str(output), **result}, ensure_ascii=False, indent=2))
    return 0 if not args.apply or not result["exists_after"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
