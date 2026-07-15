#!/usr/bin/env python3
"""Normalize Core guide frontmatter from the catalog while preserving bodies."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    data = json.loads((ROOT / "references/app-catalog.json").read_text(encoding="utf-8"))
    changed = 0
    for app in data["apps"]:
        if app.get("tier") != "core" or not app.get("guide"):
            continue
        path = ROOT / app["guide"]
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if not text.startswith("---\n"):
            body = text
        else:
            end = text.find("\n---\n", 4)
            body = text[end + 5:] if end >= 0 else ""
        source = "app_store" if app.get("app_store_url") else "homebrew" if app.get("brew_formula") or app.get("brew_cask") else "official_web"
        estimate = app.get("download_estimate_bytes")
        installed = "null"
        version = "null"
        installed_at = "null"
        for line in text.splitlines():
            if line.startswith("installed_bytes:"):
                installed = line.split(":", 1)[1].strip()
            elif line.startswith("installed_version:"):
                version = line.split(":", 1)[1].strip()
            elif line.startswith("installed_at:"):
                installed_at = line.split(":", 1)[1].strip()
        front = "\n".join([
            "---",
            f"name: {json.dumps(app['name'], ensure_ascii=False)}",
            f"category: {json.dumps(app.get('category',''), ensure_ascii=False)}",
            f"tier: {app['tier']}",
            f"status: {'installed' if installed != 'null' else 'planned'}",
            f"source: {source}",
            f"download_bytes: null",
            f"download_estimate_bytes: {estimate}",
            "download_estimate_method: catalog_size_gb_planning_estimate",
            f"installed_bytes: {installed}",
            f"installed_version: {version}",
            f"installed_at: {installed_at}",
            "secrets_policy: Never store passwords, API keys, recovery codes, or license secrets here.",
            "---",
            "",
        ])
        path.write_text(front + body.lstrip("\n"), encoding="utf-8")
        changed += 1
    print(f"Normalized {changed} Core frontmatter files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
