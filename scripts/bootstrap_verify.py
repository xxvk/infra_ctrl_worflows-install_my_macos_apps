#!/usr/bin/env python3
"""Run the final read-only drift check and emit safe recovery commands."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
from pathlib import Path

from state_paths import STATE_DIR_ENV, add_state_dir_argument, resolve_state_dir


ROOT = Path(__file__).resolve().parents[1]
STATE = resolve_state_dir()


def run(command: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout, result.stderr


def newest(pattern: str) -> Path | None:
    paths = sorted(STATE.glob(pattern))
    return paths[-1] if paths else None


def main() -> int:
    global STATE
    parser = argparse.ArgumentParser(description=__doc__)
    add_state_dir_argument(parser)
    args = parser.parse_args()
    STATE = resolve_state_dir(args.state_dir)
    os.environ[STATE_DIR_ENV] = str(STATE)
    py = sys.executable
    steps = {}
    steps["app_scan"] = run([py, "scripts/macos_apps.py", "scan"])
    steps["app_plan"] = run([py, "scripts/macos_apps.py", "plan", "--profile", "auto"])
    steps["permissions"] = run([py, "scripts/macos_permissions.py"])
    steps["preferences"] = run([py, "scripts/macos_preferences.py", "--check"])
    plan_path = newest("plan-*.json")
    permission_path = newest("permissions-*.json")
    preference_path = newest("preferences-*.json")
    plan = json.loads(plan_path.read_text()) if plan_path else {}
    permissions = json.loads(permission_path.read_text()) if permission_path else {}
    preference_output = {}
    try:
        preference_output = json.loads(steps["preferences"][1])
    except json.JSONDecodeError:
        preference_output = {"status": "unavailable", "reason": "preference check output was not JSON"}
    report = {
        "schema_version": 1,
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "mode": "read_only_final_drift_check",
        "sources": {"plan": str(plan_path) if plan_path else None, "permissions": str(permission_path) if permission_path else None, "preferences": str(preference_path) if preference_path else None},
        "app_drift": {
            "missing_count": len(plan.get("missing", [])),
            "missing_core": [item.get("name") for item in plan.get("missing", []) if item.get("tier") == "core"],
            "source_mismatches": plan.get("source_mismatches", []),
        },
        "permission_drift": permissions.get("permission_summary", {}),
        "preference_drift": preference_output.get("check", preference_output),
        "step_returncodes": {name: value[0] for name, value in steps.items()},
        "recovery_commands": [
            "python3 scripts/macos_apps.py scan",
            "python3 scripts/macos_apps.py plan --profile auto",
            "python3 scripts/macos_permissions.py",
            "python3 scripts/macos_preferences.py --check",
        ],
        "policy": "Report only; no install, authorization, preference apply, or cleanup was attempted.",
    }
    STATE.mkdir(parents=True, exist_ok=True)
    output = STATE / f"bootstrap-verify-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all(code == 0 for code in report["step_returncodes"].values()) else 1


if __name__ == "__main__":
    raise SystemExit(main())
