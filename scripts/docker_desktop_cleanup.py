#!/usr/bin/env python3
"""Inspect and, with an explicit confirmation token, remove Docker Desktop data only."""
import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HOME = Path.home()
APP = Path("/Applications/Docker.app")
# These are Docker Desktop-owned macOS locations. Do not add ~/.docker: OrbStack
# and other Docker backends may use it for contexts and credentials.
TARGETS = [
    APP,
    HOME / "Library/Containers/com.docker.docker",
    HOME / "Library/Group Containers/group.com.docker",
    HOME / "Library/Application Support/Docker Desktop",
    HOME / "Library/Logs/Docker Desktop",
    HOME / "Library/Preferences/com.docker.docker.plist",
    HOME / "Library/Saved Application State/com.electron.docker-frontend.savedState",
]


def command_output(command):
    try:
        return subprocess.run(command, capture_output=True, text=True, check=True, timeout=15).stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return None


def executable(name, extra_paths=()):
    """Resolve a tool on PATH or at an explicitly known vendor path."""
    found = shutil.which(name)
    if found:
        return found
    for path in extra_paths:
        candidate = Path(path).expanduser()
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return None


def size_bytes(path):
    if not path.exists():
        return 0
    try:
        result = subprocess.run(["du", "-sk", str(path)], capture_output=True, text=True, check=True)
        return int(result.stdout.split()[0]) * 1024
    except (subprocess.CalledProcessError, ValueError, IndexError):
        return None


def inspect():
    entries = []
    for path in TARGETS:
        if path.exists():
            entries.append({"path": str(path), "size_bytes": size_bytes(path)})
    orbctl = executable("orbctl", ["/opt/homebrew/bin/orbctl", "/usr/local/bin/orbctl", "~/.orbstack/bin/orbctl"])
    orb_status = command_output([orbctl, "status"]) if orbctl else None
    docker_cli_on_path = shutil.which("docker")
    docker_cli_login_shell = command_output(["zsh", "-lc", "command -v docker"])
    docker_cli = docker_cli_on_path or docker_cli_login_shell
    orbstack_docker = executable("docker", ["~/.orbstack/bin/docker"])
    docker_context = command_output([docker_cli, "context", "show"]) if docker_cli else None
    docker_server = (
        command_output([docker_cli, "version", "--format", "{{.Server.Version}}"]) if docker_cli else None
    )
    return {
        "generated_at": dt.datetime.now().astimezone().isoformat(),
        "docker_desktop_installed": APP.exists(),
        "orbstack_installed": Path("/Applications/OrbStack.app").exists(),
        "orbstack_status": orb_status,
        "orbstack_cli_path": orbctl,
        "orbstack_docker_cli_path": orbstack_docker,
        "docker_cli_path": docker_cli,
        "docker_cli_login_shell_path": docker_cli_login_shell,
        "docker_context": docker_context,
        "docker_server_version": docker_server,
        "orbstack_docker_ready": bool(
            Path("/Applications/OrbStack.app").exists()
            and orb_status == "Running"
            and docker_cli
            and docker_context == "orbstack"
            and docker_server
        ),
        "targets": entries,
        "total_target_bytes": sum(item["size_bytes"] or 0 for item in entries),
        "preserved": [str(HOME / ".docker"), "/Applications/OrbStack.app"],
        "warning": "Removal permanently deletes Docker Desktop-local containers, images, volumes, build cache, Kubernetes data, and settings.",
        "cli_note": "If docker_cli_path is null, add ~/.orbstack/bin to PATH after user confirmation, then open a new shell and inspect again."
    }


def command_inspect(_args):
    print(json.dumps(inspect(), ensure_ascii=False, indent=2))


def command_remove(args):
    if args.confirm != "REMOVE DOCKER DESKTOP DATA":
        raise SystemExit('Confirmation token must be exactly: REMOVE DOCKER DESKTOP DATA')
    report = inspect()
    if not report["orbstack_installed"]:
        raise SystemExit("OrbStack is not installed; stop before retiring Docker Desktop.")
    if APP.exists():
        uninstaller = APP / "Contents/MacOS/uninstall"
        if not uninstaller.exists():
            raise SystemExit(f"Official uninstaller missing: {uninstaller}")
        result = subprocess.run([str(uninstaller)])
        if result.returncode:
            raise SystemExit(
                "Docker Desktop's official uninstaller stopped with an error. "
                "Run inspect to assess any partial cleanup; do not force-delete residual paths."
            )
    for path in TARGETS[1:]:
        if path.exists():
            if path.is_dir() and not path.is_symlink():
                shutil.rmtree(path)
            else:
                path.unlink()
    print(json.dumps({"removed_at": dt.datetime.now().astimezone().isoformat(), "preflight": report, "postflight": inspect()}, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(required=True)
    inspect_parser = actions.add_parser("inspect", help="Report Docker Desktop-only paths and their disk use")
    inspect_parser.set_defaults(func=command_inspect)
    remove_parser = actions.add_parser("remove", help="Permanently remove Docker Desktop after confirmation")
    remove_parser.add_argument("--confirm", required=True, help='Exact token: REMOVE DOCKER DESKTOP DATA')
    remove_parser.set_defaults(func=command_remove)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
