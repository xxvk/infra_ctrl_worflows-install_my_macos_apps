#!/usr/bin/env python3
"""Create lightweight guides for every non-Core catalog item."""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "references/app-catalog.json"


def slug(name: str) -> str:
    value = re.sub(r"[^\w.-]+", "-", name.strip().lower(), flags=re.UNICODE).strip("-")
    return value or "component"


def source(app: dict) -> str:
    if app.get("app_store_url"):
        return "app_store"
    if app.get("brew_cask") or app.get("brew_formula"):
        return "homebrew"
    return "official_web"


def delivery(app: dict, kind: str) -> str:
    if kind == "app_store":
        return f"Mac App Store: {app['app_store_url']}"
    if kind == "homebrew":
        token = app.get("brew_cask") or app.get("brew_formula")
        flag = "--cask " if app.get("brew_cask") else ""
        return f"`brew install {flag}{token}`"
    return app.get("official_url", "来源待确认")


def main() -> int:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    now = dt.date.today().isoformat()
    created = 0
    for app in data["apps"]:
        if app.get("tier") == "core":
            continue
        guide = app.get("guide") or f"components/{slug(app['name'])}.md"
        app["guide"] = guide
        estimate = int(float(app.get("size_gb", 0)) * 1_000_000_000)
        app["download_estimate_bytes"] = estimate
        app["download_estimate_method"] = "catalog_size_gb_planning_estimate"
        path = ROOT / guide
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            continue
        kind = source(app)
        follow_up = app.get("follow_up", [])
        checklist = "\n".join(f"- [ ] {item}" for item in follow_up) or "- [ ] Open and verify the app"
        text = f'''---
component_id: {json.dumps(slug(app['name']), ensure_ascii=False)}
name: {json.dumps(app['name'], ensure_ascii=False)}
category: {json.dumps(app.get('category', ''), ensure_ascii=False)}
tier: {app['tier']}
lifecycle_status: planned
delivery_method: {kind.replace('_', '-')}
brew_cask: {json.dumps(app.get('brew_cask'))}
brew_formula: {json.dumps(app.get('brew_formula'))}
official_url: {json.dumps(app.get('official_url'))}
check_command: {json.dumps(app.get('check_command'))}
install_after: []
source: {kind}
download_estimate_bytes: {estimate}
download_estimate_method: catalog_size_gb_planning_estimate
account_required: {str(bool(app.get('preferred_account'))).lower()}
permissions_required: []
secrets_policy: Never store passwords, API keys, recovery codes, or license secrets here.
---
# {app['name']}

## Delivery

- Preferred source: {delivery(app, kind)}
- This is an Optional item; do not install automatically during a Core deployment.
- App Store installs require the user to complete Get/Download, password, Touch ID, or 2FA.

## Size tracking

- Planning download estimate: {estimate} bytes (`size_gb` catalog estimate).
- Actual download and installed footprint remain `null` until installation is performed and measured.
- After installation, record `download_bytes`, `installed_bytes`, `installed_version`, and `installed_at`.

## Post-install checklist

{checklist}

## Notes

{app.get('note', 'Review account, license, privacy, and storage settings before using the app.')}
'''
        path.write_text(text, encoding="utf-8")
        created += 1
    CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Created {created} non-Core guides")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
