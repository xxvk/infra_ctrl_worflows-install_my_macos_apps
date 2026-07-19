#!/usr/bin/env python3
"""Read-only inventory of everything this skill has installed outside the repo.

Unlike the app catalog (which tracks apps this skill helps install), this
lists the skill's *own* footprint on the machine: LaunchAgents, binaries,
logs, and dotfiles symlinks it created. Companion to
scripts/skill_uninstall.py, which acts on this inventory. Never deletes
anything itself.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

HOME = Path.home()
SKILL_ROOT = Path(__file__).resolve().parents[1]

KNOWN_LAUNCH_AGENTS = [
    "com.xvk.install-my-macos-apps.keyboard-config-logi-k240",
    "com.xvk.install-my-macos-apps.drift-check",
]

KNOWN_SUPPORT_PATHS = [
    HOME / "Library/Application Support/install_my_macos_apps",
]

KNOWN_LOG_PATHS = [
    HOME / "Library/Logs/install_my_macos_apps",
]


def _du_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    result = subprocess.run(["du", "-sk", str(path)], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return 0
    try:
        return int(result.stdout.split()[0]) * 1024
    except (IndexError, ValueError):
        return 0


def launch_agents() -> list[dict[str, object]]:
    rows = []
    for label in KNOWN_LAUNCH_AGENTS:
        plist = HOME / f"Library/LaunchAgents/{label}.plist"
        disabled = HOME / f"Library/LaunchAgents/{label}.plist.disabled"
        loaded = subprocess.run(
            ["launchctl", "print", f"gui/{os.getuid()}/{label}"],
            capture_output=True, text=True, check=False,
        ).returncode == 0
        rows.append({
            "label": label,
            "plist_path": str(plist),
            "installed": plist.is_file(),
            "disabled_backup_present": disabled.is_file(),
            "loaded": loaded,
        })
    return rows


def support_and_logs() -> list[dict[str, object]]:
    rows = []
    for path in KNOWN_SUPPORT_PATHS + KNOWN_LOG_PATHS:
        rows.append({
            "path": str(path),
            "exists": path.exists(),
            "size_bytes": _du_bytes(path),
        })
    return rows


def dotfiles_symlinks() -> list[dict[str, object]]:
    dotfiles_home = SKILL_ROOT / "dotfiles/home"
    if not dotfiles_home.is_dir():
        return []
    rows = []
    for tracked in sorted(p for p in dotfiles_home.rglob("*") if p.is_file()):
        relative = tracked.relative_to(dotfiles_home)
        destination = HOME / relative
        rows.append({
            "relative_path": str(relative),
            "destination": str(destination),
            "is_symlink_to_tracked": destination.is_symlink() and destination.resolve() == tracked.resolve(),
        })
    return rows


def inventory() -> dict[str, object]:
    return {
        "launch_agents": launch_agents(),
        "support_and_log_paths": support_and_logs(),
        "dotfiles_symlinks": dotfiles_symlinks(),
        "note": "This is the skill's own installed footprint, not the app catalog it manages.",
    }


def main() -> int:
    print(json.dumps(inventory(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
