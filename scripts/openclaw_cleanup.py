#!/usr/bin/env python3
"""Inspect and explicitly remove standalone OpenClaw leftovers."""
from __future__ import annotations
import argparse, json, shutil, subprocess
from pathlib import Path

HOME = Path.home()
KNOWN_PATHS = (HOME / ".openclaw", HOME / "Library/Application Support/kimi-desktop/daimon-share/daimon/openclaw-shim")

def size_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(item.stat().st_size for item in path.rglob("*") if item.is_file())

def discover() -> dict[str, object]:
    command = shutil.which("openclaw")
    brew_items: list[str] = []
    if brew := shutil.which("brew"):
        for scope in ("formula", "cask"):
            result = subprocess.run([brew, "list", f"--{scope}"], capture_output=True, text=True)
            brew_items += [line for line in result.stdout.splitlines() if "openclaw" in line.lower()]
    npm_items: list[str] = []
    if npm := shutil.which("npm"):
        result = subprocess.run([npm, "list", "-g", "--depth=0", "--json"], capture_output=True, text=True)
        try:
            npm_items = [name for name in json.loads(result.stdout).get("dependencies", {}) if "openclaw" in name.lower()]
        except (json.JSONDecodeError, AttributeError):
            pass
    paths = [{"path": str(path), "exists": path.exists(), "size_bytes": size_bytes(path) if path.exists() else 0} for path in KNOWN_PATHS]
    return {"command": command, "brew": brew_items, "npm": npm_items, "paths": paths}

def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect or remove standalone OpenClaw leftovers")
    sub = parser.add_subparsers(dest="action", required=True)
    sub.add_parser("inspect")
    remove = sub.add_parser("remove")
    remove.add_argument("--confirm", required=True)
    args = parser.parse_args()
    state = discover()
    if args.action == "inspect":
        print(json.dumps(state, indent=2, ensure_ascii=False))
        return 0
    if args.confirm != "REMOVE OPENCLAW":
        raise SystemExit("Confirmation token must be exactly: REMOVE OPENCLAW")
    removed = []
    for item in state["paths"]:
        if item["exists"]:
            shutil.rmtree(item["path"], ignore_errors=True)
            removed.append(item["path"])
    print(json.dumps({"removed": removed, "preserved": ["Hermes project files", "Kimi Desktop application and other data"]}, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
