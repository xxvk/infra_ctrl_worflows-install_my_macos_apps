#!/usr/bin/env python3
# Mutation action ID: dock.save-baseline
"""Scan and persist the current user's macOS Dock application order."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import plistlib
import socket
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from config_layers import resolve_config_path
from state_paths import add_state_dir_argument, resolve_state_dir


def dock_preferences() -> dict:
    result = subprocess.run(
        ["defaults", "export", "com.apple.dock", "-"],
        check=True,
        capture_output=True,
    )
    return plistlib.loads(result.stdout)


def file_url_path(value: object) -> str | None:
    if not isinstance(value, str) or not value.startswith("file://"):
        return None
    return unquote(urlparse(value).path)


def app_kind(path: str | None, bundle_id: str | None) -> str:
    path = (path or "").rstrip("/")
    bundle_id = bundle_id or ""
    if "/WebCatalog Apps/" in path or bundle_id.startswith("com.webcatalog."):
        return "webcatalog"
    if "/Library/Containers/io.playcover.PlayCover/Applications/" in path:
        return "playcover"
    if path.startswith("/System/"):
        return "system"
    if path.endswith(".app"):
        return "native"
    return "other"


def config_path(path: str | None) -> str | None:
    if not path:
        return None
    path = path.rstrip("/")
    home = str(Path.home()).rstrip("/")
    if path == home:
        return "~"
    if path.startswith(home + "/"):
        return "~" + path[len(home) :]
    return path


def scan() -> dict:
    prefs = dock_preferences()
    apps = []
    for order, tile in enumerate(prefs.get("persistent-apps", []), start=1):
        data = tile.get("tile-data", {})
        file_data = data.get("file-data", {})
        path = file_url_path(file_data.get("_CFURLString"))
        bundle_id = data.get("bundle-identifier")
        apps.append(
            {
                "order": order,
                "label": data.get("file-label"),
                "bundle_identifier": bundle_id,
                "path": path,
                "kind": app_kind(path, bundle_id),
                "exists": bool(path and os.path.exists(path)),
                "tile_type": tile.get("tile-type"),
            }
        )
    directories = []
    for order, tile in enumerate(prefs.get("persistent-others", []), start=1):
        data = tile.get("tile-data", {})
        file_data = data.get("file-data", {})
        path = file_url_path(file_data.get("_CFURLString"))
        directories.append({
            "order": order,
            "label": data.get("file-label"),
            "path": path,
            "tile_type": tile.get("tile-type"),
        })
    return {
        "schema_version": 1,
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "source": "defaults export com.apple.dock",
        "persistent_app_count": len(apps),
        "persistent_apps": apps,
        "persistent_directories": directories,
    }


def reusable_config(result: dict) -> dict:
    return {
        "schema_version": 1,
        "description": "Persistent Dock application membership and left-to-right order.",
        "persistent_apps": [
            {
                "order": app["order"],
                "label": app["label"],
                "bundle_identifier": app["bundle_identifier"],
                "path": config_path(app["path"]),
                "kind": app["kind"],
            }
            for app in result["persistent_apps"]
        ],
        "persistent_directories": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Save the current user's persistent Dock apps and order."
    )
    add_state_dir_argument(parser)
    parser.add_argument(
        "--output",
        type=Path,
        help="JSON output path; defaults to machine-local dock-scan-YYYYmmdd-HHMMSS.json",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Also write the reusable Dock order config to this JSON path.",
    )
    parser.add_argument(
        "--save-config",
        action="store_true",
        help="Write the reusable config through settings/dock-order.json to the iCloud Private target.",
    )
    args = parser.parse_args()

    try:
        result = scan()
    except (OSError, subprocess.CalledProcessError, plistlib.InvalidFileException) as exc:
        print(f"Dock scan failed: {exc}", file=sys.stderr)
        return 1

    root = Path(__file__).resolve().parents[1]
    output = args.output or (
        resolve_state_dir(args.state_dir)
        / f"dock-scan-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")

    config = args.config
    if args.save_config:
        config = root / "settings" / "dock-order.json"
    if config:
        if config.is_file():
            config = resolve_config_path(config, root=root)
        config.parent.mkdir(parents=True, exist_ok=True)
        config.write_text(
            json.dumps(reusable_config(result), ensure_ascii=False, indent=2) + "\n"
        )
        result["action_id"] = "dock.save-baseline"

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
