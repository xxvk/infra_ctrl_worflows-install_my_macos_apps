#!/usr/bin/env python3
"""Report legacy malformed Core frontmatter containing machine-state fields."""
from __future__ import annotations

import json
from pathlib import Path

from config_layers import load_app_catalog

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    data = load_app_catalog()
    findings = []
    for app in data["apps"]:
        if app.get("tier") != "core" or not app.get("guide"):
            continue
        path = ROOT / app["guide"]
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        lines = text.splitlines(keepends=True)
        if not lines or lines[0].strip() != "---":
            continue
        closing = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if closing is not None:
            continue
        marker = next((i for i, line in enumerate(lines) if line.startswith("installed_at:")), None)
        if marker is None:
            continue
        findings.append(str(path.relative_to(ROOT)))
    print(json.dumps({"tracked_files_written": False, "migration_required": findings}, indent=2))
    return 1 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
