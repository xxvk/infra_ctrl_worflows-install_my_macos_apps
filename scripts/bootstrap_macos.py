#!/usr/bin/env python3
"""Run the read-only new-Mac bootstrap assessment in dependency order."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"


def run_step(name: str, command: list[str], allow_failure: bool = False) -> dict[str, object]:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
    def redact(value: str) -> str:
        return re.sub(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "<redacted-email>", value, flags=re.IGNORECASE)
    row = {
        "name": name,
        "command": command,
        "returncode": result.returncode,
        "status": "passed" if result.returncode == 0 else ("review_required" if allow_failure else "failed"),
        "stdout_tail": redact(result.stdout[-4000:]),
        "stderr_tail": redact(result.stderr[-2000:]),
    }
    return row


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a read-only, ordered Mac bootstrap assessment")
    parser.add_argument("--profile", default="auto", help="storage profile passed to the app planner")
    args = parser.parse_args()
    py = sys.executable
    steps = [
        run_step("tracked_definition_validation", [py, "scripts/bootstrap_validate.py"]),
        run_step("app_scan", [py, "scripts/macos_apps.py", "scan"]),
        run_step("app_plan", [py, "scripts/macos_apps.py", "plan", "--profile", args.profile]),
        run_step("permission_inventory", [py, "scripts/macos_permissions.py"]),
        run_step("preference_baseline_and_check", [py, "scripts/macos_preferences.py", "--check"], allow_failure=True),
    ]
    result = {
        "schema_version": 1,
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "mode": "read_only_assessment",
        "profile": args.profile,
        "steps": steps,
        "policy": "No app installation, permission grant, login, credential entry, or preference apply was attempted.",
        "next_actions": [
            "Review the generated app plan and permission summary.",
            "Complete required interactive authorizations and account sign-ins.",
            "Apply only reviewed preference policies.",
            "Run the final verification phase.",
        ],
    }
    STATE.mkdir(exist_ok=True)
    output = STATE / f"bootstrap-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(output), "steps": steps}, ensure_ascii=False, indent=2))
    return 0 if all(step["status"] in {"passed", "review_required"} for step in steps) else 1


if __name__ == "__main__":
    raise SystemExit(main())
