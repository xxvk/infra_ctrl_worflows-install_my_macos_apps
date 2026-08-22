#!/usr/bin/env python3
"""Repair catalog-linked component frontmatter without rewriting guide bodies."""
from __future__ import annotations

import datetime as dt
import json
import re
import subprocess
from pathlib import Path

from config_layers import load_app_catalog

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "references/mac-app-catalog.json"

REQUIRED = [
    "component_id", "name", "category", "tier", "lifecycle_status", "source", "delivery_method",
    "brew_cask", "brew_formula", "official_url", "check_command", "install_after",
    "account_required", "permissions_required", "secrets_policy",
]


def parse_value(value: str):
    value = value.strip()
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        if value in {"true", "false"}:
            return value == "true"
        if value == "null":
            return None
        return value.strip('"\'')


def parse_front(text: str) -> tuple[dict, str, bool]:
    lines = text.splitlines(keepends=True)
    if lines and lines[0].strip() == "---":
        close = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
        if close is not None:
            meta = {}
            for line in lines[1:close]:
                if ":" in line and not line.startswith((" ", "-")):
                    key, value = line.split(":", 1)
                    meta[key.strip()] = parse_value(value)
            return meta, "".join(lines[close + 1:]), True
        marker = next((i for i, line in enumerate(lines) if line.startswith("installed_at:")), None)
        if marker is not None:
            meta = {}
            for line in lines[1:marker + 1]:
                if ":" in line and not line.startswith((" ", "-")):
                    key, value = line.split(":", 1)
                    meta[key.strip()] = parse_value(value)
            return meta, "".join(lines[marker + 1:]), False
    return {}, text, False


def git_frontmatter(path: Path) -> dict:
    try:
        raw = subprocess.run(["git", "show", f"HEAD:{path.relative_to(ROOT)}"], cwd=ROOT,
                             capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        return {}
    return parse_front(raw)[0]


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")


def source(app: dict) -> str:
    if app.get("app_store_url"):
        return "app_store"
    if app.get("brew_cask") or app.get("brew_formula"):
        return "homebrew"
    if app.get("npm_package"):
        return "npm_global"
    if app.get("official_url"):
        return "official_web"
    return "manual"


def delivery(app: dict) -> str:
    if app.get("app_store_url"):
        return "app-store"
    if app.get("brew_cask"):
        return "homebrew-cask"
    if app.get("brew_formula"):
        return "homebrew-formula"
    if app.get("npm_package"):
        return "npm-global"
    if app.get("official_url"):
        return "vendor-download"
    return "manual"


def render(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def main() -> int:
    data = load_app_catalog(CATALOG)
    changed = 0
    for app in data["apps"]:
        guide = app.get("guide")
        if not guide:
            continue
        path = ROOT / guide
        if not path.is_file():
            continue
        current, body, valid = parse_front(path.read_text(encoding="utf-8"))
        baseline = git_frontmatter(path)
        values = {**baseline, **current}
        values.setdefault("name", app["name"])
        values.setdefault("category", app.get("category", ""))
        values.setdefault("tier", app.get("tier", "optional"))
        values.setdefault("lifecycle_status", "planned")
        values.setdefault("source", source(app))
        values.setdefault("secrets_policy", "Never store passwords, API keys, recovery codes, or license secrets here.")
        standard = {
            "component_id": app.get("component_id") or slug(app["name"]),
            "name": app["name"],
            "category": app.get("category", values.get("category", "")),
            "tier": app.get("tier", values.get("tier", "optional")),
            "lifecycle_status": values.get("lifecycle_status", "active"),
            "delivery_method": delivery(app),
            "brew_cask": app.get("brew_cask"),
            "brew_formula": app.get("brew_formula"),
            "official_url": app.get("official_url"),
            "check_command": app.get("check_command"),
            "install_after": app.get("install_after", []),
            "account_required": values.get("account_required", bool(app.get("preferred_account"))),
            "permissions_required": values.get("permissions_required", []),
            "secrets_policy": values.get("secrets_policy"),
            "source": values.get("source", source(app)),
            "download_estimate_bytes": app.get("download_estimate_bytes", int(float(app.get("size_gb", 0)) * 1_000_000_000)),
            "download_estimate_method": app.get("download_estimate_method", "catalog_size_gb_planning_estimate"),
        }
        for extra in (
            "brew_tap",
            "brew_tap_repository",
            "brew_tap_revision",
            "brew_trust_cask",
            "npm_package",
            "npm_version",
            "cli_path",
        ):
            if extra in app or extra in values:
                standard[extra] = values.get(extra, app.get(extra))
        front = "---\n" + "\n".join(f"{key}: {render(standard[key])}" for key in [*REQUIRED, "download_estimate_bytes", "download_estimate_method", *[x for x in standard if x not in REQUIRED and x not in {"download_estimate_bytes", "download_estimate_method"}]]) + "\n---\n"
        path.write_text(front + body.lstrip("\n"), encoding="utf-8")
        changed += 1
    print(f"Repaired {changed} component frontmatter files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
