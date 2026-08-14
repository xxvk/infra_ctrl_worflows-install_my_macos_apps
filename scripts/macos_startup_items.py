#!/usr/bin/env python3
# Mutation action ID: startup-items.disable
"""Scan and selectively disable macOS user login items and startup agents.

The scan is intentionally broader than the removal operation: Background Task
Management entries are reported for visibility, while changes are limited to
the current user's Login Items and ~/Library/LaunchAgents.
"""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import shutil
import subprocess
from pathlib import Path
from xml.parsers.expat import ExpatError


HOME = Path.home()
USER_AGENTS = HOME / "Library/LaunchAgents"


def run(command: list[str], *, timeout: int = 30) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, capture_output=True, text=True, check=False, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(command, 124, exc.stdout or "", f"timed out after {timeout}s")


def login_items() -> list[dict[str, object]]:
    script = 'tell application "System Events" to get name of every login item'
    result = run(["osascript", "-e", script])
    if result.returncode != 0:
        return [{"kind": "login_item", "name": "<unavailable>", "error": result.stderr.strip()}]
    names = [item.strip() for item in result.stdout.strip().split(",") if item.strip()]
    return [
        {"kind": "login_item", "name": name, "removable": True}
        for name in names
    ]


def launch_agents() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    if not USER_AGENTS.exists():
        return rows
    for path in sorted(USER_AGENTS.glob("*.plist")):
        try:
            with path.open("rb") as stream:
                data = plistlib.load(stream)
        except (OSError, plistlib.InvalidFileException, ExpatError, ValueError) as error:
            rows.append({
                "kind": "launch_agent",
                "id": f"agent:{path.name}",
                "name": path.stem,
                "path": str(path),
                "parse_error": str(error),
                "removable": False,
                "action": "review_manually",
            })
            continue
        label = str(data.get("Label") or path.stem)
        arguments = data.get("ProgramArguments") or []
        program = data.get("Program") or (arguments[0] if arguments else None)
        rows.append({
            "kind": "launch_agent",
            "id": f"agent:{path.name}",
            "name": label,
            "path": str(path),
            "program": program,
            "run_at_load": bool(data.get("RunAtLoad", False)),
            "keep_alive": bool(data.get("KeepAlive", False)),
            "removable": True,
        })
    return rows


def background_tasks() -> list[dict[str, object]]:
    tool = shutil.which("sfltool")
    if not tool:
        return []
    result = run([tool, "dumpbtm"])
    if result.returncode != 0:
        return [{
            "kind": "background_task",
            "name": "<unavailable>",
            "error": result.stderr.strip() or f"sfltool exited {result.returncode}",
            "removable": False,
            "action": "retry_or_review_system_settings",
        }]
    rows: list[dict[str, object]] = []
    block: dict[str, str] = {}

    def flush() -> None:
        if block.get("Name") and block.get("Identifier"):
            rows.append({
                "kind": "background_task",
                "name": block["Name"],
                "identifier": block["Identifier"],
                "bundle_identifier": block.get("Bundle Identifier"),
                "url": block.get("URL"),
                "disposition": block.get("Disposition"),
                "removable": False,
                "action": "review_via_login_items_or_vendor_settings",
            })

    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()
        if line.startswith("#") and line.rstrip(":").lstrip("#").strip().isdigit() and block:
            flush()
            block = {}
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key in {"Name", "Identifier", "Bundle Identifier", "URL", "Disposition"}:
            block[key] = value.strip()
    flush()
    return rows


def scan() -> list[dict[str, object]]:
    return login_items() + launch_agents() + background_tasks()


def remove_login_item(name: str) -> None:
    escaped = name.replace('\\', '\\\\').replace('"', '\\"')
    script = f'tell application "System Events" to delete login item "{escaped}"'
    result = run(["osascript", "-e", script])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"unable to remove login item: {name}")


def disable_agent(row: dict[str, object]) -> str:
    path = Path(str(row["path"]))
    if path.parent != USER_AGENTS or path.suffix != ".plist":
        raise RuntimeError(f"refusing to modify unexpected path: {path}")
    label = str(row["name"])
    run(["launchctl", "bootout", f"gui/{os.getuid()}/{label}"])
    disabled = path.with_name(path.name + ".disabled")
    path.rename(disabled)
    return str(disabled)


def print_rows(rows: list[dict[str, object]]) -> None:
    for index, row in enumerate(rows, start=1):
        kind = str(row.get("kind"))
        name = str(row.get("name"))
        detail = row.get("path") or row.get("bundle_identifier") or row.get("identifier") or ""
        action = "disable" if row.get("removable") else "report-only"
        print(f"[{index}] {kind}: {name} | {detail} | {action}")


def interactive_review() -> int:
    rows = scan()
    if not rows:
        print("No startup items or background tasks found.")
        return 0
    print_rows(rows)
    answer = input("Enter numbers to disable, separated by commas (blank cancels): ").strip()
    if not answer:
        print("Cancelled; no changes made.")
        return 0
    try:
        selected = [rows[int(value) - 1] for value in answer.split(",")]
    except (ValueError, IndexError):
        raise SystemExit("Invalid selection.")
    blocked = [row for row in selected if not row.get("removable")]
    if blocked:
        names = ", ".join(str(row.get("name")) for row in blocked)
        raise SystemExit(f"Report-only entries cannot be disabled automatically: {names}")
    print("Selected: " + ", ".join(str(row.get("name")) for row in selected))
    if input("Type DISABLE to confirm: ").strip() != "DISABLE":
        print("Cancelled; no changes made.")
        return 0
    changed = []
    for row in selected:
        if row["kind"] == "login_item":
            remove_login_item(str(row["name"]))
            changed.append(str(row["name"]))
        elif row["kind"] == "launch_agent":
            changed.append(disable_agent(row))
    print(json.dumps({"action_id": "startup-items.disable", "disabled": changed, "data_preserved": True}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan and selectively disable macOS startup items")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("scan", help="print login items, user LaunchAgents, and background tasks as JSON")
    sub.add_parser("review", help="show a numbered list and interactively disable selected items")
    args = parser.parse_args()
    if args.action == "scan":
        print(json.dumps(scan(), ensure_ascii=False, indent=2))
        return 0
    return interactive_review()


if __name__ == "__main__":
    raise SystemExit(main())
