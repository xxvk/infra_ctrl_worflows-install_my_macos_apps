#!/usr/bin/env python3
"""Read pnpm global state under one fnm-managed Node runtime."""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Callable


RUNTIME = re.compile(r"^\d+$")


def runtime_environment(
    runtime: str,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, str]:
    """Bind pnpm's global binary directory to the selected fnm runtime."""
    if not RUNTIME.fullmatch(runtime):
        raise ValueError("pnpm runtime must be a numeric Node major")
    result = runner(
        ["fnm", "exec", f"--using={runtime}", "npm", "prefix", "--global"],
        capture_output=True,
        text=True,
        check=False,
    )
    prefix = result.stdout.strip()
    if result.returncode != 0 or not prefix:
        raise RuntimeError(f"unable to resolve fnm Node {runtime} global prefix")
    env = os.environ.copy()
    # pnpm 11 derives its global bin path as $PNPM_HOME/bin. Pointing this at
    # the prefix's bin directory would incorrectly produce a bin/bin path.
    env["PNPM_HOME"] = str(Path(prefix))
    return env


def parse_global_listing(payload: Any) -> dict[str, str]:
    """Normalize pnpm list --global --json across object and array shapes."""
    rows = payload if isinstance(payload, list) else [payload]
    packages: dict[str, str] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        for group in ("dependencies", "devDependencies", "optionalDependencies"):
            values = row.get(group, {})
            if not isinstance(values, dict):
                continue
            for name, metadata in values.items():
                if isinstance(metadata, dict) and metadata.get("version"):
                    packages[str(name)] = str(metadata["version"])
    return packages


def global_packages(
    runtime: str,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, str]:
    env = runtime_environment(runtime, runner=runner)
    result = runner(
        [
            "fnm", "exec", f"--using={runtime}", "pnpm", "list", "--global",
            "--depth=0", "--json",
        ],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    if result.returncode != 0:
        return {}
    try:
        return parse_global_listing(json.loads(result.stdout))
    except json.JSONDecodeError:
        return {}


def package_present(runtime: str, package: str, version: str) -> bool:
    return global_packages(runtime).get(package) == version


def package_root(
    runtime: str,
    package: str,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> Path | None:
    env = runtime_environment(runtime, runner=runner)
    result = runner(
        ["fnm", "exec", f"--using={runtime}", "pnpm", "root", "--global"],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    return Path(result.stdout.strip()) / package if result.returncode == 0 else None
