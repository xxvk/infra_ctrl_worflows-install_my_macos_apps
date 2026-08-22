#!/usr/bin/env python3
"""Audit Core catalog guides and GUI/CLI metadata."""
from __future__ import annotations

import json
from pathlib import Path

from config_layers import load_app_catalog

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "references/mac-app-catalog.json"


def main() -> int:
    data = load_app_catalog(CATALOG)
    core = [app for app in data["apps"] if app.get("tier") == "core"]
    missing_guides, cli_review = [], []
    for app in core:
        guide = app.get("guide")
        path = ROOT / guide if guide else None
        if not guide or not path.is_file():
            missing_guides.append({"name": app["name"], "guide": guide})
            continue
        if app.get("app_store_url") and app.get("cli_command") and not app.get("cli_formula"):
            cli_review.append({"name": app["name"], "cli_command": app["cli_command"], "issue": "missing cli_formula"})
    result = {
        "core_total": len(core),
        "guides_present": len(core) - len(missing_guides),
        "missing_guides": missing_guides,
        "machine_measurements_in_guides": [],
        "app_store_cli_metadata_review": cli_review,
        "size_note": "Current-machine measurements belong in machine-local install records, not component Markdown.",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not missing_guides and not cli_review else 1


if __name__ == "__main__":
    raise SystemExit(main())
