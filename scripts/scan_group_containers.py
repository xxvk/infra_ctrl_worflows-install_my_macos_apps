#!/usr/bin/env python3
"""Read-only audit of macOS Group Containers and likely orphaned data."""

from __future__ import annotations

import argparse
import json
import os
import plistlib
from xml.parsers.expat import ExpatError
from pathlib import Path


HOME = Path.home()
ROOT = HOME / "Library/Group Containers"
APP_ROOTS = (Path("/Applications"), HOME / "Applications")


def directory_size(path: Path) -> int:
    total = 0
    for item in path.rglob("*"):
        try:
            if item.is_file():
                total += item.stat().st_size
        except OSError:
            pass
    return total


def installed_bundle_ids() -> dict[str, str]:
    result: dict[str, str] = {}
    for root in APP_ROOTS:
        if not root.exists():
            continue
        for app in root.glob("*.app"):
            plist = app / "Contents/Info.plist"
            try:
                with plist.open("rb") as stream:
                    bundle_id = plistlib.load(stream).get("CFBundleIdentifier")
                if bundle_id:
                    result[str(bundle_id)] = str(app)
            except (OSError, plistlib.InvalidFileException, ExpatError, ValueError):
                continue
    return result


def metadata(container: Path) -> dict[str, object]:
    path = container / ".com.apple.containermanagerd.metadata.plist"
    try:
        with path.open("rb") as stream:
            data = plistlib.load(stream)
        return {
            "creator": data.get("MCMMetadataCreator"),
            "identifier": data.get("MCMMetadataIdentifier"),
            "content_class": data.get("MCMMetadataContentClass"),
        }
    except (OSError, plistlib.InvalidFileException, ValueError):
        return {"metadata_error": True}


def human_size(value: int) -> str:
    size = float(value)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{value} B"


def scan() -> list[dict[str, object]]:
    installed = installed_bundle_ids()
    rows = []
    if not ROOT.exists():
        return rows
    for container in sorted(ROOT.iterdir()):
        if not container.is_dir():
            continue
        info = metadata(container)
        creator = info.get("creator")
        owner_app = installed.get(str(creator)) if creator else None
        size = directory_size(container)
        rows.append({
            "path": str(container),
            "size_bytes": size,
            "size": human_size(size),
            "creator": creator,
            "metadata_identifier": info.get("identifier"),
            "owner_app": owner_app,
            "likely_orphan": bool(creator and not owner_app),
            "action": "review_only",
        })
    return rows


def deletion_candidates() -> list[dict[str, object]]:
    """Return narrow, app-specific candidates; never whole shared containers."""
    candidates: list[dict[str, object]] = []
    office = ROOT / "UBF8T346G9.Office"
    outlook_app = any((root / "Microsoft Outlook.app").exists() for root in APP_ROOTS)
    if office.exists() and not outlook_app:
        for relative in (Path("Outlook"), Path("OutlookProfile.plist")):
            path = office / relative
            if path.exists():
                candidates.append({
                    "path": str(path),
                    "size_bytes": directory_size(path) if path.is_dir() else path.stat().st_size,
                    "size": human_size(directory_size(path) if path.is_dir() else path.stat().st_size),
                    "reason": "Microsoft Outlook is not installed; this is an Outlook-specific child inside a shared Office container.",
                    "confidence": "review_before_delete",
                    "preserve_parent": str(office),
                    "action": "delete_only_after_explicit_confirmation",
                })
    return candidates


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan macOS Group Containers without deleting anything")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    rows = scan()
    candidates = deletion_candidates()
    if args.json:
        print(json.dumps({"root": str(ROOT), "count": len(rows), "containers": rows, "deletion_candidates": candidates}, indent=2, ensure_ascii=False))
        return 0
    print(f"Group Containers: {ROOT}")
    print("Read-only scan. 'likely_orphan' means the metadata creator did not match an installed app; it is not proof that deletion is safe.")
    for row in sorted(rows, key=lambda item: int(item["size_bytes"]), reverse=True):
        owner = row["owner_app"] or "no matching app bundle"
        orphan = " REVIEW" if row["likely_orphan"] else ""
        print(f"{row['size']:>10}  {row['creator'] or 'unknown':<42}  {owner}{orphan}")
        print(f"            {row['path']}")
    print("\nDeletion candidates (narrow paths only; explicit confirmation still required):")
    if not candidates:
        print("  none detected")
    for candidate in candidates:
        print(f"{candidate['size']:>10}  {candidate['path']}")
        print(f"            reason: {candidate['reason']}")
        print(f"            preserve: {candidate['preserve_parent']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
