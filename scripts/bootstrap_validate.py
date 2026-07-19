#!/usr/bin/env python3
"""Validate that the tracked bootstrap definition is self-contained."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "SKILL.md",
    "README.md",
    "references/app-catalog.json",
    "settings/privacy.yaml",
    "settings/system-preferences.yaml",
    "settings/system-preferences-values.json",
    "settings/manual-actions.yaml",
    "settings/dock-order.json",
    "settings/keyboard.yaml",
    "scripts/bootstrap_macos.py",
    "scripts/macos_apps.py",
    "scripts/macos_permissions.py",
    "scripts/macos_permissions_cleanup.py",
    "scripts/macos_preferences.py",
]


def main() -> int:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    catalog = json.loads((ROOT / "references/app-catalog.json").read_text())
    guide_missing = []
    for app in catalog.get("apps", []):
        guide = app.get("guide")
        if guide and not (ROOT / guide).is_file():
            guide_missing.append({"name": app.get("name"), "guide": guide})
    result = {
        "mode": "tracked_definition_only",
        "state_read": False,
        "required_files": len(REQUIRED_FILES),
        "missing_files": missing,
        "catalog_apps": len(catalog.get("apps", [])),
        "missing_guides": guide_missing,
        "status": "passed" if not missing and not guide_missing else "failed",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
