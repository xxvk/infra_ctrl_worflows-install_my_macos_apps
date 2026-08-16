#!/usr/bin/env python3
"""Freeze private Safari plans and verify manual results without live writes."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import os
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from browser_lifecycle import item_fingerprint
from browser_review import BrowserReviewError, review_items
from safari_export import SafariExportError, parse_export
from schema_contract import validate_document
from state_paths import add_state_dir_argument, resolve_state_dir
from transaction_contract import require_confirmation, transaction_metadata


ACTION_ID = "browser.plan-freeze"
CONFIRMATION = "FREEZE BROWSER PLAN"
ALLOWED_ACTIONS = {"move", "merge", "archive", "delete"}
MAX_OPERATIONS = 1000


class BrowserTransactionError(RuntimeError):
    """A privacy-safe browser transaction planning failure."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise BrowserTransactionError("Safari export is unavailable") from exc
    return digest.hexdigest()


def _identity_boundary(item: Mapping[str, Any]) -> dict[str, Any]:
    source = item["source"]
    return {
        "browser": source["browser"],
        "profile_scope": source["profile_scope"],
        "profile_ref": source["profile_ref"],
        "account_ref": source["account_ref"],
    }


def _parse_created_at(value: str) -> None:
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise BrowserTransactionError("created_at must be ISO 8601") from exc
    if parsed.tzinfo is None:
        raise BrowserTransactionError("created_at must include a time zone")


def inspect_export(path: Path) -> dict[str, Any]:
    """Read one explicit supported export and retain private items in memory."""

    try:
        stat = path.stat()
        parsed = parse_export(path)
        reviewed = review_items(parsed["items"])
    except (OSError, SafariExportError, BrowserReviewError) as exc:
        raise BrowserTransactionError("Safari export is unavailable or invalid") from exc
    return {
        "items": reviewed["items"],
        "sha256": _file_sha256(path),
        "size_bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def _plan_hash(plan: Mapping[str, Any]) -> str:
    payload = copy.deepcopy(dict(plan))
    payload.pop("plan_sha256", None)
    return _sha256_bytes(_canonical_json(payload))


def validate_plan(plan: Mapping[str, Any]) -> list[str]:
    errors = validate_document(dict(plan), "browser-transaction-plan")
    if errors:
        return errors
    if plan["plan_sha256"] != _plan_hash(plan):
        errors.append("plan_sha256 does not match the frozen payload")
    if plan["backup"]["artifact_sha256"] != plan["source"]["artifact_sha256"]:
        errors.append("backup artifact does not match the source export")
    operation_ids = [row["operation_id"] for row in plan["operations"]]
    item_ids = [row["item_id"] for row in plan["operations"]]
    if len(operation_ids) != len(set(operation_ids)):
        errors.append("operation IDs must be unique")
    if len(item_ids) != len(set(item_ids)):
        errors.append("an item may appear as a source operation only once")
    if len(plan["operations"]) > MAX_OPERATIONS:
        errors.append("operation count exceeds the bounded maximum")
    if any(row["executable"] or row["interface_status"] != "unavailable" for row in plan["operations"]):
        errors.append("Safari operations must remain non-executable")
    if plan["apply_interface"]["supported"] or plan["execution_authorized"]:
        errors.append("plan must not authorize live Safari writes")
    return errors


def _operation_input_errors(operation: Mapping[str, Any]) -> list[str]:
    allowed = {"action", "item_id", "target_item_id", "target_collection"}
    errors = []
    if set(operation) - allowed:
        errors.append("operation contains unknown fields")
    action = operation.get("action")
    if action not in ALLOWED_ACTIONS:
        errors.append("operation action is unsupported")
    if not isinstance(operation.get("item_id"), str):
        errors.append("operation requires an item_id")
    target_item = operation.get("target_item_id")
    target_collection = operation.get("target_collection")
    if action == "merge":
        if not isinstance(target_item, str) or target_collection is not None:
            errors.append("merge requires only target_item_id")
    elif action in {"move", "archive"}:
        if target_item is not None:
            errors.append("move/archive cannot use target_item_id")
        if (
            not isinstance(target_collection, list)
            or not target_collection
            or any(not isinstance(value, str) or not value for value in target_collection)
        ):
            errors.append("move/archive requires a non-empty target_collection")
    elif action == "delete" and (target_item is not None or target_collection is not None):
        errors.append("delete cannot have a target")
    return errors


def build_plan_for_items(
    items: list[dict[str, Any]],
    operations: list[dict[str, Any]],
    *,
    source_path: Path,
    source_sha256: str,
    source_size: int,
    source_mtime_ns: int,
    created_at: str,
) -> dict[str, Any]:
    _parse_created_at(created_at)
    if not operations or len(operations) > MAX_OPERATIONS:
        raise BrowserTransactionError("operation list is empty or exceeds the limit")
    item_map = {item["item_id"]: item for item in items}
    if len(item_map) != len(items):
        raise BrowserTransactionError("browser item IDs must be unique")
    fingerprints = {item_id: item_fingerprint(item) for item_id, item in item_map.items()}
    initial_counts = Counter(fingerprints.values())
    final_counts = Counter(initial_counts)
    source_item_ids: set[str] = set()
    target_item_ids: set[str] = set()
    rows: list[dict[str, Any]] = []

    for operation in operations:
        errors = _operation_input_errors(operation)
        if errors:
            raise BrowserTransactionError(errors[0])
        item_id = operation["item_id"]
        if item_id in source_item_ids:
            raise BrowserTransactionError("an item may be planned only once")
        item = item_map.get(item_id)
        if item is None:
            raise BrowserTransactionError("operation references an unknown item")
        source_item_ids.add(item_id)
        action = operation["action"]
        source_fingerprint = fingerprints[item_id]
        final_counts[source_fingerprint] -= 1
        target_item_id = operation.get("target_item_id")
        target_fingerprint = None
        target_pre_count = None
        target_collection = operation.get("target_collection")
        expected_post_fingerprint = None
        expected_post_pre_count = None

        if action == "merge":
            if target_item_id == item_id:
                raise BrowserTransactionError("merge target must differ from source")
            target = item_map.get(target_item_id)
            if target is None:
                raise BrowserTransactionError("merge references an unknown target")
            if _identity_boundary(target) != _identity_boundary(item):
                raise BrowserTransactionError("merge cannot cross an identity boundary")
            target_item_ids.add(target_item_id)
            target_fingerprint = fingerprints[target_item_id]
            target_pre_count = initial_counts[target_fingerprint]
        elif action in {"move", "archive"}:
            changed = copy.deepcopy(item)
            changed["collection"]["kind"] = "bookmarks"
            changed["collection"]["path"] = list(target_collection)
            expected_post_fingerprint = item_fingerprint(changed)
            if expected_post_fingerprint == source_fingerprint:
                raise BrowserTransactionError("move/archive target would not change the item")
            expected_post_pre_count = initial_counts[expected_post_fingerprint]
            final_counts[expected_post_fingerprint] += 1

        seed = {
            "source_sha256": source_sha256,
            "action": action,
            "item_id": item_id,
            "target_item_id": target_item_id,
            "target_collection": target_collection,
        }
        rows.append(
            {
                "operation_id": "bop_" + _sha256_bytes(_canonical_json(seed))[:24],
                "action": action,
                "item_id": item_id,
                "identity_boundary": _identity_boundary(item),
                "source_fingerprint": source_fingerprint,
                "source_pre_count": initial_counts[source_fingerprint],
                "source_expected_post_count": None,
                "target_item_id": target_item_id,
                "target_fingerprint": target_fingerprint,
                "target_pre_count": target_pre_count,
                "target_expected_post_count": None,
                "target_collection": list(target_collection) if target_collection else None,
                "expected_post_fingerprint": expected_post_fingerprint,
                "expected_post_pre_count": expected_post_pre_count,
                "expected_post_count": None,
                "interface_status": "unavailable",
                "executable": False,
            }
        )

    if source_item_ids & target_item_ids:
        raise BrowserTransactionError("a merge target cannot also be a planned source")
    for row in rows:
        row["source_expected_post_count"] = final_counts[row["source_fingerprint"]]
        if row["target_fingerprint"] is not None:
            row["target_expected_post_count"] = final_counts[row["target_fingerprint"]]
        if row["expected_post_fingerprint"] is not None:
            row["expected_post_count"] = final_counts[row["expected_post_fingerprint"]]

    plan_seed = {
        "source_sha256": source_sha256,
        "created_at": created_at,
        "operations": rows,
    }
    plan = {
        "schema_version": 1,
        "kind": "browser_transaction_plan",
        "plan_id": "btp_" + _sha256_bytes(_canonical_json(plan_seed))[:24],
        "created_at": created_at,
        "plan_sha256": "0" * 64,
        "source": {
            "browser": "safari",
            "interface": "safari_export_zip",
            "path": str(source_path.expanduser().resolve()),
            "artifact_sha256": source_sha256,
            "size_bytes": source_size,
            "mtime_ns": source_mtime_ns,
            "item_count": len(items),
        },
        "backup": {
            "kind": "safari_bookmarks_only_export",
            "artifact_sha256": source_sha256,
            "verified": True,
            "unencrypted": True,
            "recovery_mode": "manual_import_additive",
            "exact_rollback_supported": False,
        },
        "operations": rows,
        "apply_interface": {
            "supported": False,
            "status": "interface_unavailable",
            "reason": "supported_item_write_interface_unavailable",
            "manual_handoff_only": True,
        },
        "privacy": {
            "provenance": "machine_observation",
            "storage_layer": "machine_local",
            "contains_private_content": True,
            "git_allowed": False,
            "redaction_required": True,
        },
        "execution_authorized": False,
    }
    plan["plan_sha256"] = _plan_hash(plan)
    errors = validate_plan(plan)
    if errors:
        raise BrowserTransactionError("generated browser plan is invalid")
    return plan


def build_plan(
    export: Path,
    operations: list[dict[str, Any]],
    *,
    created_at: str,
) -> dict[str, Any]:
    inspected = inspect_export(export)
    return build_plan_for_items(
        inspected["items"],
        operations,
        source_path=export,
        source_sha256=inspected["sha256"],
        source_size=inspected["size_bytes"],
        source_mtime_ns=inspected["mtime_ns"],
        created_at=created_at,
    )


def operations_from_organization(
    organization: Mapping[str, Any],
    items: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Convert reviewed bookmark dispositions without copying titles or URLs."""

    if organization.get("execution_authorized") is not False:
        raise BrowserTransactionError("organization must not authorize execution")
    decisions = organization.get("decisions")
    if not isinstance(decisions, list):
        raise BrowserTransactionError("organization decisions are unavailable")
    item_map = {item["item_id"]: item for item in items}
    if len(item_map) != len(items):
        raise BrowserTransactionError("browser item IDs must be unique")
    decision_ids = [row.get("item_id") for row in decisions if isinstance(row, dict)]
    if len(decision_ids) != len(decisions) or len(decision_ids) != len(set(decision_ids)):
        raise BrowserTransactionError("organization decisions must contain unique item IDs")
    if set(decision_ids) != set(item_map):
        raise BrowserTransactionError("organization decisions do not match the current export")

    operations: list[dict[str, Any]] = []
    for decision in decisions:
        item = item_map[decision["item_id"]]
        if decision.get("item_fingerprint") != item_fingerprint(item):
            raise BrowserTransactionError("organization item fingerprint has drifted")
        if decision.get("execution_authorized") is not False:
            raise BrowserTransactionError("organization decision authorizes execution")
        item_type = decision.get("item_type")
        disposition = decision.get("disposition")
        target = decision.get("target_collection")
        if item_type == "reading_list":
            if disposition not in {"delete_later", "defer"} or target is not None:
                raise BrowserTransactionError("Reading List organization decision is invalid")
            continue
        if item_type != "bookmark" or item.get("item_type") != "bookmark":
            raise BrowserTransactionError("organization item type does not match the export")
        if disposition in {"move", "archive"}:
            operations.append(
                {
                    "action": disposition,
                    "item_id": decision["item_id"],
                    "target_collection": copy.deepcopy(target),
                }
            )
        elif disposition == "delete":
            if target is not None:
                raise BrowserTransactionError("delete organization decision cannot have a target")
            operations.append({"action": "delete", "item_id": decision["item_id"]})
        else:
            raise BrowserTransactionError("bookmark organization disposition is invalid")
    if not operations:
        raise BrowserTransactionError("organization contains no bookmark operations")
    return operations


def build_plan_from_organization(
    export: Path,
    organization: Mapping[str, Any],
    *,
    created_at: str,
) -> dict[str, Any]:
    """Build an export-bound, non-executable plan from one validated organization."""

    from browser_organization import validate_organization

    if validate_organization(organization):
        raise BrowserTransactionError("browser organization is invalid")
    inspected = inspect_export(export)
    source = organization.get("source")
    if not isinstance(source, dict) or source.get("artifact_sha256") != inspected["sha256"]:
        raise BrowserTransactionError("browser organization source export has drifted")
    operations = operations_from_organization(organization, inspected["items"])
    expected_count = organization.get("summary", {}).get("bookmark_operation_count")
    if expected_count != len(operations):
        raise BrowserTransactionError("browser organization operation count is invalid")
    return build_plan_for_items(
        inspected["items"],
        operations,
        source_path=export,
        source_sha256=inspected["sha256"],
        source_size=inspected["size_bytes"],
        source_mtime_ns=inspected["mtime_ns"],
        created_at=created_at,
    )


def _plan_bytes(plan: Mapping[str, Any]) -> bytes:
    return (json.dumps(plan, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def freeze_plan(
    plan: Mapping[str, Any],
    state_dir: Path,
    *,
    confirmation: str,
) -> dict[str, Any]:
    errors = validate_plan(plan)
    if errors:
        raise BrowserTransactionError("browser plan is invalid")
    require_confirmation(ACTION_ID, confirmation)
    destination = state_dir / "browser" / "plans" / f"{plan['plan_id']}.json"
    payload = _plan_bytes(plan)
    if destination.exists():
        try:
            existing = destination.read_bytes()
        except OSError as exc:
            raise BrowserTransactionError("existing browser plan is unreadable") from exc
        if existing != payload:
            raise BrowserTransactionError("refusing to overwrite a different browser plan")
        status = "unchanged"
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=destination.parent, prefix=".browser-plan-", delete=False
            ) as output:
                temporary = Path(output.name)
                output.write(payload)
                output.flush()
                os.fsync(output.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, destination)
        except OSError as exc:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            raise BrowserTransactionError("failed to freeze browser plan") from exc
        status = "written"
    try:
        verified = json.loads(destination.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BrowserTransactionError("frozen browser plan failed read-back") from exc
    if verified != dict(plan) or validate_plan(verified):
        raise BrowserTransactionError("frozen browser plan failed verification")
    metadata = transaction_metadata(
        "browser.plan-freeze",
        phase="record",
        status=status,
        targets=[plan["plan_id"]],
    )
    return {
        **metadata,
        "status": status,
        "verified": True,
        "writes_performed": status == "written",
        "browser_writes_performed": False,
        "execution_authorized": False,
    }


def _redacted_failure(reasons: list[str]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "browser_transaction_verification_summary",
        "status": "failed",
        "reasons": sorted(set(reasons)),
        "private_content_emitted": False,
        "writes_performed": False,
        "execution_authorized": False,
    }


def verify_preapply(plan: Mapping[str, Any], export: Path) -> dict[str, Any]:
    errors = validate_plan(plan)
    if errors:
        return _redacted_failure(["invalid_plan"])
    if _file_sha256(export) != plan["source"]["artifact_sha256"]:
        return _redacted_failure(["source_export_changed"])
    try:
        inspected = inspect_export(export)
    except BrowserTransactionError:
        return _redacted_failure(["source_export_unavailable"])
    item_map = {item["item_id"]: item for item in inspected["items"]}
    reasons = []
    for operation in plan["operations"]:
        current = item_map.get(operation["item_id"])
        if current is None:
            reasons.append("planned_item_missing")
        elif item_fingerprint(current) != operation["source_fingerprint"]:
            reasons.append("planned_item_changed")
    if reasons:
        return _redacted_failure(reasons)
    return {
        "schema_version": 1,
        "kind": "browser_transaction_verification_summary",
        "status": "passed",
        "verified_operation_count": len(plan["operations"]),
        "apply_interface": "unavailable",
        "private_content_emitted": False,
        "writes_performed": False,
        "execution_authorized": False,
    }


def apply_live_safari(plan: Mapping[str, Any], export: Path) -> dict[str, Any]:
    preflight = verify_preapply(plan, export)
    if preflight["status"] != "passed":
        return preflight
    return {
        "schema_version": 1,
        "kind": "browser_transaction_apply_summary",
        "status": "blocked",
        "reason": "supported_item_write_interface_unavailable",
        "manual_handoff_only": True,
        "private_content_emitted": False,
        "writes_performed": False,
        "execution_authorized": False,
    }


def verify_post_export(plan: Mapping[str, Any], export: Path) -> dict[str, Any]:
    if validate_plan(plan):
        return _redacted_failure(["invalid_plan"])
    try:
        inspected = inspect_export(export)
    except BrowserTransactionError:
        return _redacted_failure(["post_export_unavailable"])
    counts = Counter(item_fingerprint(item) for item in inspected["items"])
    passed = 0
    failed = 0
    failure_reasons: Counter[str] = Counter()
    for operation in plan["operations"]:
        checks = [
            counts[operation["source_fingerprint"]]
            == operation["source_expected_post_count"]
        ]
        if operation["target_fingerprint"] is not None:
            checks.append(
                counts[operation["target_fingerprint"]]
                == operation["target_expected_post_count"]
            )
        if operation["expected_post_fingerprint"] is not None:
            checks.append(
                counts[operation["expected_post_fingerprint"]]
                == operation["expected_post_count"]
            )
        if all(checks):
            passed += 1
        else:
            failed += 1
            failure_reasons["post_export_mismatch"] += 1
    return {
        "schema_version": 1,
        "kind": "browser_transaction_verification_summary",
        "status": "passed" if failed == 0 else "failed",
        "verified_operation_count": passed,
        "failed_operation_count": failed,
        "failure_reason_counts": dict(sorted(failure_reasons.items())),
        "private_content_emitted": False,
        "writes_performed": False,
        "execution_authorized": False,
    }


def _load_json(path: Path, *, expected: type) -> Any:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BrowserTransactionError("private input is unavailable or invalid") from exc
    if not isinstance(value, expected):
        raise BrowserTransactionError("private input is unavailable or invalid")
    return value


def _plan_summary(plan: Mapping[str, Any], *, status: str, writes: bool) -> dict[str, Any]:
    counts = Counter(row["action"] for row in plan["operations"])
    return {
        "schema_version": 1,
        "kind": "browser_transaction_redacted_summary",
        "status": status,
        "operation_count": len(plan["operations"]),
        "operation_counts": dict(sorted(counts.items())),
        "backup_verified": True,
        "exact_rollback_supported": False,
        "apply_interface": "unavailable",
        "private_content_emitted": False,
        "writes_performed": writes,
        "browser_writes_performed": False,
        "execution_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser(
        "validate-plan", help="validate one explicit private or fictional plan"
    )
    validate_parser.add_argument("plan", type=Path)
    plan_parser = subparsers.add_parser(
        "plan-safari-export", help="preview or freeze a plan for one explicit export"
    )
    plan_parser.add_argument("export", type=Path)
    plan_input = plan_parser.add_mutually_exclusive_group(required=True)
    plan_input.add_argument("--operations", type=Path)
    plan_input.add_argument("--organization", type=Path)
    plan_parser.add_argument("--created-at")
    plan_parser.add_argument("--apply", action="store_true")
    plan_parser.add_argument("--confirm", default="")
    add_state_dir_argument(plan_parser)
    pre_parser = subparsers.add_parser("verify-preapply")
    pre_parser.add_argument("plan", type=Path)
    pre_parser.add_argument("export", type=Path)
    post_parser = subparsers.add_parser("verify-post-export")
    post_parser.add_argument("plan", type=Path)
    post_parser.add_argument("export", type=Path)
    apply_parser = subparsers.add_parser("apply-live-safari")
    apply_parser.add_argument("plan", type=Path)
    apply_parser.add_argument("export", type=Path)
    args = parser.parse_args(argv)

    try:
        if args.command == "validate-plan":
            plan = _load_json(args.plan, expected=dict)
            errors = validate_plan(plan)
            result = {
                "schema_version": 1,
                "kind": "browser_transaction_redacted_summary",
                "status": "passed" if not errors else "failed",
                "operation_count": len(plan.get("operations", [])),
                "errors": errors,
                "private_content_emitted": False,
                "writes_performed": False,
                "execution_authorized": False,
            }
        elif args.command == "plan-safari-export":
            created_at = args.created_at or dt.datetime.now(dt.timezone.utc).isoformat()
            if args.organization is not None:
                organization = _load_json(args.organization, expected=dict)
                plan = build_plan_from_organization(
                    args.export,
                    organization,
                    created_at=created_at,
                )
            else:
                operations = _load_json(args.operations, expected=list)
                plan = build_plan(args.export, operations, created_at=created_at)
            if not args.apply:
                result = _plan_summary(plan, status="preview", writes=False)
            else:
                record = freeze_plan(
                    plan,
                    resolve_state_dir(args.state_dir),
                    confirmation=args.confirm,
                )
                result = _plan_summary(
                    plan,
                    status=record["status"],
                    writes=record["writes_performed"],
                )
                result["action_id"] = record["action_id"]
                result["verified"] = record["verified"]
        else:
            plan = _load_json(args.plan, expected=dict)
            if args.command == "verify-preapply":
                result = verify_preapply(plan, args.export)
            elif args.command == "verify-post-export":
                result = verify_post_export(plan, args.export)
            else:
                result = apply_live_safari(plan, args.export)
    except (BrowserTransactionError, ValueError, KeyError) as exc:
        summary_kind = {
            "apply-live-safari": "browser_transaction_apply_summary",
            "verify-preapply": "browser_transaction_verification_summary",
            "verify-post-export": "browser_transaction_verification_summary",
        }.get(args.command, "browser_transaction_redacted_summary")
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": summary_kind,
                    "status": "failed",
                    "error": str(exc),
                    "private_content_emitted": False,
                    "writes_performed": False,
                    "execution_authorized": False,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"passed", "preview", "written", "unchanged", "blocked"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
