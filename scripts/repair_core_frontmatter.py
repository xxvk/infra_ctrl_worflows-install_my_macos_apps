#!/usr/bin/env python3
"""Repair missing YAML frontmatter closing delimiters without touching body text."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    data = json.loads((ROOT / "references/app-catalog.json").read_text(encoding="utf-8"))
    repaired = 0
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
        lines.insert(marker + 1, "---\n")
        path.write_text("".join(lines), encoding="utf-8")
        repaired += 1
    print(f"Repaired {repaired} Core frontmatter files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
