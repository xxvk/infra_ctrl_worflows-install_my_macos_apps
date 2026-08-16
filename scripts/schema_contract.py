#!/usr/bin/env python3
# Mutation action ID: schema.migrate-write
"""Validate registered JSON contracts and migrate version envelopes safely."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "references" / "schema-registry.json"
SCHEMA_DIALECT = "https://json-schema.org/draft/2020-12/schema"
MUTATION_ACTION_ID = "schema.migrate-write"
WRITE_CONFIRMATION = "WRITE SCHEMA MIGRATION"
SUPPORTED_SCHEMA_KEYS = {
    "$schema",
    "$id",
    "title",
    "description",
    "type",
    "required",
    "properties",
    "additionalProperties",
    "items",
    "enum",
    "const",
    "minItems",
    "maxItems",
    "minLength",
    "pattern",
    "minimum",
    "anyOf",
}


class SchemaContractError(RuntimeError):
    """Raised when a registry, schema, document, or migration is invalid."""


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SchemaContractError(f"JSON file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SchemaContractError(f"invalid JSON in {path}: {exc}") from exc


def load_registry(
    path: Path = REGISTRY_PATH,
    *,
    root: Path = ROOT,
) -> dict[str, Any]:
    value = load_json(path)
    if not isinstance(value, dict):
        raise SchemaContractError("schema registry must be an object")
    if value.get("schema_version") != 1:
        raise SchemaContractError("schema registry schema_version must be 1")
    if value.get("kind") != "json_schema_registry":
        raise SchemaContractError("schema registry kind is invalid")
    if value.get("dialect") != SCHEMA_DIALECT:
        raise SchemaContractError("schema registry dialect is invalid")
    formats = value.get("formats")
    if not isinstance(formats, dict) or not formats:
        raise SchemaContractError("schema registry formats must be a non-empty object")
    for kind, entry in formats.items():
        if not isinstance(kind, str) or not kind or not isinstance(entry, dict):
            raise SchemaContractError("schema registry contains an invalid format entry")
        if entry.get("current_version") != 1:
            raise SchemaContractError(f"{kind}: current_version must be 1")
        relative = entry.get("schema")
        if not isinstance(relative, str) or not relative:
            raise SchemaContractError(f"{kind}: schema path is missing")
        schema_path = (root / relative).resolve()
        if not _inside(schema_path, root):
            raise SchemaContractError(f"{kind}: schema path escapes repository")
        if not schema_path.is_file():
            raise SchemaContractError(f"{kind}: schema not found: {relative}")
        examples = entry.get("tracked_examples")
        if not isinstance(examples, list):
            raise SchemaContractError(f"{kind}: tracked_examples must be a list")
    return value


def _audit_schema_node(schema: Any, path: str, errors: list[str]) -> None:
    if not isinstance(schema, dict):
        errors.append(f"{path}: schema node must be an object")
        return
    unsupported = sorted(set(schema) - SUPPORTED_SCHEMA_KEYS)
    if unsupported:
        errors.append(f"{path}: unsupported schema keywords: {', '.join(unsupported)}")
    properties = schema.get("properties")
    if properties is not None:
        if not isinstance(properties, dict):
            errors.append(f"{path}.properties: must be an object")
        else:
            for name, child in properties.items():
                _audit_schema_node(child, f"{path}.properties[{name!r}]", errors)
    items = schema.get("items")
    if items is not None:
        _audit_schema_node(items, f"{path}.items", errors)
    additional = schema.get("additionalProperties")
    if isinstance(additional, dict):
        _audit_schema_node(additional, f"{path}.additionalProperties", errors)
    elif additional is not None and not isinstance(additional, bool):
        errors.append(f"{path}.additionalProperties: must be a boolean or schema")
    alternatives = schema.get("anyOf")
    if alternatives is not None:
        if not isinstance(alternatives, list) or not alternatives:
            errors.append(f"{path}.anyOf: must be a non-empty array")
        else:
            for index, child in enumerate(alternatives):
                _audit_schema_node(child, f"{path}.anyOf[{index}]", errors)


def audit_schema(schema: Any) -> list[str]:
    errors: list[str] = []
    _audit_schema_node(schema, "$schema", errors)
    if isinstance(schema, dict) and schema.get("$schema") != SCHEMA_DIALECT:
        errors.append(f"$schema: must declare {SCHEMA_DIALECT}")
    return errors


def _matches_type(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "null":
        return value is None
    return False


def _validate(value: Any, schema: dict[str, Any], path: str, errors: list[str]) -> None:
    expected = schema.get("type")
    if expected is not None:
        accepted = [expected] if isinstance(expected, str) else expected
        if not isinstance(accepted, list) or not all(isinstance(item, str) for item in accepted):
            errors.append(f"{path}: schema type declaration is invalid")
            return
        if not any(_matches_type(value, item) for item in accepted):
            errors.append(f"{path}: expected {' or '.join(accepted)}, got {type(value).__name__}")
            return

    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected constant {schema['const']!r}")
    if "enum" in schema:
        choices = schema["enum"]
        if not isinstance(choices, list) or value not in choices:
            errors.append(f"{path}: value {value!r} is not in the allowed enum")

    alternatives = schema.get("anyOf")
    if isinstance(alternatives, list):
        matched = False
        for alternative in alternatives:
            alternative_errors: list[str] = []
            _validate(value, alternative, path, alternative_errors)
            if not alternative_errors:
                matched = True
                break
        if not matched:
            errors.append(f"{path}: does not match any allowed schema alternative")

    if isinstance(value, dict):
        required = schema.get("required", [])
        if isinstance(required, list):
            for name in required:
                if name not in value:
                    errors.append(f"{path}: missing required property {name!r}")
        properties = schema.get("properties", {})
        if isinstance(properties, dict):
            for name, child_schema in properties.items():
                if name in value:
                    _validate(value[name], child_schema, f"{path}.{name}", errors)
            extras = set(value) - set(properties)
            additional = schema.get("additionalProperties", True)
            if additional is False:
                for name in sorted(extras):
                    errors.append(f"{path}: additional property is not allowed: {name!r}")
            elif isinstance(additional, dict):
                for name in sorted(extras):
                    _validate(value[name], additional, f"{path}.{name}", errors)

    if isinstance(value, list):
        minimum = schema.get("minItems")
        if isinstance(minimum, int) and len(value) < minimum:
            errors.append(f"{path}: expected at least {minimum} items")
        maximum = schema.get("maxItems")
        if isinstance(maximum, int) and len(value) > maximum:
            errors.append(f"{path}: expected at most {maximum} items")
        item_schema = schema.get("items")
        if isinstance(item_schema, dict):
            for index, item in enumerate(value):
                _validate(item, item_schema, f"{path}[{index}]", errors)

    if isinstance(value, str):
        minimum = schema.get("minLength")
        if isinstance(minimum, int) and len(value) < minimum:
            errors.append(f"{path}: expected at least {minimum} characters")
        pattern = schema.get("pattern")
        if isinstance(pattern, str) and re.search(pattern, value) is None:
            errors.append(f"{path}: does not match pattern {pattern!r}")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        if isinstance(minimum, (int, float)) and value < minimum:
            errors.append(f"{path}: must be at least {minimum}")


def validate_instance(value: Any, schema: dict[str, Any]) -> list[str]:
    schema_errors = audit_schema(schema)
    if schema_errors:
        raise SchemaContractError("; ".join(schema_errors))
    errors: list[str] = []
    _validate(value, schema, "$", errors)
    return errors


def schema_for(
    kind: str,
    *,
    registry_path: Path = REGISTRY_PATH,
    root: Path = ROOT,
) -> tuple[dict[str, Any], dict[str, Any]]:
    registry = load_registry(registry_path, root=root)
    entry = registry["formats"].get(kind)
    if not isinstance(entry, dict):
        raise SchemaContractError(f"unknown schema kind: {kind}")
    schema = load_json(root / entry["schema"])
    if not isinstance(schema, dict):
        raise SchemaContractError(f"{kind}: schema must be an object")
    errors = audit_schema(schema)
    if errors:
        raise SchemaContractError("; ".join(errors))
    return schema, entry


def validate_document(
    value: Any,
    kind: str,
    *,
    registry_path: Path = REGISTRY_PATH,
    root: Path = ROOT,
) -> list[str]:
    schema, _entry = schema_for(kind, registry_path=registry_path, root=root)
    return validate_instance(value, schema)


def load_and_validate(
    path: Path,
    kind: str,
    *,
    registry_path: Path = REGISTRY_PATH,
    root: Path = ROOT,
) -> Any:
    value = load_json(path)
    errors = validate_document(value, kind, registry_path=registry_path, root=root)
    if errors:
        raise SchemaContractError(f"{kind} validation failed for {path}: " + "; ".join(errors))
    return value


def validate_tracked(
    *,
    registry_path: Path = REGISTRY_PATH,
    root: Path = ROOT,
) -> dict[str, Any]:
    registry = load_registry(registry_path, root=root)
    rows = []
    errors = []
    for kind, entry in registry["formats"].items():
        schema, _ = schema_for(kind, registry_path=registry_path, root=root)
        for relative in entry["tracked_examples"]:
            path = (root / relative).resolve()
            if not _inside(path, root):
                row_errors = ["example path escapes repository"]
            elif not path.is_file():
                row_errors = ["example file not found"]
            else:
                try:
                    row_errors = validate_instance(load_json(path), schema)
                except SchemaContractError as exc:
                    row_errors = [str(exc)]
            rows.append(
                {
                    "kind": kind,
                    "path": relative,
                    "status": "passed" if not row_errors else "failed",
                    "errors": row_errors,
                }
            )
            errors.extend(f"{relative}: {error}" for error in row_errors)
    return {
        "schema_version": 1,
        "status": "passed" if not errors else "failed",
        "formats": len(registry["formats"]),
        "examples": len(rows),
        "results": rows,
        "errors": errors,
    }


def migrate_document(
    value: Any,
    kind: str,
    target_version: int,
    *,
    allow_downgrade: bool = False,
    registry_path: Path = REGISTRY_PATH,
    root: Path = ROOT,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SchemaContractError("migration source must be a JSON object")
    schema_for(kind, registry_path=registry_path, root=root)
    source_version = value.get("schema_version", 0)
    if not isinstance(source_version, int) or isinstance(source_version, bool):
        raise SchemaContractError("schema_version must be an integer")
    if source_version not in {0, 1} or target_version not in {0, 1}:
        raise SchemaContractError("only schema versions 0 and 1 are supported")
    if target_version < source_version and not allow_downgrade:
        raise SchemaContractError("downgrade requires --allow-downgrade")

    if source_version == target_version:
        migrated = dict(value)
    elif source_version == 0 and target_version == 1:
        migrated = {"schema_version": 1, **value}
    elif source_version == 1 and target_version == 0:
        migrated = {key: child for key, child in value.items() if key != "schema_version"}
    else:
        raise SchemaContractError(f"unsupported migration: {source_version} -> {target_version}")

    if target_version == 1:
        errors = validate_document(
            migrated,
            kind,
            registry_path=registry_path,
            root=root,
        )
        if errors:
            raise SchemaContractError("migrated document is invalid: " + "; ".join(errors))
    return migrated


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def write_migration(
    output: Path,
    value: Any,
    *,
    source: Path,
) -> dict[str, Any]:
    output = output.expanduser().resolve()
    source = source.expanduser().resolve()
    if output == source:
        raise SchemaContractError("migration output must differ from the source path")
    if not output.parent.is_dir():
        raise SchemaContractError(f"migration output directory does not exist: {output.parent}")
    payload = canonical_bytes(value)
    if output.exists():
        existing = output.read_bytes()
        if existing != payload:
            raise SchemaContractError(f"refusing to overwrite different output: {output}")
        status = "unchanged"
    else:
        temporary = output.with_name(f".{output.name}.tmp-{os.getpid()}")
        try:
            with temporary.open("xb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, output)
        finally:
            if temporary.exists():
                temporary.unlink()
        status = "written"
    readback = output.read_bytes()
    if readback != payload:
        raise SchemaContractError("migration output read-back differs from the planned payload")
    return {
        "schema_version": 1,
        "action_id": MUTATION_ACTION_ID,
        "status": status,
        "source": str(source),
        "output": str(output),
        "bytes": len(payload),
        "sha256": sha256_bytes(readback),
        "verified": True,
    }


def _print_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list", help="list registered JSON format contracts")
    subparsers.add_parser("validate-tracked", help="validate every registered tracked example")
    validate_parser = subparsers.add_parser("validate", help="validate one JSON document")
    validate_parser.add_argument("kind")
    validate_parser.add_argument("path", type=Path)
    migrate_parser = subparsers.add_parser("migrate", help="preview or write a version migration")
    migrate_parser.add_argument("kind")
    migrate_parser.add_argument("path", type=Path)
    migrate_parser.add_argument("--to", type=int, required=True, choices=[0, 1])
    migrate_parser.add_argument("--allow-downgrade", action="store_true")
    migrate_parser.add_argument("--output", type=Path)
    migrate_parser.add_argument("--apply", action="store_true")
    migrate_parser.add_argument("--confirm")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "list":
            registry = load_registry()
            _print_json(
                {
                    "schema_version": 1,
                    "dialect": registry["dialect"],
                    "formats": [
                        {
                            "kind": kind,
                            "current_version": entry["current_version"],
                            "schema": entry["schema"],
                            "tracked_examples": len(entry["tracked_examples"]),
                        }
                        for kind, entry in registry["formats"].items()
                    ],
                }
            )
            return 0
        if args.command == "validate-tracked":
            result = validate_tracked()
            _print_json(result)
            return 0 if result["status"] == "passed" else 1
        if args.command == "validate":
            load_and_validate(args.path.expanduser().resolve(), args.kind)
            _print_json(
                {
                    "schema_version": 1,
                    "status": "passed",
                    "kind": args.kind,
                    "path": str(args.path.expanduser().resolve()),
                }
            )
            return 0
        if args.command == "migrate":
            source = args.path.expanduser().resolve()
            original = load_json(source)
            migrated = migrate_document(
                original,
                args.kind,
                args.to,
                allow_downgrade=args.allow_downgrade,
            )
            source_version = original.get("schema_version", 0) if isinstance(original, dict) else None
            if not args.apply:
                _print_json(
                    {
                        "schema_version": 1,
                        "status": "preview",
                        "kind": args.kind,
                        "source_version": source_version,
                        "target_version": args.to,
                        "source": str(source),
                        "output": str(args.output.expanduser().resolve()) if args.output else None,
                        "document": migrated,
                    }
                )
                return 0
            if args.confirm != WRITE_CONFIRMATION:
                raise SchemaContractError(
                    f"--apply requires --confirm {WRITE_CONFIRMATION!r}"
                )
            if args.output is None:
                raise SchemaContractError("--apply requires a separate --output path")
            result = write_migration(args.output, migrated, source=source)
            result.update(
                {
                    "kind": args.kind,
                    "source_version": source_version,
                    "target_version": args.to,
                }
            )
            _print_json(result)
            return 0
    except SchemaContractError as exc:
        print(f"schema contract error: {exc}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
