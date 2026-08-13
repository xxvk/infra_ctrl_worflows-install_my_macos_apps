#!/usr/bin/env python3
"""Validate and merge public policy with iCloud-synced, Git-ignored Private configuration."""

from __future__ import annotations

import argparse
import copy
import json
import os
import re
from pathlib import Path
from typing import Any, Mapping

from schema_contract import SchemaContractError, load_and_validate


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "Private" / "manifest.json"
DEFAULT_CATALOG = ROOT / "references" / "app-catalog.json"
DEFAULT_CATALOG_OVERLAY = ROOT / "Private" / "app-catalog-overlay.json"
PUBLIC_ONLY_ENV = "MACOMRADE_PUBLIC_ONLY"
FORBIDDEN_KEYS = {
    "api_key",
    "access_token",
    "refresh_token",
    "password",
    "private_key",
    "recovery_code",
    "cookie",
    "session_token",
}
PRIVATE_LOCATOR_KINDS = {
    "icloud_private_config_locator",
    "tracked_private_config_locator",  # backward compatibility before 0.1.1
}
APP_CATALOG_OVERLAY_KIND = "app_catalog_private_overlay"


class ConfigurationLayerError(RuntimeError):
    pass


def public_only_enabled(environ: Mapping[str, str] | None = None) -> bool:
    environment = os.environ if environ is None else environ
    return environment.get(PUBLIC_ONLY_ENV, "").strip().casefold() in {
        "1",
        "true",
        "yes",
        "on",
    }


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigurationLayerError(f"configuration file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigurationLayerError(f"invalid JSON in {path}: {exc}") from exc


def _load_locator_document(path: Path) -> Any:
    """Read JSON or the deliberately tiny YAML subset used by locator files."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConfigurationLayerError(f"configuration file not found: {path}") from exc
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        values: dict[str, Any] = {}
        for raw_line in text.splitlines():
            if not raw_line or raw_line.lstrip().startswith("#"):
                continue
            if raw_line[0].isspace() or ":" not in raw_line:
                continue
            key, raw_value = raw_line.split(":", 1)
            key = key.strip()
            value = raw_value.strip().strip("\"'")
            if not key or not value:
                continue
            values[key] = int(value) if key == "schema_version" and value.isdigit() else value
        return values


def deep_merge(base: Any, overlay: Any) -> Any:
    """Return a merged copy; dictionaries recurse and all other values replace."""
    if isinstance(base, dict) and isinstance(overlay, dict):
        merged = copy.deepcopy(base)
        for key, value in overlay.items():
            merged[key] = (
                deep_merge(merged[key], value)
                if key in merged
                else copy.deepcopy(value)
            )
        return merged
    return copy.deepcopy(overlay)


def apply_app_catalog_overlay(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Merge personal app fields by stable app name and render account prompts."""
    if overlay.get("schema_version") != 1 or overlay.get("kind") != APP_CATALOG_OVERLAY_KIND:
        raise ConfigurationLayerError("app catalog Private overlay metadata is invalid")
    apps = base.get("apps")
    patches = overlay.get("apps")
    if not isinstance(apps, list) or not isinstance(patches, dict):
        raise ConfigurationLayerError("app catalog and Private overlay must contain apps")
    merged = copy.deepcopy(base)
    by_name = {
        app.get("name"): app
        for app in merged["apps"]
        if isinstance(app, dict) and isinstance(app.get("name"), str)
    }
    unknown = sorted(set(patches) - set(by_name))
    if unknown:
        raise ConfigurationLayerError(
            "Private app catalog overlay references unknown apps: " + ", ".join(unknown)
        )
    for name, patch in patches.items():
        if not isinstance(patch, dict):
            raise ConfigurationLayerError(f"Private app patch must be an object: {name}")
        if "name" in patch:
            raise ConfigurationLayerError(f"Private app patch cannot replace name: {name}")
        by_name[name].update(deep_merge({}, patch))

    for app in merged["apps"]:
        account = app.get("preferred_account")
        follow_up = app.get("follow_up")
        if not isinstance(follow_up, list):
            continue
        rendered = []
        for item in follow_up:
            if isinstance(item, str) and "{preferred_account}" in item:
                if not account:
                    raise ConfigurationLayerError(
                        f"app requires preferred_account from Private overlay: {app.get('name')}"
                    )
                item = item.replace("{preferred_account}", str(account))
            rendered.append(item)
        app["follow_up"] = rendered
    return merged


def load_app_catalog(
    base_path: Path = DEFAULT_CATALOG,
    overlay_path: Path = DEFAULT_CATALOG_OVERLAY,
    *,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    try:
        base = load_and_validate(base_path, "catalog")
    except SchemaContractError as exc:
        raise ConfigurationLayerError(str(exc)) from exc
    default_overlay = overlay_path.expanduser().resolve() == DEFAULT_CATALOG_OVERLAY.resolve()
    if (default_overlay and public_only_enabled(environ)) or not overlay_path.is_file():
        if not isinstance(base, dict):
            raise ConfigurationLayerError("app catalog base must be a JSON object")
        return base
    try:
        overlay = load_and_validate(overlay_path, "private-overlay")
    except SchemaContractError as exc:
        raise ConfigurationLayerError(str(exc)) from exc
    if not isinstance(base, dict) or not isinstance(overlay, dict):
        raise ConfigurationLayerError("app catalog layers must be JSON objects")
    return apply_app_catalog_overlay(base, overlay)


def _forbidden_key_paths(value: Any, prefix: str = "$") -> list[str]:
    findings: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in FORBIDDEN_KEYS:
                findings.append(f"{prefix}.{key}")
            findings.extend(_forbidden_key_paths(child, f"{prefix}.{key}"))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(_forbidden_key_paths(child, f"{prefix}[{index}]"))
    return findings


def _forbidden_text_key_lines(text: str) -> list[str]:
    """Find prohibited YAML-like mapping keys without parsing arbitrary YAML."""
    findings: list[str] = []
    key_pattern = re.compile(
        r"""^\s*(?:-\s*)?["']?([A-Za-z0-9_-]+)["']?\s*:"""
    )
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = key_pattern.match(line)
        if not match:
            continue
        normalized = match.group(1).strip().lower().replace("-", "_")
        if normalized in FORBIDDEN_KEYS:
            findings.append(f"line {line_number}: {match.group(1)}")
    return findings


def _inside_root(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def resolve_config_path(path: Path, *, root: Path = ROOT) -> Path:
    """Follow a tracked JSON or YAML Private locator inside the repository."""
    path = path.expanduser().resolve()
    value = _load_locator_document(path)
    if not isinstance(value, dict) or value.get("kind") not in PRIVATE_LOCATOR_KINDS:
        return path
    relative = value.get("private_path")
    if not isinstance(relative, str) or not relative:
        raise ConfigurationLayerError(f"Private locator has no private_path: {path}")
    target = root / relative
    if not _inside_root(target, root):
        raise ConfigurationLayerError(
            f"Private locator path escapes the repository: {relative}"
        )
    if not target.is_file():
        raise ConfigurationLayerError(f"Private locator target not found: {relative}")
    return target.resolve()


def audit_manifest(
    manifest_path: Path = DEFAULT_MANIFEST,
    *,
    root: Path = ROOT,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    manifest_path = manifest_path.expanduser().resolve()
    expected_default = (root / "Private" / "manifest.json").resolve()
    explicit_public_only = (
        manifest_path == DEFAULT_MANIFEST.resolve() and public_only_enabled(environ)
    )
    if explicit_public_only or (manifest_path == expected_default and not manifest_path.is_file()):
        return {
            "status": "valid",
            "mode": "public_only",
            "manifest": None,
            "overlay_count": 0,
            "checked_overlays": [],
            "missing_optional_overlays": [],
            "sync_policy": (
                "Private overlays are disabled by MACOMRADE_PUBLIC_ONLY."
                if explicit_public_only
                else "No iCloud Private overlay is present; public defaults are active."
            ),
            "secrets_policy": "Secrets never belong in Git or Private configuration.",
        }
    manifest = load_json(manifest_path)
    if not isinstance(manifest, dict):
        raise ConfigurationLayerError("Private manifest must be a JSON object")
    if manifest.get("schema_version") != 1:
        raise ConfigurationLayerError("Private manifest schema_version must be 1")
    if manifest.get("kind") not in {
        "icloud_private_overlay_manifest",
        "tracked_private_overlay_manifest",
    }:
        raise ConfigurationLayerError("Private manifest kind is invalid")
    if manifest.get("merge_precedence") not in (
        ["public_base", "icloud_private_overlay"],
        ["public_base", "tracked_private_overlay"],
    ):
        raise ConfigurationLayerError("Private manifest merge_precedence is invalid")
    overlays = manifest.get("overlays")
    if not isinstance(overlays, list):
        raise ConfigurationLayerError("Private manifest overlays must be a list")

    checked: list[str] = []
    missing_optional: list[str] = []
    seen_ids: set[str] = set()
    for entry in overlays:
        if not isinstance(entry, dict):
            raise ConfigurationLayerError("every Private overlay entry must be an object")
        overlay_id = entry.get("id")
        relative = entry.get("path")
        if not isinstance(overlay_id, str) or not overlay_id:
            raise ConfigurationLayerError("every Private overlay requires a non-empty id")
        if overlay_id in seen_ids:
            raise ConfigurationLayerError(f"duplicate Private overlay id: {overlay_id}")
        seen_ids.add(overlay_id)
        if not isinstance(relative, str) or not relative:
            raise ConfigurationLayerError(f"Private overlay {overlay_id} requires a path")
        path = root / relative
        if not _inside_root(path, root):
            raise ConfigurationLayerError(
                f"Private overlay path escapes the repository: {relative}"
            )
        if not path.is_file():
            if entry.get("optional") is True:
                missing_optional.append(relative)
                continue
            raise ConfigurationLayerError(f"Private overlay file not found: {relative}")
        overlay_format = entry.get("format", "json")
        if overlay_format == "json":
            findings = _forbidden_key_paths(load_json(path))
        elif overlay_format == "yaml":
            findings = _forbidden_text_key_lines(path.read_text(encoding="utf-8"))
        else:
            raise ConfigurationLayerError(
                f"Private overlay {overlay_id} has unsupported format: {overlay_format}"
            )
        if findings:
            raise ConfigurationLayerError(
                f"Private overlay contains prohibited secret-bearing keys: "
                + ", ".join(findings)
            )
        checked.append(relative)

    return {
        "status": "valid",
        "mode": "icloud_private",
        "manifest": str(manifest_path),
        "overlay_count": len(overlays),
        "checked_overlays": checked,
        "missing_optional_overlays": missing_optional,
        "sync_policy": "Private configuration is synchronized by iCloud Drive and ignored by Git.",
        "secrets_policy": "Private configuration may contain identifiers, never secrets.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    merge_parser = subparsers.add_parser("merge")
    merge_parser.add_argument("--base", type=Path, required=True)
    merge_parser.add_argument("--private", dest="private_path", type=Path)
    args = parser.parse_args()

    try:
        if args.command == "audit":
            result = audit_manifest(args.manifest)
        else:
            base = load_json(args.base)
            result = (
                deep_merge(base, load_json(args.private_path))
                if args.private_path
                else base
            )
    except ConfigurationLayerError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
