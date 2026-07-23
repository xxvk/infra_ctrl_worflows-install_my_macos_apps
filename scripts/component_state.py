#!/usr/bin/env python3
# Mutation action ID: component-state.migrate
"""Audit component guides for machine state and preserve findings locally."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
from pathlib import Path

from state_paths import add_state_dir_argument, resolve_state_dir


ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ROOT / "components"
CONFIRM_MIGRATION = "MIGRATE COMPONENT STATE"
PROHIBITED_FRONTMATTER = {
    "completion_notes",
    "detected_version",
    "download_bytes",
    "installed",
    "installed_at",
    "installed_bytes",
    "installed_version",
    "installed_measurement_method",
    "known_cross_machine_status",
    "last_checked",
    "path",
    "source_status",
    "status",
    "verification_status",
    "verified",
    "verified_at",
    "version",
}
BODY_PATTERNS = (
    ("completed_checkbox", re.compile(r"^\s*-\s*\[x\]", re.IGNORECASE)),
    ("repository_state_link", re.compile(r"(?:\.\./)?state/(?:install|scan|verify|permissions|preferences)-\d{8}", re.IGNORECASE)),
    ("local_evidence_heading", re.compile(r"^##\s+Local evidence\b", re.IGNORECASE)),
    ("installed_path_observation", re.compile(r"^\s*-\s*Installed path:", re.IGNORECASE)),
    ("installed_version_observation", re.compile(r"^\s*-\s*(?:\[[ x]\]\s*)?Installed version:", re.IGNORECASE)),
    ("installed_footprint_observation", re.compile(r"^\s*-\s*Installed footprint:", re.IGNORECASE)),
    ("verified_version_observation", re.compile(r"^\s*-\s*(?:\[[ x]\]\s*)?Version verified:", re.IGNORECASE)),
    ("dated_verification_record", re.compile(r"^\s*-\s*Verification record:.*\b20\d{2}-\d{2}-\d{2}\b", re.IGNORECASE)),
    ("dated_missing_observation", re.compile(r"Confirmed missing during the \b20\d{2}-\d{2}-\d{2}\b scan", re.IGNORECASE)),
    ("dated_configuration_observation", re.compile(r"^\s*-\s*Created .*\b20\d{2}-\d{2}-\d{2}\b", re.IGNORECASE)),
    ("recorded_download_measurement", re.compile(r"^\s*\|\s*Download recorded\s*\|", re.IGNORECASE)),
    ("recorded_install_measurement", re.compile(r"^\s*\|\s*Installed size recorded\s*\|", re.IGNORECASE)),
    ("premeasurement_install_observation", re.compile(r"installed before per-app byte measurement", re.IGNORECASE)),
    ("machine_baseline_observation", re.compile(r"\bcurrent M4 baseline\b", re.IGNORECASE)),
    ("current_bundle_source_observation", re.compile(r"\bcurrent bundle was installed manually\b", re.IGNORECASE)),
    ("current_build_observation", re.compile(r"\bverified current build\b", re.IGNORECASE)),
    ("current_status_table", re.compile(r"^\|\s*Component\s*\|\s*Guide\s*\|\s*Current status\s*\|", re.IGNORECASE)),
    ("installed_status_cell", re.compile(r"^\|[^|]+\|[^|]+\|[^|]*\binstalled\b", re.IGNORECASE)),
    ("local_measurement_prose", re.compile(r"Installed footprint above is measured locally", re.IGNORECASE)),
    ("machine_scoped_retirement", re.compile(r"\bis retired for this machine\b", re.IGNORECASE)),
)


def split_frontmatter(text: str) -> tuple[list[str], list[str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return [], lines
    try:
        end = next(index for index, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        return [], lines
    return lines[1:end], lines[end + 1 :]


def audit_path(path: Path, *, root: Path = ROOT) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    front, body = split_frontmatter(text)
    violations: list[dict[str, object]] = []
    for offset, line in enumerate(front, start=2):
        if ":" not in line or line.startswith((" ", "-")):
            continue
        key = line.split(":", 1)[0].strip()
        if key in PROHIBITED_FRONTMATTER:
            violations.append(
                {"code": "machine_state_frontmatter", "line": offset, "key": key, "text": line}
            )
    body_start = len(front) + 3 if front else 1
    for offset, line in enumerate(body, start=body_start):
        for code, pattern in BODY_PATTERNS:
            if pattern.search(line):
                violations.append({"code": code, "line": offset, "text": line})
    try:
        guide = str(path.relative_to(root))
    except ValueError:
        guide = str(path)
    return {
        "guide": guide,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "violations": violations,
    }


def audit(root: Path = COMPONENTS) -> dict[str, object]:
    guides = [audit_path(path) for path in sorted(root.glob("*.md"))]
    findings = [guide for guide in guides if guide["violations"]]
    return {
        "schema_version": 1,
        "mode": "component_machine_state_audit",
        "checked_guides": len(guides),
        "affected_guides": len(findings),
        "violation_count": sum(len(guide["violations"]) for guide in findings),
        "findings": findings,
        "status": "passed" if not findings else "failed",
    }


def migration_record(result: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": 1,
        "action_id": "component-state.migrate",
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": "tracked component guides before RC-08 normalization",
        "source_deleted": False,
        "affected_guides": result["affected_guides"],
        "violation_count": result["violation_count"],
        "findings": result["findings"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_state_dir_argument(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("audit", help="report machine-state observations; read-only")
    migrate_parser = subparsers.add_parser("migrate", help="copy observations into machine-local state")
    migrate_parser.add_argument("--apply", action="store_true", help="write the migration record")
    migrate_parser.add_argument("--confirm", default="", help=f'exact token: "{CONFIRM_MIGRATION}"')
    args = parser.parse_args()

    result = audit()
    if args.command == "audit":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "passed" else 1

    record = migration_record(result)
    if not args.apply:
        print(json.dumps({**record, "status": "planned"}, ensure_ascii=False, indent=2))
        return 0
    if args.confirm != CONFIRM_MIGRATION:
        parser.error(f'--apply requires --confirm "{CONFIRM_MIGRATION}"')
    state_dir = resolve_state_dir(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    output = state_dir / f"component-state-migration-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps({**record, "status": "recorded"}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(output), **record, "status": "recorded"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
