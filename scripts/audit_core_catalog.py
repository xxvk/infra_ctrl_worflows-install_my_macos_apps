#!/usr/bin/env python3
"""Audit Core catalog guides, size measurements, and GUI/CLI metadata."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "references/app-catalog.json"


def main() -> int:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    core = [app for app in data["apps"] if app.get("tier") == "core"]
    missing_guides, missing_sizes, cli_review = [], [], []
    for app in core:
        guide = app.get("guide")
        path = ROOT / guide if guide else None
        if not guide or not path.is_file():
            missing_guides.append({"name": app["name"], "guide": guide})
            continue
        text = path.read_text(encoding="utf-8")
        if "download_bytes:" not in text or "installed_bytes:" not in text:
            missing_sizes.append(app["name"])
        if app.get("app_store_url") and app.get("cli_command") and not app.get("cli_formula"):
            cli_review.append({"name": app["name"], "cli_command": app["cli_command"], "issue": "missing cli_formula"})
    result = {
        "core_total": len(core),
        "guides_present": len(core) - len(missing_guides),
        "missing_guides": missing_guides,
        "guides_missing_size_measurements": missing_sizes,
        "app_store_cli_metadata_review": cli_review,
        "size_note": "Catalog size_gb is an estimate; download_bytes and installed_bytes are measured values.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not missing_guides and not missing_sizes and not cli_review else 1


if __name__ == "__main__":
    raise SystemExit(main())
