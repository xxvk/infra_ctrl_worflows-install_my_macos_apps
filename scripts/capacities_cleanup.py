#!/usr/bin/env python3
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

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"
APP = Path("/Applications/Capacities.app")
PRESERVED = [
    Path.home() / "Library/Application Support/Capacities",
    Path.home() / "Library/Preferences/io.capacities.app.plist",
    Path.home() / "Library/HTTPStorages/io.capacities.app",
    Path.home() / "Library/Logs/Capacities",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="remove the app bundle")
    parser.add_argument("--confirm", action="store_true", help="confirm the approved removal")
    args = parser.parse_args()
    if args.apply and not args.confirm:
        parser.error("--apply requires --confirm")

    existed_before = APP.exists()
    removed = False
    if args.apply and existed_before:
        print_precondition_warning("Capacities app bundle removal")
        shutil.rmtree(APP)
        removed = True

    result = {
        "schema_version": 1,
        "captured_at": dt.datetime.now().astimezone().isoformat(),
        "app_path": str(APP),
        "existed_before": existed_before,
        "apply_requested": args.apply,
        "removed": removed,
        "exists_after": APP.exists(),
        "preserved_data_paths": [str(path) for path in PRESERVED if path.exists()],
        "policy": "Remove only the app bundle; preserve support data for separate migration cleanup.",
    }
    STATE.mkdir(exist_ok=True)
    output = STATE / f"capacities-cleanup-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"state_file": str(output), **result}, ensure_ascii=False, indent=2))
    return 0 if not args.apply or not result["exists_after"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
