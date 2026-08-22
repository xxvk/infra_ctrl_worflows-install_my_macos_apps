#!/usr/bin/env python3
"""Archive visible Pixel Launcher pages via adb UI hierarchy and screenshots."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "Private/device-layouts"
BOUNDS_RE = re.compile(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]")


def run_adb(serial: str, args: list[str], *, binary: bool = False) -> bytes | str:
    result = subprocess.run(
        ["adb", "-s", serial, *args], capture_output=True, check=False, timeout=45
    )
    if result.returncode:
        error = result.stderr.decode(errors="replace").strip()
        raise RuntimeError(f"adb {' '.join(args)} failed: {error}")
    return result.stdout if binary else result.stdout.decode(errors="replace").strip()


def choose_device(requested: str | None) -> str:
    result = subprocess.run(["adb", "devices"], capture_output=True, text=True, timeout=15)
    devices = [line.split()[0] for line in result.stdout.splitlines()[1:] if "\tdevice" in line]
    if requested:
        if requested not in devices:
            raise RuntimeError(f"requested adb device is not connected: {requested}")
        return requested
    if len(devices) != 1:
        raise RuntimeError(f"expected exactly one adb device, found {len(devices)}; use --serial")
    return devices[0]


def capture_xml(serial: str, remote: str) -> str:
    for _ in range(3):
        run_adb(serial, ["shell", "rm", "-f", remote])
        run_adb(serial, ["shell", "uiautomator", "dump", remote])
        result = subprocess.run(
            ["adb", "-s", serial, "shell", "cat", remote], capture_output=True, timeout=30
        )
        text = result.stdout.decode(errors="replace").strip()
        if result.returncode == 0 and text.startswith("<?xml"):
            return text
        time.sleep(1)
    raise RuntimeError(f"uiautomator did not produce a readable hierarchy: {remote}")


def bounds(node: ET.Element) -> list[int] | None:
    match = BOUNDS_RE.fullmatch(node.get("bounds", ""))
    return [int(value) for value in match.groups()] if match else None


def visible_labels(node: ET.Element) -> list[str]:
    labels: list[str] = []
    for child in node.iter():
        for key in ("text", "content-desc"):
            value = child.get(key, "").strip()
            if value and value not in labels:
                labels.append(value)
    return labels


def parse_page(xml_text: str, page: int) -> dict:
    root = ET.fromstring(xml_text)
    widgets: list[dict] = []
    widget_descendants: set[int] = set()
    for node in root.iter():
        if node.get("class", "").endswith("LauncherAppWidgetHostView"):
            widget_descendants.update(id(child) for child in node.iter())
            packages = [n.get("package", "") for n in node.iter() if n.get("package")]
            host = next((pkg for pkg in packages if "nexuslauncher" not in pkg), None)
            widgets.append(
                {
                    "name": node.get("content-desc") or None,
                    "package": host,
                    "bounds": bounds(node),
                    "visible_labels": visible_labels(node),
                    "evidence": "ui_confirmed",
                }
            )

    workspace_items: list[dict] = []
    workspace = next(
        (n for n in root.iter() if n.get("resource-id", "").endswith(":id/workspace")), None
    )
    if workspace is not None:
        for node in workspace.iter():
            if id(node) in widget_descendants or node.get("clickable") != "true":
                continue
            desc = node.get("content-desc", "")
            if node.get("long-clickable") != "true" and not desc.startswith("Folder:"):
                continue
            box = bounds(node)
            if not box or box[1] >= 1929:
                continue
            text = node.get("text", "")
            workspace_items.append(
                {
                    "name": text or desc.split(":", 1)[-1].split(",", 1)[0].strip(),
                    "type": "folder" if desc.startswith("Folder:") else "icon",
                    "description": desc or None,
                    "bounds": box,
                    "evidence": "ui_confirmed",
                }
            )
        workspace_items.sort(key=lambda item: (item["bounds"][1], item["bounds"][0]))

    hotseat: list[dict] = []
    hotseat_node = next(
        (n for n in root.iter() if n.get("resource-id", "").endswith(":id/hotseat")), None
    )
    if hotseat_node is not None:
        candidates = []
        for node in hotseat_node.iter():
            desc = node.get("content-desc", "")
            is_folder = desc.startswith("Folder:")
            if node.get("clickable") != "true" or (
                node.get("long-clickable") != "true" and not is_folder
            ):
                continue
            box = bounds(node)
            if box and box[1] < 2149:
                candidates.append(node)
        for node in candidates:
            desc = node.get("content-desc", "")
            text = node.get("text", "")
            kind = "folder" if desc.startswith("Folder:") else "predicted_app" if desc.startswith("Predicted app:") else "app"
            hotseat.append(
                {
                    "name": text or desc.split(":", 1)[-1].split(",", 1)[0].strip(),
                    "type": kind,
                    "description": desc or None,
                    "bounds": bounds(node),
                    "evidence": "ui_confirmed",
                }
            )
        hotseat.sort(key=lambda item: item["bounds"][0])

    return {"page": page, "widgets": widgets, "workspace_items": workspace_items, "hotseat": hotseat}


def capture_folders(serial: str, hotseat: list[dict], output_dir: Path, stem: str) -> list[dict]:
    folders: list[dict] = []
    for index, item in enumerate((x for x in hotseat if x["type"] == "folder"), 1):
        x1, y1, x2, y2 = item["bounds"]
        xml_name = f"{stem}-folder-{index:02d}.xml"
        content = None
        for _ in range(2):
            run_adb(serial, ["shell", "input", "tap", str((x1 + x2) // 2), str((y1 + y2) // 2)])
            time.sleep(2)
            xml_text = capture_xml(serial, f"/sdcard/macomrade-folder-{index}.xml")
            root = ET.fromstring(xml_text)
            content = next(
                (n for n in root.iter() if n.get("resource-id", "").endswith(":id/folder_content")), None
            )
            if content is not None:
                break
        if content is None:
            raise RuntimeError(f"folder did not open: {item['name']}")
        (output_dir / xml_name).write_text(xml_text, encoding="utf-8")
        members = []
        if content is not None:
            for node in content.iter():
                if node.get("clickable") == "true" and node.get("long-clickable") == "true":
                    name = node.get("text") or node.get("content-desc")
                    if name:
                        members.append({"name": name, "bounds": bounds(node)})
        shot_name = f"{stem}-folder-{index:02d}.png"
        (output_dir / shot_name).write_bytes(
            bytes(run_adb(serial, ["exec-out", "screencap", "-p"], binary=True))
        )
        folders.append(
            {
                "name": item["name"], "members": members, "item_count": len(members),
                "screenshot": shot_name, "ui_hierarchy": xml_name, "evidence": "ui_confirmed",
            }
        )
        run_adb(serial, ["shell", "input", "keyevent", "KEYCODE_BACK"])
        time.sleep(1)
    return folders


def markdown(report: dict) -> str:
    lines = [
        "# Pixel home screen audit",
        "",
        f"- Device: `{report['device']['model']}` (`{report['device']['serial']}`)",
        f"- Generated: {report['generated_at']}",
        "- Evidence: UI hierarchy plus native adb screenshots; grid placement is not database-confirmed.",
        "",
    ]
    for page in report["pages"]:
        lines += [f"## Page {page['page']}", "", "### Widgets", ""]
        if not page["widgets"]:
            lines.append("- None exposed in the UI hierarchy.")
        for widget in page["widgets"]:
            label = widget["name"] or widget["package"] or "Unnamed widget"
            detail = "; ".join(widget["visible_labels"][:8])
            lines.append(f"- **{label}** — `{widget['package']}` — bounds `{widget['bounds']}` — {detail}")
        lines += ["", "### Icons and folders", "", "| Name | Type | Bounds | Evidence |", "|---|---|---|---|"]
        for item in page["workspace_items"]:
            lines.append(f"| {item['name']} | {item['type']} | `{item['bounds']}` | {item['evidence']} |")
        lines += ["", "### Hotseat", "", "| # | Name | Type | Evidence |", "|---|---|---|---|"]
        for index, item in enumerate(page["hotseat"], 1):
            lines.append(f"| {index} | {item['name']} | {item['type']} | {item['evidence']} |")
        lines += ["", f"Screenshot: `{page['screenshot']}`", f"UI hierarchy: `{page['ui_hierarchy']}`", ""]
    lines += ["## Hotseat folder contents", ""]
    for folder in report["folders"]:
        names = ", ".join(member["name"] for member in folder["members"])
        lines.append(f"- **{folder['name']}** ({folder['item_count']}): {names}")
        lines.append(f"  - Evidence: `{folder['screenshot']}`, `{folder['ui_hierarchy']}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serial", help="target adb serial; required when multiple devices are connected")
    parser.add_argument("--pages", type=int, default=1, help="number of pages to capture, starting at Home (default: 1)")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.pages < 1:
        parser.error("--pages must be at least 1")

    serial = choose_device(args.serial)
    model = str(run_adb(serial, ["shell", "getprop", "ro.product.model"]))
    size = str(run_adb(serial, ["shell", "wm", "size"]))
    stamp = dt.datetime.now().astimezone()
    stem = f"pixel-home-audit-{stamp.strftime('%Y-%m-%d-%H%M%S')}"
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for _ in range(2):
        run_adb(serial, ["shell", "input", "keyevent", "KEYCODE_HOME"])
        time.sleep(1)

    pages = []
    page_signatures: set[str] = set()
    for page_number in range(1, args.pages + 1):
        remote = f"/sdcard/macomrade-home-{page_number}.xml"
        xml_text = capture_xml(serial, remote)
        signature = hashlib.sha256(xml_text.encode()).hexdigest()
        if signature in page_signatures:
            raise RuntimeError(f"page {page_number} duplicates an earlier page; archive not written")
        page_signatures.add(signature)
        page = parse_page(xml_text, page_number)
        xml_name = f"{stem}-page-{page_number:02d}.xml"
        (args.output_dir / xml_name).write_text(xml_text, encoding="utf-8")
        shot_name = f"{stem}-page-{page_number:02d}.png"
        (args.output_dir / shot_name).write_bytes(
            bytes(run_adb(serial, ["exec-out", "screencap", "-p"], binary=True))
        )
        page["screenshot"] = shot_name
        page["ui_hierarchy"] = xml_name
        pages.append(page)
        if page_number < args.pages:
            run_adb(serial, ["shell", "input", "swipe", "900", "1200", "180", "1200", "350"])
            time.sleep(1)
    run_adb(serial, ["shell", "input", "keyevent", "KEYCODE_HOME"])
    folders = capture_folders(serial, pages[0]["hotseat"], args.output_dir, stem)
    run_adb(serial, ["shell", "input", "keyevent", "KEYCODE_HOME"])

    report = {
        "schema": "pixel-home-audit-v1",
        "generated_at": stamp.isoformat(),
        "device": {"serial": serial, "model": model, "display_size": size},
        "evidence_levels": ["ui_confirmed", "visual_confirmed", "inferred", "unavailable"],
        "limitations": ["launcher_db_unavailable_without_root", "widget_configuration_may_be_opaque"],
        "pages": pages,
        "folders": folders,
    }
    json_path = args.output_dir / f"{stem}.json"
    md_path = args.output_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(markdown(report), encoding="utf-8")
    print(f"wrote {json_path} and {md_path} ({len(pages)} page(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
