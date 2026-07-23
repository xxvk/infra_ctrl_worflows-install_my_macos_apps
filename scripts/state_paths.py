#!/usr/bin/env python3
"""Resolve the machine-local runtime state directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
from pathlib import Path
from typing import Mapping


STATE_DIR_ENV = "INSTALL_MY_MACOS_APPS_STATE_DIR"
PRODUCT_STATE_RELATIVE = Path("Library/Application Support/install-macos-apps/state")


def _platform_identity() -> str:
    result = subprocess.run(
        ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        match = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', result.stdout)
        if match:
            return match.group(1)
    return platform.node() or f"uid-{os.getuid()}"


def machine_id(*, raw_identity: str | None = None) -> str:
    """Return a stable, non-reversible short machine scope."""
    identity = raw_identity or _platform_identity()
    return f"mac-{hashlib.sha256(identity.encode('utf-8')).hexdigest()[:12]}"


def resolve_state_dir(
    explicit: Path | str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
    machine_id: str | None = None,
) -> Path:
    """Resolve CLI override, then environment override, then machine default."""
    environment = os.environ if environ is None else environ
    selected = explicit or environment.get(STATE_DIR_ENV)
    if selected:
        return Path(selected).expanduser().resolve()
    home_path = Path.home() if home is None else home
    return home_path / PRODUCT_STATE_RELATIVE / (machine_id or globals()["machine_id"]())


def add_state_dir_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--state-dir",
        type=Path,
        help=f"machine-local state directory; overrides ${STATE_DIR_ENV}",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["path", "info"], nargs="?", default="path")
    add_state_dir_argument(parser)
    args = parser.parse_args()
    path = resolve_state_dir(args.state_dir)
    if args.command == "path":
        print(path)
    else:
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "state_dir": str(path),
                    "environment_override": STATE_DIR_ENV,
                    "source": (
                        "cli"
                        if args.state_dir
                        else "environment"
                        if os.environ.get(STATE_DIR_ENV)
                        else "machine_default"
                    ),
                    "machine_scoped": not bool(args.state_dir or os.environ.get(STATE_DIR_ENV)),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
