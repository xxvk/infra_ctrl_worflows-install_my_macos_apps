#!/usr/bin/env python3
"""Review and selectively remove stale macOS TCC authorization records.

The default action is a dry-run. Applying a reset requires --apply and an
interactive confirmation. This script resets only named TCC service/client
pairs; it never deletes applications or their data.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from backup_precondition_check import print_precondition_warning

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / "state"
SERVICE_COMMANDS = {
    "kTCCServiceAccessibility": "Accessibility",
    "kTCCServiceAppleEvents": "AppleEvents",
    "kTCCServiceListenEvent": "ListenEvent",
    "kTCCServiceScreenCapture": "ScreenCapture",
    "kTCCServiceSystemPolicyAllFiles": "SystemPolicyAllFiles",
    "kTCCServiceSystemPolicyDesktopFolder": "SystemPolicyDesktopFolder",
    "kTCCServiceSystemPolicyDocumentsFolder": "SystemPolicyDocumentsFolder",
    "kTCCServiceSystemPolicyDownloadsFolder": "SystemPolicyDownloadsFolder",
    "kTCCServiceSystemPolicyNetworkVolumes": "SystemPolicyNetworkVolumes",
    "kTCCServiceRemovableVolumes": "RemovableVolumes",
}


def latest_state() -> Path:
    paths = sorted(STATE_DIR.glob("permissions-*.json"))
    if not paths:
        raise SystemExit("No permissions state found; run scripts/macos_permissions.py first.")
    return paths[-1]


def candidates(state: dict, include_manual_review: bool, selected_client: str | None) -> list[dict[str, object]]:
    tcc = state.get("tcc_inventory", {})
    rows = tcc.get("unmatched_client_classifications", [])
    output = []
    for row in rows:
        if selected_client and row.get("client") != selected_client:
            continue
        classification_status = row.get("classification_status")
        if classification_status == "legacy_or_removed":
            reason = "legacy_or_removed"
        elif include_manual_review and classification_status in {"unlisted_or_manual", "current_app_identity_variant"}:
            reason = "manual_review_included"
        else:
            continue
        service = row.get("service")
        command_service = SERVICE_COMMANDS.get(str(service))
        if not command_service:
            output.append({**row, "cleanup_status": "unsupported_service", "reason": reason})
            continue
        output.append({
            "client": row["client"],
            "service": service,
            "service_name": row.get("service_name"),
            "status": row.get("status"),
            "classification": row.get("classification"),
            "reason": reason,
            "tccutil_service": command_service,
            "cleanup_status": "candidate",
        })
    return output


def print_candidates(rows: list[dict[str, object]]) -> None:
    if not rows:
        print("No cleanup candidates in the selected scope.")
        return
    for index, row in enumerate(rows, 1):
        print(
            f"[{index}] {row.get('client')} | {row.get('service_name')} | "
            f"{row.get('status')} | {row.get('classification')} | {row.get('cleanup_status')}"
        )


def apply(rows: list[dict[str, object]]) -> dict[str, object]:
    tccutil = shutil.which("tccutil")
    if not tccutil:
        raise SystemExit("tccutil was not found on PATH.")
    results = []
    for row in rows:
        if row.get("cleanup_status") != "candidate":
            continue
        command = [tccutil, "reset", str(row["tccutil_service"]), str(row["client"])]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        results.append({
            **row,
            "command": command,
            "result": "reset_requested" if result.returncode == 0 else "failed",
            "stderr": result.stderr.strip(),
        })
    return {"applied_at": dt.datetime.now(dt.timezone.utc).isoformat(), "results": results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Review and selectively reset stale macOS TCC records")
    parser.add_argument("--state", type=Path, help="permissions state JSON; defaults to the newest state record")
    parser.add_argument("--client", help="limit review to one exact TCC client bundle ID")
    parser.add_argument("--include-manual-review", action="store_true", help="include unlisted/current-variant candidates; still requires confirmation")
    parser.add_argument("--apply", action="store_true", help="reset candidate TCC records after confirmation")
    args = parser.parse_args()
    state_path = args.state or latest_state()
    state = json.loads(state_path.read_text())
    rows = candidates(state, args.include_manual_review, args.client)
    print(f"Source state: {state_path}")
    print_candidates(rows)
    if not args.apply:
        print("Dry-run only; no authorization was changed.")
        return 0
    actionable = [row for row in rows if row.get("cleanup_status") == "candidate"]
    if not actionable:
        print("No supported candidates to reset; no changes made.")
        return 0
    print("This resets only the listed TCC service/client records. It does not delete apps or data.")
    print_precondition_warning("TCC record reset")
    if input("Type CLEAN TCC to continue: ").strip() != "CLEAN TCC":
        print("Cancelled; no changes made.")
        return 0
    result = apply(actionable)
    output = STATE_DIR / f"permissions-cleanup-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps({"source_state": str(state_path), **result}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(output), **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
