#!/usr/bin/env python3
"""Export the iPhone home-screen layout to Markdown via pymobiledevice3.

Reads SpringBoard getIconState with full detail (app bundle ids, folder
contents, widget kind + grid size) and writes a Markdown archive under
Private/device-layouts/ (gitignored, iCloud-synced).

Usage:
    python3 scripts/ios-layout-export-pymd3.py [--udid <UDID>] [--output <path>]

Requires: pymobiledevice3 in a venv (see README), iPhone unlocked, Developer
Mode enabled (see components/libimobiledevice.md / go-ios.md).
"""

from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

PYMD3 = "pymobiledevice3"  # resolve via PATH or pass --pymd3


def run_pymd3(args: list[str], udid: str | None) -> str:
    cmd = [PYMD3]
    if udid:
        cmd += ["--udid", udid]
    cmd += args
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"pymobiledevice3 {args} failed: {r.stderr[-500:]}")
    return r.stdout


def run_pymd3_global(args: list[str], udid: str | None) -> str:
    """Run a top-level pymobiledevice3 command; --udid must come after it."""
    cmd = [PYMD3] + args
    if udid:
        cmd += ["--udid", udid]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"pymobiledevice3 {args} failed: {r.stderr[-500:]}")
    return r.stdout


def describe_item(item: dict) -> tuple[str, str, str]:
    """Return (name, type, detail) for one icon-state item."""
    name = item.get("displayName") or ""
    kind = item.get("elementType") or item.get("iconType") or ""
    if item.get("iconLists"):  # folder
        total = sum(len(page) for page in item["iconLists"])
        pages = len(item["iconLists"])
        detail = f"folder: {total} icons / {pages} pages"
        return name or "(folder)", "Folder", detail
    if kind == "widget" or item.get("iconType") == "custom":
        w = item.get("widgetIdentifier") or ""
        g = item.get("gridSize") or ""
        size = {"small": "小", "medium": "中", "large": "大"}.get(g, g)
        return name or "(widget)", f"Widget({size})", w
    bid = item.get("bundleIdentifier") or ""
    return name or "(app)", "App", bid


def folder_contents(item: dict) -> list[str]:
    """Expand a folder into per-page lines of its contained app names."""
    out: list[str] = []
    for page_idx, page in enumerate(item.get("iconLists", []), start=1):
        names = []
        for app in page:
            if not isinstance(app, dict):
                continue
            nm = app.get("displayName") or "(app)"
            bid = app.get("bundleIdentifier") or ""
            names.append(f"{nm} (`{bid}`)")
        out.append(f"  - 页 {page_idx}: {', '.join(names)}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--udid", default=None, help="target device UDID")
    ap.add_argument("--output", default=None, help="output Markdown path")
    ap.add_argument(
        "--pymd3",
        default="pymobiledevice3",
        help="path to the pymobiledevice3 CLI (default: on PATH)",
    )
    args = ap.parse_args()
    global PYMD3
    PYMD3 = args.pymd3

    state = json.loads(run_pymd3(["springboard", "state", "get"], None))

    # device name (best effort)
    device_label = args.udid or "iPhone"
    try:
        info = json.loads(run_pymd3_global(["lockdown", "info"], args.udid))
        if isinstance(info, dict) and info.get("DeviceName"):
            device_label = f"{info['DeviceName']} ({args.udid})"
    except Exception:
        pass

    lines: list[str] = []
    lines.append("# iPhone home screen layout\n")
    lines.append(f"- Device: `{device_label}`")
    lines.append(f"- Generated: {datetime.datetime.now().astimezone().isoformat()}")
    lines.append(f"- Screens: {len(state)} (index 0 = dock)\n")

    for i, screen in enumerate(state):
        title = "Dock (screen 0)" if i == 0 else f"Screen {i}"
        lines.append(f"## {title}\n")
        lines.append("| # | Name | Type | Detail |")
        lines.append("|---|---|---|---|")
        folder_blocks: list[str] = []
        for j, item in enumerate(screen):
            if not isinstance(item, dict):
                continue
            name, kind, detail = describe_item(item)
            safe = lambda s: str(s).replace("|", "\\|")
            lines.append(f"| {j+1} | {safe(name)} | {safe(kind)} | {safe(detail)} |")
            if item.get("iconLists"):
                folder_blocks.append(f"**{name}** 内容：\n" + "\n".join(folder_contents(item)))
        lines.append("")
        if folder_blocks:
            lines.append("<details>")
            lines.append("<summary>文件夹内容展开</summary>")
            lines.append("")
            lines.extend(folder_blocks)
            lines.append("</details>")
            lines.append("")

    out = args.output or f"Private/device-layouts/iphone-home-layout-{datetime.date.today()}.md"
    Path(out).write_text("\n".join(lines), encoding="utf-8")
    print(f"layout written to {out} ({len(state)} screens)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
