#!/usr/bin/env python3
"""Validate progressive-disclosure structure for the Skill entry point."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MAX_SKILL_LINES = 500
DOMAIN_REFERENCES = {
    "references/runtime-and-developer-baseline.md": [
        "## Version and product roadmap",
        "## Mission: one-sync, ready-to-use Mac",
        "### Shared Python Core policy",
        "### Android developer environment",
        "### Whisper model selection",
    ],
    "references/permissions-preferences-bootstrap.md": [
        "## Required macOS permission preflight",
        "### Permission inventory and bootstrap rule",
        "### User-preference extraction rule",
        "### Bootstrap entry point",
        "### Required iCloud/Git integrity preflight",
        "### Stale TCC authorization cleanup",
    ],
    "references/keyboard-and-logitech.md": [
        "## Keyboard settings workflow",
        "### Logitech K240 profile",
        "### Logitech MX Keys Mac profile",
        "### F1–F3, F5, and F12 native listener implementation",
        "### Logitech K240/M212 battery telemetry",
    ],
    "references/startup-dock-and-security.md": [
        "## Startup item and login component audit",
        "## Dock configuration and order audit",
        "## Developer-machine Gatekeeper policy",
    ],
    "references/application-installation-workflow.md": [
        "## Workflow",
        "## App Store workflow",
        "## Documentation churn policy",
        "## Component frontmatter integrity",
    ],
    "references/application-maintenance.md": [
        "## GUI app and CLI workflow",
        "## Duplicate bundle cleanup",
        "## Complete removal and embedded helper cleanup",
        "## Browser download preflight",
        "## Chrome multi-profile workflow",
        "## GitHub CLI preflight",
        "## Docker Desktop retirement",
        "## Catalog maintenance",
    ],
    "references/machine-role-profiles.md": [
        "## Purpose",
        "## Role model",
        "## Overrides and boundaries",
    ],
    "references/localization-accessibility.md": [
        "## Locale policy",
        "## Accessibility requirements",
    ],
    "references/app-adapter-sdk.md": [
        "## Adapter contract",
        "## WeChat reference adapter",
        "## Claude VM reference adapter",
    ],
    "references/performance-benchmarks.md": [
        "## Measured operations",
        "## Budgets and baselines",
    ],
    "references/audit-reports.md": [
        "## Accessibility and localization",
        "## Boundary",
    ],
    "references/drift-monitor.md": [
        "## Finding and notification policy",
        "## Power and privacy",
    ],
    "references/public-release-readiness.md": [
        "## Current blockers",
        "## Repeatable publication inventory",
        "## Target repository model",
        "## Publication gates",
        "## Selected history strategy",
        "## Visibility-change transaction",
    ],
}
CORE_HEADINGS = [
    "## Operating contract",
    "## Reference routing",
    "## Mandatory execution sequence",
    "## Mutation contract",
    "## Catalog and documentation contract",
    "## Persistent records and local validation",
    "## Safety rules",
]


def validate_skill_structure(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    skill_path = root / "SKILL.md"
    errors: list[str] = []
    if not skill_path.is_file():
        return {"status": "failed", "errors": ["SKILL.md not found"]}
    skill = skill_path.read_text(encoding="utf-8")
    line_count = len(skill.splitlines())
    if line_count > MAX_SKILL_LINES:
        errors.append(
            f"SKILL.md exceeds progressive-disclosure limit: {line_count} > {MAX_SKILL_LINES}"
        )
    for heading in CORE_HEADINGS:
        if heading not in skill:
            errors.append(f"SKILL.md missing core heading: {heading}")

    checked_references: list[str] = []
    for relative, anchors in DOMAIN_REFERENCES.items():
        if f"]({relative})" not in skill:
            errors.append(f"SKILL.md does not directly link: {relative}")
        path = root / relative
        if not path.is_file():
            errors.append(f"domain reference not found: {relative}")
            continue
        text = path.read_text(encoding="utf-8")
        if "## Contents" not in text:
            errors.append(f"domain reference has no contents section: {relative}")
        for anchor in anchors:
            if anchor not in text:
                errors.append(f"{relative} missing preserved section: {anchor}")
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if "://" in target or target.startswith("#"):
                continue
            target_path = target.split("#", 1)[0]
            if target_path and not (path.parent / target_path).exists():
                errors.append(f"{relative} local link not found: {target}")
        checked_references.append(relative)

    for target in re.findall(r"\]\(([^)]+)\)", skill):
        if "://" in target or target.startswith("#"):
            continue
        target_path = target.split("#", 1)[0]
        if target_path and not (root / target_path).exists():
            errors.append(f"SKILL.md local link not found: {target}")

    return {
        "status": "passed" if not errors else "failed",
        "skill_lines": line_count,
        "max_skill_lines": MAX_SKILL_LINES,
        "domain_references": checked_references,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = validate_skill_structure(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
