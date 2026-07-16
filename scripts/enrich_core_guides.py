#!/usr/bin/env python3
"""Create Core component guides and persist size estimates/measurements.

The pre-install estimate deliberately remains separate from measured bytes:
catalog ``size_gb`` is a planning estimate; ``installed_bytes`` is measured
from the current bundle or Homebrew prefix after installation.
"""
from __future__ import annotations

import datetime as dt
import json
import plistlib
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "references/app-catalog.json"
APP_DIRS = [Path("/Applications"), Path.home() / "Applications", Path("/System/Applications")]


def bytes_on_disk(path: Path) -> int | None:
    if not path.exists():
        return None
    result = subprocess.run(["du", "-skL", str(path)], capture_output=True, text=True, check=False)
    if result.returncode:
        return None
    try:
        return int(result.stdout.split()[0]) * 1024
    except (IndexError, ValueError):
        return None


def installed_bundles() -> list[dict]:
    found = []
    for directory in APP_DIRS:
        if not directory.is_dir():
            continue
        for app in directory.glob("*.app"):
            info = app / "Contents/Info.plist"
            try:
                meta = plistlib.loads(info.read_bytes())
            except Exception:
                continue
            found.append({
                "name": (meta.get("CFBundleDisplayName") or meta.get("CFBundleName") or app.stem).casefold(),
                "path": app,
                "version": meta.get("CFBundleShortVersionString"),
            })
    return found


def cli_size(app: dict) -> tuple[int | None, str | None, str | None]:
    command = app.get("check_command")
    formula = app.get("brew_formula")
    if not command or not formula or not shutil.which(command):
        return None, None, None
    brew = shutil.which("brew") or "/opt/homebrew/bin/brew"
    prefix = subprocess.run([brew, "--prefix", formula], capture_output=True, text=True, check=False)
    if prefix.returncode:
        return None, None, None
    path = Path(prefix.stdout.strip())
    version_result = subprocess.run([command, "--version"], capture_output=True, text=True, check=False)
    version_lines = (version_result.stdout + version_result.stderr).splitlines()
    return bytes_on_disk(path), str(path), version_lines[0] if version_lines else None


def main() -> int:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    bundles = installed_bundles()
    now = dt.date.today().isoformat()
    for app in data["apps"]:
        if app.get("tier") != "core":
            continue
        guide = app.get("guide") or f"components/{app['name'].lower().replace(' ', '-').replace('/', '-')}.md"
        app["guide"] = guide
        estimate = int(float(app.get("size_gb", 0)) * 1_000_000_000)
        app["download_estimate_bytes"] = estimate
        app["download_estimate_method"] = "catalog_size_gb_planning_estimate"
        aliases = {app["name"].casefold(), *(x.casefold() for x in app.get("aliases", []))}
        bundle = next((x for x in bundles if x["name"] in aliases), None)
        actual = None
        version = None
        if bundle:
            actual = bytes_on_disk(bundle["path"])
            version = bundle["version"]
        cli_actual, cli_path, cli_version = cli_size(app)
        if cli_actual is not None:
            actual, version = cli_actual, cli_version
            app["cli_path"] = cli_path
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
    print("Enriched Core guides and catalog metadata")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
