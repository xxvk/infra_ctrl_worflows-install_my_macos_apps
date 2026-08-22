#!/usr/bin/env python3
"""Report local version/footprint evidence without editing tracked guides."""
from __future__ import annotations

import json
import plistlib
import subprocess
from pathlib import Path

from config_layers import load_app_catalog

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "references/mac-app-catalog.json"
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


def main() -> int:
    data = load_app_catalog(CATALOG)
    installed = local_apps()
    observations = []
    for app in data["apps"]:
        if app.get("tier") == "core" or not app.get("guide"):
            continue
        aliases = {app["name"].casefold(), *(x.casefold() for x in app.get("aliases", []))}
        hit = next((x for x in installed if x["name"] in aliases), None)
        if not hit:
            continue
        observations.append(
            {
                "name": app["name"],
                "guide": app["guide"],
                "detected_path": hit["path"],
                "detected_version": hit["version"],
                "installed_bytes": hit["bytes"],
            }
        )
    print(
        json.dumps(
            {
                "mode": "read_only_machine_observation",
                "tracked_files_written": False,
                "observations": observations,
                "state_policy": "Persist this output only in machine-local state.",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
