#!/usr/bin/env python3
"""Repository-local unified CLI for the macOS lifecycle skill."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Sequence


ROOT = Path(__file__).resolve().parents[1]
IDENTITY_PATH = ROOT / "references/cli-identity.json"
VERSION_PATH = ROOT / "VERSION"
REQUIRED_FAMILIES = {
    "scan",
    "plan",
    "apply",
    "verify",
    "drift",
    "diagnostics",
    "migration",
}
RESERVED_FUTURE_COMMANDS = {"mac-buro", "5y-plan"}


@dataclass(frozen=True)
class Route:
    family: str
    target: str
    script: str
    prefix: tuple[str, ...]
    mutating_capable: bool
    description: str

    @property
    def id(self) -> str:
        return f"{self.family}.{self.target}"


ROUTES = (
    Route("scan", "apps", "scripts/macos_apps.py", ("scan",), False, "inventory installed applications"),
    Route("scan", "permissions", "scripts/macos_permissions.py", (), False, "inventory permission prerequisites"),
    Route("scan", "startup", "scripts/macos_startup_items.py", ("scan",), False, "inventory login and startup items"),
    Route("scan", "dock", "scripts/macos_dock.py", (), True, "capture Dock order to machine-local state"),
    Route("scan", "all", "scripts/bootstrap_macos.py", (), False, "run the ordered read-only bootstrap assessment"),
    Route("plan", "apps", "scripts/macos_apps.py", ("plan",), False, "build a capacity-aware application plan"),
    Route("apply", "apps", "scripts/macos_apps.py", ("install",), True, "dry-run or explicitly apply an application plan"),
    Route("apply", "preferences", "scripts/macos_preferences.py", (), True, "dry-run or explicitly apply tracked preferences"),
    Route("verify", "baseline", "scripts/bootstrap_verify.py", (), False, "run final baseline read-back"),
    Route("verify", "release", "scripts/release_check.py", (), False, "run the local release gate"),
    Route("verify", "clean-mac", "scripts/clean_mac_acceptance.py", ("validate",), False, "validate the Clean-Mac harness"),
    Route("verify", "supply-chain", "scripts/supply_chain.py", ("validate",), False, "validate installation-source policy"),
    Route("drift", "baseline", "scripts/bootstrap_verify.py", (), False, "compare current Mac with the baseline"),
    Route("drift", "supply-chain", "scripts/supply_chain.py", ("inspect",), False, "inspect source and package-manager drift"),
    Route("diagnostics", "release", "scripts/release_check.py", (), False, "run deterministic release diagnostics"),
    Route("diagnostics", "permissions", "scripts/macos_permissions.py", (), False, "record permission diagnostics"),
    Route("diagnostics", "supply-chain", "scripts/supply_chain.py", ("inspect",), False, "inspect source diagnostics"),
    Route("diagnostics", "state", "scripts/state_paths.py", ("info",), False, "explain machine-local state resolution"),
    Route("diagnostics", "clean-mac", "scripts/clean_mac_acceptance.py", ("status",), False, "show Clean-Mac acceptance status"),
    Route("migration", "state", "scripts/migrate_state.py", (), True, "inspect, materialize, migrate, or clean legacy state"),
)


def load_identity(path: Path = IDENTITY_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def version(path: Path = VERSION_PATH) -> str:
    return path.read_text(encoding="utf-8").strip()


def route_index() -> dict[tuple[str, str], Route]:
    return {(route.family, route.target): route for route in ROUTES}


def command_for(
    route: Route,
    passthrough: Sequence[str],
    *,
    python: str = sys.executable,
) -> list[str]:
    return [python, route.script, *route.prefix, *passthrough]


def route_rows(*, python: str = sys.executable) -> list[dict]:
    rows = []
    for route in ROUTES:
        row = asdict(route)
        row["id"] = route.id
        row["prefix"] = list(route.prefix)
        row["compatibility_command"] = command_for(route, [], python=python)
        rows.append(row)
    return rows


def validate_contract(root: Path = ROOT) -> dict:
    errors: list[str] = []
    try:
        identity = load_identity(root / "references/cli-identity.json")
    except (OSError, json.JSONDecodeError) as exc:
        identity = {}
        errors.append(f"cannot read CLI identity: {exc}")

    if identity.get("schema_version") != 1:
        errors.append("CLI identity schema_version must be 1")
    if identity.get("cli_name") != "macomrade":
        errors.append("CLI identity cli_name must be macomrade")
    if identity.get("status") != "repository_local":
        errors.append("CLI identity status must be repository_local")
    if identity.get("product_name_status") != "undecided":
        errors.append("product name must remain undecided")
    reserved = identity.get("reserved_future_commands", [])
    reserved_names = {
        row.get("name")
        for row in reserved
        if isinstance(row, dict) and row.get("status") == "reserved_unimplemented"
    }
    if reserved_names != RESERVED_FUTURE_COMMANDS:
        errors.append("reserved future commands must be exactly mac-buro and 5y-plan")

    keys = [(route.family, route.target) for route in ROUTES]
    if len(keys) != len(set(keys)):
        errors.append("route family/target pairs must be unique")
    families = {route.family for route in ROUTES}
    missing_families = sorted(REQUIRED_FAMILIES - families)
    if missing_families:
        errors.append(f"missing command families: {', '.join(missing_families)}")

    root_resolved = root.resolve()
    for route in ROUTES:
        path = (root / route.script).resolve()
        if path.parent != (root_resolved / "scripts"):
            errors.append(f"{route.id}: target must remain directly under scripts/")
        if not path.is_file():
            errors.append(f"{route.id}: target script not found: {route.script}")

    launcher = root / "bin/macomrade"
    if not launcher.is_file():
        errors.append("repository-local launcher not found: bin/macomrade")
    elif not os.access(launcher, os.X_OK):
        errors.append("repository-local launcher is not executable: bin/macomrade")
    for command in RESERVED_FUTURE_COMMANDS:
        if (root / "bin" / command).exists():
            errors.append(f"reserved future command must not be executable yet: {command}")

    try:
        current_version = version(root / "VERSION")
    except OSError as exc:
        current_version = ""
        errors.append(f"cannot read VERSION: {exc}")
    if not current_version:
        errors.append("VERSION must not be empty")

    return {
        "schema_version": 1,
        "status": "passed" if not errors else "failed",
        "cli_name": identity.get("cli_name"),
        "version": current_version,
        "route_count": len(ROUTES),
        "families": sorted(families),
        "compatibility": "legacy scripts retained",
        "reserved_future_commands": sorted(RESERVED_FUTURE_COMMANDS),
        "errors": errors,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="macomrade", description=__doc__)
    parser.add_argument("--version", action="version", version=f"%(prog)s {version()}")
    parser.add_argument(
        "--explain",
        action="store_true",
        help="print the resolved compatibility command without executing it",
    )
    subparsers = parser.add_subparsers(dest="family", required=True)

    routes_parser = subparsers.add_parser("routes", help="list stable routes")
    routes_parser.add_argument("--json", action="store_true")
    validate_parser = subparsers.add_parser("validate", help="validate the CLI contract")
    validate_parser.add_argument("--json", action="store_true")

    by_family: dict[str, list[Route]] = {}
    for route in ROUTES:
        by_family.setdefault(route.family, []).append(route)
    for family in sorted(by_family):
        family_parser = subparsers.add_parser(family)
        family_parser.add_argument(
            "target",
            choices=sorted(route.target for route in by_family[family]),
        )
        family_parser.add_argument(
            "passthrough",
            nargs=argparse.REMAINDER,
            help="arguments passed unchanged to the compatibility script",
        )
    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    runner: Callable[..., subprocess.CompletedProcess] = subprocess.run,
) -> int:
    args = build_parser().parse_args(argv)
    if args.family == "routes":
        rows = route_rows()
        if args.json:
            print(json.dumps({"schema_version": 1, "routes": rows}, ensure_ascii=False, indent=2))
        else:
            for row in rows:
                mutation = "mutation-capable" if row["mutating_capable"] else "read-only"
                print(f"{row['id']:<28} {mutation:<16} {row['description']}")
        return 0
    if args.family == "validate":
        result = validate_contract()
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"{result['status']}: {result['cli_name']} {result['version']} ({result['route_count']} routes)")
            for error in result["errors"]:
                print(f"- {error}", file=sys.stderr)
        return 0 if result["status"] == "passed" else 1

    route = route_index()[(args.family, args.target)]
    command = command_for(route, args.passthrough)
    if args.explain:
        print(shlex.join(command))
        return 0
    completed = runner(command, cwd=ROOT, check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
