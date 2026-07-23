#!/usr/bin/env python3
"""Semantic validation for references/app-catalog.json.

The formal JSON Schema validates the versioned structural envelope. This
read-only validator complements it with catalog-specific cross-field rules
such as source consistency, duplicate names, and guide-file existence. Run
both after any manual catalog edit.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "references/app-catalog.json"

REQUIRED_FIELDS = ["name", "category", "tier", "guide"]
VALID_TIERS = {"core", "optional", "heavy"}


def validate(catalog: dict, root: Path = ROOT) -> list[str]:
    errors = []
    apps = catalog.get("apps")
    if not isinstance(apps, list):
        return ["catalog has no top-level 'apps' list"]

    seen_names = {}
    for index, app in enumerate(apps):
        label = app.get("name") or f"<entry {index}>"

        for field in REQUIRED_FIELDS:
            if not app.get(field):
                errors.append(f"{label}: missing required field '{field}'")

        tier = app.get("tier")
        if tier is not None and tier not in VALID_TIERS:
            errors.append(f"{label}: tier '{tier}' is not one of {sorted(VALID_TIERS)}")

        name = app.get("name")
        if name:
            if name in seen_names:
                errors.append(f"{label}: duplicate name (also entry {seen_names[name]})")
            seen_names[name] = index

        guide = app.get("guide")
        if guide and not (root / guide).is_file():
            errors.append(f"{label}: guide path '{guide}' does not exist")

        has_source = any([
            app.get("brew_cask"), app.get("brew_formula"),
            app.get("app_store_url"), app.get("official_url"),
            app.get("system_app"),
        ])
        if not has_source:
            errors.append(f"{label}: no source field present (brew_cask/brew_formula/app_store_url/official_url/system_app)")

        app_store_url = app.get("app_store_url")
        if app_store_url and not (app_store_url.startswith("macappstore://") or "apps.apple.com" in app_store_url):
            errors.append(f"{label}: app_store_url '{app_store_url}' does not look like an App Store URL")

    return errors


def main() -> int:
    catalog = json.loads(CATALOG_PATH.read_text())
    errors = validate(catalog)
    result = {
        "catalog_path": str(CATALOG_PATH),
        "app_count": len(catalog.get("apps", [])),
        "error_count": len(errors),
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
