#!/usr/bin/env python3
"""Audit every catalog-linked component guide against the app template."""
from __future__ import annotations

import json
from pathlib import Path

from component_state import audit as audit_component_state
from config_layers import load_app_catalog

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "references/mac-app-catalog.json"

REQUIRED = {
    "component_id", "name", "category", "tier", "lifecycle_status", "source", "delivery_method",
    "brew_cask", "brew_formula", "official_url", "check_command", "install_after",
    "account_required", "permissions_required", "secrets_policy",
}


def frontmatter(path: Path) -> tuple[set[str], bool]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return set(), False
    end = text.find("\n---\n", 4)
    if end < 0:
        return set(), False
    keys = {line.split(":", 1)[0].strip() for line in text[4:end].splitlines()
            if ":" in line and not line.startswith((" ", "-"))}
    return keys, True


def main() -> int:
    data = load_app_catalog(CATALOG)
    failures = []
    catalog_guides = set()
    for app in data["apps"]:
        guide = app.get("guide")
        if not guide:
            continue
        path = ROOT / guide
        catalog_guides.add(path.resolve())
        if not path.is_file():
            failures.append({"app": app["name"], "guide": guide, "issue": "missing_file"})
            continue
        keys, valid = frontmatter(path)
        missing = sorted(REQUIRED - keys)
        if not valid:
            failures.append({"app": app["name"], "guide": guide, "issue": "invalid_frontmatter"})
        elif missing:
            failures.append({"app": app["name"], "guide": guide, "issue": "missing_fields", "fields": missing})
    for path in sorted((ROOT / "components").glob("*.md")):
        if path.name == "README.md" or path.resolve() in catalog_guides:
            continue
        keys, valid = frontmatter(path)
        if not valid or REQUIRED - keys:
            failures.append({"guide": str(path.relative_to(ROOT)), "issue": "unlinked_or_invalid_component", "fields": sorted(REQUIRED - keys)})
    machine_state = audit_component_state()
    result = {
        "required_fields": sorted(REQUIRED),
        "checked_catalog_guides": len(catalog_guides),
        "failures": failures,
        "machine_state_boundary": {
            key: value
            for key, value in machine_state.items()
            if key != "findings" or value
        },
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if failures or machine_state["status"] != "passed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
