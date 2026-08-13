#!/usr/bin/env python3
"""Safe, metadata-only SDK for application lifecycle adapters.

This first SDK exposes WeChat as an inspect/classify/manual-handoff adapter and
Claude VM as an inspect/plan adapter. It deliberately has no generic apply
command: existing application-specific transaction owners remain the only
authority for destructive actions.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
from typing import Any

import claude_vm_cleanup
import localization
from config_layers import load_app_catalog
from schema_contract import SchemaContractError, load_and_validate
from state_paths import resolve_state_dir


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "settings" / "app-adapters.json"


class AdapterError(RuntimeError):
    """Raised when an adapter contract cannot be safely executed."""


def load_catalog(path: Path = CATALOG_PATH) -> dict[str, Any]:
    try:
        return load_and_validate(path, "app-adapter-catalog")
    except SchemaContractError as exc:
        raise AdapterError(str(exc)) from exc


def adapter_for(adapter_id: str, catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    catalog = catalog or load_catalog()
    matches = [item for item in catalog["adapters"] if item["id"] == adapter_id]
    if len(matches) != 1:
        raise AdapterError(f"unknown adapter: {adapter_id}")
    return matches[0]


def validate_catalog(catalog: dict[str, Any], app_catalog: dict[str, Any]) -> None:
    if catalog.get("kind") != "app_adapter_catalog":
        raise AdapterError("app adapter catalog kind is invalid")
    adapters = catalog.get("adapters")
    if not isinstance(adapters, list) or not adapters:
        raise AdapterError("app adapter catalog has no adapters")
    component_ids = {
        (ROOT / app["guide"]).stem
        for app in app_catalog.get("apps", [])
        if isinstance(app, dict) and isinstance(app.get("guide"), str)
    }
    message_keys = set(localization.load_catalogs()["en"]["messages"])
    seen = set()
    for adapter in adapters:
        adapter_id = adapter["id"]
        if adapter_id in seen:
            raise AdapterError(f"duplicate adapter id: {adapter_id}")
        seen.add(adapter_id)
        if adapter["component_id"] not in component_ids:
            raise AdapterError(f"{adapter_id} references unknown component: {adapter['component_id']}")
        for key in [adapter["name_key"], adapter["summary_key"], *[item["description_key"] for item in adapter["data_classes"]], *[item["description_key"] for item in adapter["operations"]]]:
            if key not in message_keys:
                raise AdapterError(f"{adapter_id} references unknown message key: {key}")
        for root in adapter["known_roots"]:
            relative = root["relative_path"]
            if relative.startswith("/") or ".." in Path(relative).parts:
                raise AdapterError(f"{adapter_id} root escapes home: {relative}")
        for operation in adapter["operations"]:
            action_id = operation.get("action_id")
            if operation["automatable"]:
                raise AdapterError(f"{adapter_id} operations must not be generically automatable")
            if action_id and operation.get("confirmation_mode") != "exact":
                raise AdapterError(f"{adapter_id} transaction handoff must require exact confirmation")


def validate() -> dict[str, Any]:
    try:
        catalog = load_catalog()
        validate_catalog(catalog, load_app_catalog())
    except (AdapterError, Exception) as exc:
        return {"schema_version": 1, "status": "failed", "errors": [str(exc)]}
    return {
        "schema_version": 1,
        "status": "passed",
        "adapter_ids": sorted(adapter["id"] for adapter in catalog["adapters"]),
        "generic_apply": "unsupported",
        "errors": [],
    }


def _allocated_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    try:
        total += path.stat(follow_symlinks=False).st_blocks * 512
    except OSError:
        return 0
    for parent, directories, files in os.walk(path, followlinks=False):
        directories[:] = [item for item in directories if not (Path(parent) / item).is_symlink()]
        for name in files:
            try:
                total += (Path(parent) / name).stat(follow_symlinks=False).st_blocks * 512
            except OSError:
                continue
    return total


def _redact_home(value: str, home: Path) -> str:
    value = str(value)
    try:
        relative = Path(value).resolve().relative_to(home.resolve())
        return str(Path("~") / relative)
    except (OSError, ValueError):
        return "<external-path>"


def _wechat_inspection(adapter: dict[str, Any], home: Path) -> dict[str, Any]:
    roots = []
    for root in adapter["known_roots"]:
        path = home / root["relative_path"]
        roots.append(
            {
                "relative_path": root["relative_path"],
                "data_class": root["data_class"],
                "exists": path.exists(),
                "allocated_bytes": _allocated_bytes(path),
                "disposition": "manual_review",
            }
        )
    return {
        "privacy_boundary": "metadata_only",
        "roots": roots,
        "classes": [
            {
                "id": item["id"],
                "disposition": item["disposition"],
                "description_key": item["description_key"],
            }
            for item in adapter["data_classes"]
        ],
    }


def _claude_inspection(adapter: dict[str, Any], home: Path) -> dict[str, Any]:
    raw = claude_vm_cleanup.report()
    return {
        "privacy_boundary": "metadata_only",
        "roots": [
            {
                "relative_path": adapter["known_roots"][0]["relative_path"],
                "data_class": "vm-bundle",
                "exists": bool(raw.get("vm_bundle_exists")),
                "allocated_bytes": int(raw.get("vm_bundle_bytes") or 0),
                "disposition": "manual_review",
            }
        ],
        "vm_bundle_exists": bool(raw.get("vm_bundle_exists")),
        "vm_bundle_bytes": int(raw.get("vm_bundle_bytes") or 0),
        "images": [
            {
                "name": Path(str(item.get("path", "unknown"))).name,
                "exists": bool(item.get("exists")),
                "bytes": int(item.get("bytes") or 0),
            }
            for item in raw.get("images", [])
        ],
        "processes_holding_vm_count": len(raw.get("processes_holding_vm", [])),
        "classes": [
            {
                "id": item["id"],
                "disposition": item["disposition"],
                "description_key": item["description_key"],
            }
            for item in adapter["data_classes"]
        ],
        "source_path_boundary": _redact_home(str(raw.get("claude_support_path", "")), home),
    }


def inspect(adapter_id: str, *, home: Path | None = None) -> dict[str, Any]:
    catalog = load_catalog()
    adapter = adapter_for(adapter_id, catalog)
    validate_catalog(catalog, load_app_catalog())
    home = home or Path.home()
    details = (
        _wechat_inspection(adapter, home)
        if adapter_id == "wechat"
        else _claude_inspection(adapter, home)
    )
    return {
        "schema_version": 1,
        "kind": "app_adapter_inspection",
        "adapter_id": adapter_id,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        **details,
    }


def plan(adapter_id: str, *, inspection: dict[str, Any] | None = None, lang: str = "system") -> dict[str, Any]:
    adapter = adapter_for(adapter_id)
    inspection = inspection or inspect(adapter_id)
    operations = []
    for operation in adapter["operations"]:
        row = {
            "id": operation["id"],
            "risk": operation["risk"],
            "automatable": operation["automatable"],
            "description_key": operation["description_key"],
            "description": localization.message(operation["description_key"], lang),
        }
        if operation.get("action_id"):
            row["action_id"] = operation["action_id"]
            row["confirmation_mode"] = operation["confirmation_mode"]
        operations.append(row)
    return {
        "schema_version": 1,
        "kind": "app_adapter_plan",
        "adapter_id": adapter_id,
        "inspection_generated_at": inspection.get("generated_at"),
        "execution_mode": "manual_handoff_only" if adapter_id == "wechat" else "existing_transaction_only",
        "operations": operations,
        "privacy_boundary": "metadata_only",
    }


def _write_state(kind: str, value: dict[str, Any], state_dir: Path) -> Path:
    state_dir.mkdir(parents=True, exist_ok=True)
    path = state_dir / f"app-adapter-{kind}-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate SDK contracts")
    subparsers.add_parser("list", help="list declared adapters")
    for command in ("inspect", "plan"):
        item = subparsers.add_parser(command, help=f"{command} one adapter without generic apply")
        item.add_argument("--adapter", required=True, choices=["wechat", "claude-vm"])
        item.add_argument("--lang", default="system")
        item.add_argument("--state-dir", type=Path)
    args = parser.parse_args()
    if args.command == "validate":
        result = validate()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "passed" else 1
    if args.command == "list":
        catalog = load_catalog()
        print(json.dumps({"schema_version": 1, "adapters": catalog["adapters"]}, ensure_ascii=False, indent=2))
        return 0
    try:
        inspection = inspect(args.adapter)
        result = inspection if args.command == "inspect" else plan(args.adapter, inspection=inspection, lang=args.lang)
        output = _write_state(args.command, result, resolve_state_dir(args.state_dir))
        print(json.dumps({"record": str(output), "result": result}, ensure_ascii=False, indent=2))
        return 0
    except (AdapterError, localization.LocalizationError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
