#!/usr/bin/env python3
"""Run low-noise read-only drift monitoring with deduplication and cooldowns."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from schema_contract import SchemaContractError, load_and_validate
from state_paths import add_state_dir_argument, resolve_state_dir


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "settings" / "drift-monitor.json"


class DriftMonitorError(RuntimeError):
    """Raised when monitor policy or observations are invalid."""


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    try:
        return load_and_validate(path, "drift-monitor-policy")
    except SchemaContractError as exc:
        raise DriftMonitorError(str(exc)) from exc


def validate() -> dict[str, Any]:
    try:
        policy = load_policy()
        if policy["minimum_confidence"] > 1:
            raise DriftMonitorError("minimum_confidence may not exceed 1")
        if policy["cooldown_hours"]["high"] > policy["cooldown_hours"]["medium"]:
            raise DriftMonitorError("high severity cooldown may not exceed medium")
    except DriftMonitorError as exc:
        return {"schema_version": 1, "status": "failed", "errors": [str(exc)]}
    return {"schema_version": 1, "status": "passed", "policy": policy, "errors": []}


def power_status() -> dict[str, Any]:
    result = subprocess.run(["pmset", "-g", "batt"], capture_output=True, text=True, check=False)
    text = result.stdout
    percent = next((int(token.rstrip("%;")) for token in text.split() if token.endswith("%;") and token[:-2].isdigit()), None)
    return {"available": result.returncode == 0 and percent is not None, "percentage": percent, "charging": "AC Power" in text or "charging" in text.lower()}


def should_defer_for_power(power: dict[str, Any], minimum: int) -> bool:
    return bool(power.get("available") and not power.get("charging") and isinstance(power.get("percentage"), int) and power["percentage"] < minimum)


def _finding(identifier: str, severity: str, confidence: float, message: str) -> dict[str, Any]:
    return {"id": identifier, "severity": severity, "confidence": confidence, "message": message}


def extract_findings(report: dict[str, Any]) -> list[dict[str, Any]]:
    app = report.get("app_drift") if isinstance(report.get("app_drift"), dict) else {}
    preferences = report.get("preference_drift") if isinstance(report.get("preference_drift"), dict) else {}
    rows = []
    for name in app.get("missing_core", []):
        if isinstance(name, str):
            rows.append(_finding(f"missing-core:{name}", "high", 0.95, f"Core app missing: {name}"))
    for item in app.get("source_mismatches", []):
        if isinstance(item, dict) and isinstance(item.get("app"), str):
            rows.append(_finding(f"source-mismatch:{item['app']}", "medium", 0.9, f"Source mismatch: {item['app']}"))
    if preferences.get("status") == "mismatch":
        rows.append(_finding("preference-mismatch", "medium", 0.8, "Tracked preference values differ."))
    for name, returncode in report.get("step_returncodes", {}).items():
        if isinstance(name, str) and isinstance(returncode, int) and returncode != 0:
            rows.append(_finding(f"check-unavailable:{name}", "low", 0.7, f"Read-only check needs review: {name}"))
    return sorted(rows, key=lambda item: (item["severity"], item["id"]))


def deduplicate(findings: list[dict[str, Any]], previous: dict[str, Any] | None, cooldown_hours: dict[str, int], *, now: dt.datetime) -> dict[str, Any]:
    prior = {item.get("id"): item for item in (previous or {}).get("findings", []) if isinstance(item, dict)}
    due, all_rows = [], []
    for finding in findings:
        existing = prior.get(finding["id"], {})
        row = {**finding, "first_seen_at": existing.get("first_seen_at", now.isoformat()), "last_seen_at": now.isoformat()}
        last = existing.get("last_notified_at")
        notify = True
        if isinstance(last, str):
            try:
                elapsed = now - dt.datetime.fromisoformat(last.replace("Z", "+00:00"))
                notify = elapsed.total_seconds() >= cooldown_hours[finding["severity"]] * 3600
            except ValueError:
                notify = True
        if notify:
            row["last_notified_at"] = now.isoformat()
            due.append(row)
        else:
            row["last_notified_at"] = last
        all_rows.append(row)
    return {"findings": all_rows, "new_or_due": due, "suppressed_count": len(all_rows) - len(due)}


def _latest_drift(state_dir: Path) -> Path | None:
    rows = sorted(state_dir.glob("bootstrap-verify-*.json"))
    return rows[-1] if rows else None


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def run_monitor(state_dir: Path, *, runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run, now: dt.datetime | None = None) -> dict[str, Any]:
    policy = load_policy()
    power = power_status()
    now = now or dt.datetime.now(dt.timezone.utc)
    if should_defer_for_power(power, policy["min_battery_percent"]):
        return {"schema_version": 1, "mode": "deferred_low_battery", "power": power, "policy": "No scan ran; retry when charging or battery is sufficient."}
    command = [sys.executable, "scripts/bootstrap_verify.py", "--state-dir", str(state_dir)]
    completed = runner(command, cwd=ROOT, capture_output=True, text=True, check=False)
    report_path = _latest_drift(state_dir)
    if not report_path:
        return {"schema_version": 1, "mode": "review_required", "reason": "drift report was not written", "returncode": completed.returncode}
    report = json.loads(report_path.read_text(encoding="utf-8"))
    findings = [item for item in extract_findings(report) if item["confidence"] >= policy["minimum_confidence"]]
    ledger_path = state_dir / "drift-monitor-ledger.json"
    try:
        previous = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else None
    except (OSError, json.JSONDecodeError):
        previous = None
    deduped = deduplicate(findings, previous, policy["cooldown_hours"], now=now)
    ledger = {"schema_version": 1, "kind": "drift_monitor_ledger", "updated_at": now.isoformat(), "findings": deduped["findings"]}
    _write(ledger_path, ledger)
    summary = deduped["new_or_due"][:policy["max_summary_findings"]]
    return {"schema_version": 1, "mode": "read_only_monitor", "power": power, "drift_report": report_path.name, "new_or_due": summary, "suppressed_count": deduped["suppressed_count"], "repairs_attempted": "none", "policy": "Report only; no installation, authorization, preference apply, cleanup, or repair was attempted."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate low-noise monitor policy")
    run_parser = subparsers.add_parser("run", help="run a read-only monitor cycle")
    add_state_dir_argument(run_parser)
    args = parser.parse_args()
    if args.command == "validate":
        result = validate()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "passed" else 1
    try:
        state_dir = resolve_state_dir(args.state_dir)
        result = run_monitor(state_dir)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (DriftMonitorError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
