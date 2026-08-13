#!/usr/bin/env python3
"""Resolve composable machine roles into explainable app selections."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from config_layers import load_app_catalog
from schema_contract import SchemaContractError, load_and_validate


ROOT = Path(__file__).resolve().parents[1]
ROLE_PATH = ROOT / "settings" / "machine-roles.json"


class MachineRoleError(RuntimeError):
    """Raised when a role definition or selection is ambiguous or unsafe."""


def load_roles(path: Path = ROLE_PATH) -> dict[str, Any]:
    try:
        return load_and_validate(path, "machine-role-catalog")
    except SchemaContractError as exc:
        raise MachineRoleError(str(exc)) from exc


def validate_catalog(role_catalog: dict[str, Any], app_catalog: dict[str, Any]) -> None:
    if role_catalog.get("kind") != "machine_role_catalog":
        raise MachineRoleError("machine role catalog kind is invalid")
    roles = role_catalog.get("roles")
    if not isinstance(roles, dict) or not roles:
        raise MachineRoleError("machine role catalog has no roles")
    base_role = role_catalog.get("base_role")
    if base_role not in roles:
        raise MachineRoleError("base_role is not declared")
    app_names = {
        app.get("name")
        for app in app_catalog.get("apps", [])
        if isinstance(app, dict) and isinstance(app.get("name"), str)
    }
    for role_id, role in roles.items():
        for parent in role.get("inherits", []):
            if parent not in roles:
                raise MachineRoleError(f"{role_id} inherits unknown role: {parent}")
        for app_name in [*role.get("include_apps", []), *role.get("exclude_apps", [])]:
            if app_name not in app_names:
                raise MachineRoleError(f"{role_id} references unknown catalog app: {app_name}")

    visiting, visited = set(), set()

    def visit(role_id: str) -> None:
        if role_id in visiting:
            raise MachineRoleError(f"role inheritance cycle includes: {role_id}")
        if role_id in visited:
            return
        visiting.add(role_id)
        for parent in roles[role_id]["inherits"]:
            visit(parent)
        visiting.remove(role_id)
        visited.add(role_id)

    for role_id in roles:
        visit(role_id)


def _expand_requested(role_catalog: dict[str, Any], requested: list[str], storage_gb: float) -> list[str]:
    roles = role_catalog["roles"]
    expanded = []
    for role_id in requested or ["auto"]:
        if role_id == "auto":
            expanded.append("expanded" if storage_gb >= 512 else "compact")
            continue
        if role_id not in roles:
            raise MachineRoleError(f"unknown role: {role_id}")
        expanded.append(role_id)
    return expanded


def resolve(
    role_catalog: dict[str, Any],
    app_catalog: dict[str, Any],
    requested: list[str],
    *,
    storage_gb: float,
    include_apps: list[str] | None = None,
    exclude_apps: list[str] | None = None,
) -> dict[str, Any]:
    validate_catalog(role_catalog, app_catalog)
    roles = role_catalog["roles"]
    expanded = _expand_requested(role_catalog, requested, storage_gb)
    ordered_roles: list[str] = []

    def add(role_id: str) -> None:
        for parent in roles[role_id]["inherits"]:
            add(parent)
        if role_id not in ordered_roles:
            ordered_roles.append(role_id)

    add(role_catalog["base_role"])
    for role_id in expanded:
        add(role_id)

    app_order = [
        app["name"]
        for app in app_catalog.get("apps", [])
        if app.get("lifecycle_status") != "retired"
    ]
    known = set(app_order)
    includes: dict[str, list[str]] = {}
    excluded: set[str] = set()
    for app in app_catalog.get("apps", []):
        if app.get("lifecycle_status") != "retired" and app.get("tier") == "core":
            includes.setdefault(app["name"], []).append(role_catalog["base_role"])
    for role_id in ordered_roles:
        for app_name in roles[role_id]["include_apps"]:
            includes.setdefault(app_name, []).append(role_id)
        excluded.update(roles[role_id]["exclude_apps"])
    for app_name in include_apps or []:
        if app_name not in known:
            raise MachineRoleError(f"explicit include references unknown catalog app: {app_name}")
        includes.setdefault(app_name, []).append("explicit_include")
    for app_name in exclude_apps or []:
        if app_name not in known:
            raise MachineRoleError(f"explicit exclude references unknown catalog app: {app_name}")
        excluded.add(app_name)

    selected_apps = [app_name for app_name in app_order if app_name in includes and app_name not in excluded]
    return {
        "schema_version": 1,
        "kind": "machine_role_selection",
        "roles": ordered_roles,
        "requested_roles": requested or ["auto"],
        "storage_gb": storage_gb,
        "selected_apps": selected_apps,
        "excluded_apps": sorted(excluded),
        "reasons": {app_name: includes[app_name] for app_name in selected_apps},
    }


def validate() -> dict[str, Any]:
    try:
        role_catalog = load_roles()
        validate_catalog(role_catalog, load_app_catalog())
    except (MachineRoleError, Exception) as exc:
        return {"schema_version": 1, "status": "failed", "errors": [str(exc)]}
    return {
        "schema_version": 1,
        "status": "passed",
        "roles": sorted(role_catalog["roles"]),
        "base_role": role_catalog["base_role"],
        "errors": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate role definitions")
    explain_parser = subparsers.add_parser("explain", help="resolve roles into an app selection")
    explain_parser.add_argument("--roles", default="auto")
    explain_parser.add_argument("--storage-gb", type=float, required=True)
    explain_parser.add_argument("--include-app", action="append", default=[])
    explain_parser.add_argument("--exclude-app", action="append", default=[])
    args = parser.parse_args()
    if args.command == "validate":
        result = validate()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "passed" else 1
    try:
        result = resolve(
            load_roles(),
            load_app_catalog(),
            [item for item in args.roles.split(",") if item],
            storage_gb=args.storage_gb,
            include_apps=args.include_app,
            exclude_apps=args.exclude_app,
        )
    except MachineRoleError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
