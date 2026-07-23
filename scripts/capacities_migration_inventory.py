#!/usr/bin/env python3
"""Inventory Capacities data locations without reading document contents."""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
from pathlib import Path

from state_paths import add_state_dir_argument, resolve_state_dir


ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
CANDIDATES = [
    Path("/Applications/Capacities.app"),
    HOME / "Library/Application Support/Capacities",
    HOME / "Library/Preferences/io.capacities.app.plist",
    HOME / "Library/HTTPStorages/io.capacities.app",
    HOME / "Library/Logs/Capacities",
]


def inspect(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"path": str(path), "present": False}
    if path.is_file():
        return {"path": str(path), "present": True, "kind": "file", "bytes": path.stat().st_size}
    total = 0
    files = 0
    extensions = collections.Counter()
    newest = None
    for child in path.rglob("*"):
        if not child.is_file():
            continue
        files += 1
        try:
            stat = child.stat()
        except OSError:
            continue
        total += stat.st_size
        extensions[child.suffix.lower() or "<no_extension>"] += 1
        newest = max(newest or stat.st_mtime, stat.st_mtime)
    return {
        "path": str(path),
        "present": True,
        "kind": "directory",
        "bytes": total,
        "file_count": files,
        "extension_counts": dict(extensions.most_common(20)),
        "newest_modified_at": dt.datetime.fromtimestamp(newest, dt.timezone.utc).isoformat() if newest else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_state_dir_argument(parser)
    args = parser.parse_args()
    result = {
        "schema_version": 1,
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "mode": "read_only_migration_preflight",
        "paths": [inspect(path) for path in CANDIDATES],
        "policy": "No Capacities document contents were read, moved, exported, or deleted.",
        "next_action": "User must export/verify required data before app or support-data cleanup.",
    }
    state_dir = resolve_state_dir(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    output = state_dir / f"capacities-migration-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(output), "paths": result["paths"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
