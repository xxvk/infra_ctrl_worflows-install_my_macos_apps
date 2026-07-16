#!/usr/bin/env python3
"""Add local version/footprint evidence to non-Core component guides."""
from __future__ import annotations

import datetime as dt
import json
import plistlib
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "references/app-catalog.json"
APP_DIRS = [Path("/Applications"), Path.home() / "Applications"]


def local_apps() -> list[dict]:
    found = []
    for base in APP_DIRS:
        if not base.is_dir():
            continue
        for path in base.glob("*.app"):
            try:
                meta = plistlib.loads((path / "Contents/Info.plist").read_bytes())
            except Exception:
                continue
            du = subprocess.run(["du", "-sk", str(path)], capture_output=True, text=True, check=False)
            size = int(du.stdout.split()[0]) * 1024 if du.stdout.split() else None
            label = (meta.get("CFBundleDisplayName") or meta.get("CFBundleName") or path.stem)
            found.append({"name": label.casefold(), "path": str(path), "version": meta.get("CFBundleShortVersionString"), "bytes": size})
    return found


def replace_field(text: str, key: str, value: object) -> str:
    rendered = json.dumps(value, ensure_ascii=False) if value is not None else "null"
    updated, count = re.subn(rf"^{re.escape(key)}:.*$", f"{key}: {rendered}", text, count=1, flags=re.MULTILINE)
    return updated if count else text.replace("---\n", f"---\n{key}: {rendered}\n", 1)


def main() -> int:
    data = json.loads(CATALOG.read_text(encoding="utf-8"))
    installed = local_apps()
    today = dt.date.today().isoformat()
    changed = 0
    for app in data["apps"]:
        if app.get("tier") == "core" or not app.get("guide"):
            continue
        aliases = {app["name"].casefold(), *(x.casefold() for x in app.get("aliases", []))}
        hit = next((x for x in installed if x["name"] in aliases), None)
        if not hit:
            continue
        path = ROOT / app["guide"]
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        text = replace_field(text, "status", "installed")
        text = replace_field(text, "installed_bytes", hit["bytes"])
        text = replace_field(text, "installed_version", hit["version"])
        text = replace_field(text, "installed_at", today)
        text = replace_field(text, "installed_measurement_method", "local_du")
        if app["name"] == "Brave Browser":
            text = replace_field(text, "download_bytes", 151494656)
            text = replace_field(text, "download_measurement_method", "homebrew_install_log")
        evidence = (
            f"\n## Local evidence ({today})\n\n"
            f"- Installed path: `{hit['path']}`\n"
            f"- Installed version: `{hit['version'] or 'unknown'}`\n"
            f"- Installed footprint: `{hit['bytes'] if hit['bytes'] is not None else 'unknown'}` bytes, measured with `du -sk`.\n"
            f"- Download bytes are recorded separately; a local bundle footprint is not treated as download volume.\n"
        )
        if "## Local evidence (" not in text:
            text = text.rstrip() + "\n" + evidence
        path.write_text(text, encoding="utf-8")
        changed += 1
    CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Enriched {changed} installed non-Core guides")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
