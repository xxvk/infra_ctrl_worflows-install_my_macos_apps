#!/usr/bin/env python3
"""Read-only backup precondition check.

Reports Time Machine configuration/staleness so destructive-adjacent
scripts (Docker Desktop retirement, Capacities cleanup, TCC reset) can warn
the user before proceeding. It never blocks, configures, or starts a
backup; it only observes and reports. iCloud file sync is explicitly not
treated as a substitute for a full-system backup, since it does not cover
installed apps, non-iCloud folders, or system/preference state.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys

STALE_AFTER_DAYS = 35  # matches the user's stated ~monthly Time Machine cadence


def _run(args: list[str]) -> tuple[int, str, str]:
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def check_time_machine() -> dict[str, object]:
    dest_code, dest_out, dest_err = _run(["tmutil", "destinationinfo"])
    if dest_code != 0 or "No destinations configured" in dest_out:
        return {
            "status": "not_configured",
            "detail": dest_out or dest_err,
        }

    latest_code, latest_out, latest_err = _run(["tmutil", "latestbackup"])
    if latest_code != 0 or not latest_out:
        return {
            "status": "configured_no_backup_found",
            "destination_info": dest_out,
            "detail": latest_err or "tmutil latestbackup returned no path",
        }

    # tmutil latestbackup returns a path like /Volumes/.../Backups.backupdb/<Host>/<timestamp>
    timestamp_str = latest_out.rstrip("/").rsplit("/", 1)[-1]
    try:
        backup_time = dt.datetime.strptime(timestamp_str, "%Y-%m-%d-%H%M%S")
    except ValueError:
        return {
            "status": "configured_unparseable_timestamp",
            "destination_info": dest_out,
            "latest_backup_path": latest_out,
        }

    age_days = (dt.datetime.now() - backup_time).days
    return {
        "status": "stale" if age_days > STALE_AFTER_DAYS else "current",
        "destination_info": dest_out,
        "latest_backup_path": latest_out,
        "latest_backup_at": backup_time.isoformat(),
        "age_days": age_days,
        "stale_after_days": STALE_AFTER_DAYS,
    }


def warning_lines(tm_status: dict[str, object]) -> list[str]:
    status = tm_status["status"]
    if status == "not_configured":
        return [
            "WARNING: No Time Machine destination is configured on this Mac.",
            "iCloud file sync alone does not back up installed apps, non-iCloud",
            "folders, or system/preference state. Consider a Time Machine backup",
            "before proceeding with an irreversible cleanup.",
        ]
    if status == "configured_no_backup_found":
        return [
            "WARNING: A Time Machine destination is configured but no completed",
            "backup was found. Consider running a backup before proceeding.",
        ]
    if status == "stale":
        return [
            f"WARNING: Latest Time Machine backup is {tm_status['age_days']} days old",
            f"(warn threshold: {tm_status['stale_after_days']} days). Consider running",
            "a fresh backup before proceeding with an irreversible cleanup.",
        ]
    if status == "configured_unparseable_timestamp":
        return [
            "WARNING: A Time Machine backup exists but its age could not be verified.",
        ]
    return []  # status == "current": no warning needed


def print_precondition_warning(operation_name: str) -> None:
    """Call from a destructive-adjacent script before its --apply path runs.

    Never raises and never blocks; it only prints an advisory warning to
    stderr so the calling script's own confirmation flow remains the sole
    gate on the operation.
    """
    tm_status = check_time_machine()
    lines = warning_lines(tm_status)
    if not lines:
        return
    print(f"--- Backup precondition check ({operation_name}) ---", file=sys.stderr)
    for line in lines:
        print(line, file=sys.stderr)
    print("---", file=sys.stderr)


def main() -> int:
    tm_status = check_time_machine()
    print(json.dumps({"time_machine": tm_status}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
