#!/usr/bin/env python3
"""Create Core component guides and persist planning estimates only.

Detected versions, paths, and measured bytes belong in machine-local state and
must never be copied into the catalog or component Markdown.
"""
from __future__ import annotations

import json
from pathlib import Path

from config_layers import load_app_catalog

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "references/mac-app-catalog.json"
def main() -> int:
    data = load_app_catalog(CATALOG)
    for app in data["apps"]:
        if app.get("tier") != "core":
            continue
        guide = app.get("guide") or f"components/{app['name'].lower().replace(' ', '-').replace('/', '-')}.md"
        app["guide"] = guide
        estimate = int(float(app.get("size_gb", 0)) * 1_000_000_000)
        app["download_estimate_bytes"] = estimate
        app["download_estimate_method"] = "catalog_size_gb_planning_estimate"
        path = ROOT / guide
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            text = path.read_text(encoding="utf-8")
        else:
            text = f"---\ncomponent_id: {app['name'].lower().replace(' ', '-')}\nname: {app['name']}\ncategory: {app.get('category', '')}\ntier: core\nlifecycle_status: active\ndelivery_method: {'app-store' if app.get('app_store_url') else 'homebrew-cask' if app.get('brew_cask') else 'homebrew-formula' if app.get('brew_formula') else 'vendor-download'}\nbrew_cask: {app.get('brew_cask')}\nbrew_formula: {app.get('brew_formula')}\nofficial_url: {app.get('official_url')}\ncheck_command: {app.get('check_command')}\ninstall_after: []\naccount_required: false\npermissions_required: []\nsecrets_policy: Never store passwords, API keys, recovery codes, or license secrets here.\n---\n\n# {app['name']}\n\n"
        metadata = (
            f"download_estimate_bytes: {estimate}\n"
            f"download_estimate_method: catalog_size_gb_planning_estimate\n"
        )
        if text.startswith("---\n"):
            end = text.find("\n---", 4)
            body = text[end + 5:].lstrip("\n") if end >= 0 else text
            text = text[:4] + metadata + text[end:] if end >= 0 else text
            if end >= 0:
                text = text[:4] + metadata + text[end:]
        else:
            text = "---\n" + metadata + "---\n\n" + text
        path.write_text(text, encoding="utf-8")
    CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Enriched Core guides and catalog planning metadata")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
