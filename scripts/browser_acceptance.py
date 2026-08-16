#!/usr/bin/env python3
"""Run Safari-only BR-08 acceptance without persisting private browser data."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any, Callable, Mapping

import browser_sources
from browser_lifecycle import (
    BrowserLifecycleError,
    build_review_queue,
    item_fingerprint,
    validate_ledger,
)
from browser_review import BrowserReviewError, redacted_summary, review_items
from browser_transactions import (
    BrowserTransactionError,
    apply_live_safari,
    build_plan,
    verify_post_export,
    verify_preapply,
)
from safari_export import SafariExportError, parse_export
from schema_contract import validate_document


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "references" / "browser-acceptance.json"
FIXTURE_PATH = ROOT / "tests" / "fixtures" / "schema_contract" / "browser-acceptance-v1.json"
EXPECTED_GATE_IDS = [f"BA-{index:02d}" for index in range(1, 11)]
ALLOWED_GATE_STATUSES = {"passed", "deferred", "interface_limited", "failed", "not_run"}


class BrowserAcceptanceError(RuntimeError):
    """A redacted Safari acceptance failure."""


def _load_json(path: Path, *, expected: type) -> Any:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BrowserAcceptanceError("private acceptance input is unavailable or invalid") from exc
    if not isinstance(value, expected):
        raise BrowserAcceptanceError("private acceptance input is unavailable or invalid")
    return value


def _load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BrowserAcceptanceError("browser acceptance contract is unavailable") from exc
    if not isinstance(value, dict):
        raise BrowserAcceptanceError("browser acceptance contract is unavailable")
    return value


def validate_contract(
    path: Path = CONTRACT_PATH,
    fixture: Path = FIXTURE_PATH,
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        contract = _load_contract(path)
    except BrowserAcceptanceError as exc:
        return {"status": "failed", "errors": [str(exc)]}
    if contract.get("schema_version") != 1:
        errors.append("contract schema_version must be 1")
    if contract.get("kind") != "browser_live_acceptance_contract":
        errors.append("contract kind is invalid")
    scope = contract.get("scope", {})
    if scope.get("browsers") != ["safari"]:
        errors.append("current acceptance scope must be Safari only")
    if scope.get("chrome_status") != "deferred_by_user":
        errors.append("Chrome must preserve the user-deferred status")
    if scope.get("safari_profile_model") != "shared_across_profiles":
        errors.append("Safari profile model must remain shared")
    gates = contract.get("gates", [])
    gate_ids = [row.get("id") for row in gates if isinstance(row, dict)]
    if gate_ids != EXPECTED_GATE_IDS:
        errors.append("acceptance gate IDs and order must remain stable")
    if any(not row.get("name") for row in gates if isinstance(row, dict)):
        errors.append("every acceptance gate requires a name")
    if set(contract.get("allowed_gate_statuses", [])) != ALLOWED_GATE_STATUSES:
        errors.append("allowed gate statuses are invalid")
    privacy = contract.get("privacy", {})
    if privacy.get("raw_export_persisted") is not False:
        errors.append("acceptance must not persist the raw export")
    if privacy.get("private_item_content_emitted") is not False:
        errors.append("acceptance must not emit private item content")
    if privacy.get("internal_safari_store_allowed") is not False:
        errors.append("the internal Safari store must remain prohibited")
    if contract.get("writes_performed") is not False:
        errors.append("acceptance contract must remain read-only")
    if contract.get("browser_writes_performed") is not False:
        errors.append("acceptance contract must not write Safari")
    if contract.get("execution_authorized") is not False:
        errors.append("acceptance contract must not authorize execution")
    try:
        example = _load_json(fixture, expected=dict)
        errors.extend(validate_document(example, "browser-acceptance"))
    except BrowserAcceptanceError as exc:
        errors.append(str(exc))
    return {
        "schema_version": 1,
        "status": "passed" if not errors else "failed",
        "gate_count": len(gates),
        "chrome_status": scope.get("chrome_status"),
        "writes_performed": False,
        "execution_authorized": False,
        "errors": errors,
    }


def _gate_rows(contract: Mapping[str, Any]) -> list[dict[str, str]]:
    return [
        {"id": row["id"], "status": "not_run", "reason": "not_run"}
        for row in contract["gates"]
    ]


def _set_gate(
    gates: list[dict[str, str]], gate_id: str, status: str, reason: str
) -> None:
    if status not in ALLOWED_GATE_STATUSES:
        raise BrowserAcceptanceError("invalid acceptance gate status")
    for row in gates:
        if row["id"] == gate_id:
            row.update(status=status, reason=reason)
            return
    raise BrowserAcceptanceError("unknown acceptance gate")


def _overall_status(gates: list[dict[str, str]]) -> str:
    statuses = {row["status"] for row in gates}
    if "failed" in statuses:
        return "failed"
    if statuses & {"deferred", "interface_limited", "not_run"}:
        return "partial"
    return "passed"


def _summary(
    *,
    captured_at: str,
    capability: Mapping[str, Any],
    gates: list[dict[str, str]],
    counts: Mapping[str, int | None],
) -> dict[str, Any]:
    safari = capability.get("safari", {})
    result = {
        "schema_version": 1,
        "kind": "browser_live_acceptance_summary",
        "captured_at": captured_at,
        "status": _overall_status(gates),
        "scope": {
            "browsers": ["safari"],
            "chrome_status": "deferred_by_user",
            "safari_profile_model": "shared_across_profiles",
        },
        "runtime": {
            "safari_present": bool(safari.get("present")),
            "safari_version": safari.get("version") if isinstance(safari.get("version"), str) else None,
            "safari_build": safari.get("build") if isinstance(safari.get("build"), str) else None,
        },
        "gates": gates,
        "counts": dict(counts),
        "privacy": {
            "provenance": "machine_observation",
            "storage_layer": "ephemeral_output",
            "contains_private_content": False,
            "git_allowed": False,
            "redaction_required": True,
        },
        "private_content_emitted": False,
        "writes_performed": False,
        "browser_writes_performed": False,
        "execution_authorized": False,
    }
    errors = validate_document(result, "browser-acceptance")
    if errors:
        raise BrowserAcceptanceError("generated browser acceptance summary is invalid")
    return result


def inspect_live(
    export: Path,
    *,
    capability: Mapping[str, Any] | None = None,
    ledger: Mapping[str, Any] | None = None,
    operations: list[dict[str, Any]] | None = None,
    post_export: Path | None = None,
    as_of: str | None = None,
    captured_at: str | None = None,
) -> dict[str, Any]:
    """Inspect one explicit export twice and emit aggregate acceptance only."""

    contract = _load_contract()
    observed = dict(capability or browser_sources.inspect_safari())
    captured = captured_at or dt.datetime.now(dt.timezone.utc).isoformat()
    review_date = as_of or captured[:10]
    gates = _gate_rows(contract)
    counts: dict[str, int | None] = {
        "bookmark_count": 0,
        "reading_list_count": 0,
        "queued_count": None,
        "suppressed_count": None,
        "planned_operation_count": None,
        "verified_operation_count": None,
        "failed_operation_count": None,
    }

    capability_ok = (
        observed.get("safari", {}).get("present") is True
        and observed.get("official_export", {}).get("support") == "supported_user_mediated"
        and observed.get("official_export", {}).get("content_read") is False
        and observed.get("private_item_content") == "not_read"
    )
    _set_gate(
        gates,
        "BA-01",
        "passed" if capability_ok else "failed",
        "supported_export_capability" if capability_ok else "capability_contract_mismatch",
    )
    _set_gate(
        gates,
        "BA-08",
        "interface_limited",
        "supported_item_write_interface_unavailable",
    )
    _set_gate(gates, "BA-10", "deferred", "deferred_by_user")

    try:
        first = parse_export(export)
        second = parse_export(export)
    except SafariExportError:
        _set_gate(gates, "BA-02", "failed", "explicit_export_invalid")
        return _summary(
            captured_at=captured,
            capability=observed,
            gates=gates,
            counts=counts,
        )

    counts["bookmark_count"] = first["bookmark_count"]
    counts["reading_list_count"] = first["reading_list_count"]
    _set_gate(gates, "BA-02", "passed", "explicit_export_valid")
    first_fingerprints = [item_fingerprint(item) for item in first["items"]]
    second_fingerprints = [item_fingerprint(item) for item in second["items"]]
    inventory_equal = (
        first["bookmark_count"] == second["bookmark_count"]
        and first["reading_list_count"] == second["reading_list_count"]
        and [row["item_id"] for row in first["items"]]
        == [row["item_id"] for row in second["items"]]
        and first_fingerprints == second_fingerprints
    )
    _set_gate(
        gates,
        "BA-03",
        "passed" if inventory_equal else "failed",
        "repeat_inventory_equal" if inventory_equal else "repeat_inventory_mismatch",
    )
    shared_boundary = all(
        row["source"]["browser"] == "safari"
        and row["source"]["profile_scope"] == "shared_across_profiles"
        and row["source"]["profile_ref"] is None
        and row["source"]["account_ref"] is None
        for row in first["items"]
    )
    _set_gate(
        gates,
        "BA-04",
        "passed" if shared_boundary else "failed",
        "shared_profile_boundary_preserved" if shared_boundary else "profile_boundary_mismatch",
    )

    try:
        reviewed_first = review_items(first["items"])
        reviewed_second = review_items(second["items"])
        review_equal = (
            redacted_summary(first, reviewed_first)
            == redacted_summary(second, reviewed_second)
            and [item_fingerprint(item) for item in reviewed_first["items"]]
            == [item_fingerprint(item) for item in reviewed_second["items"]]
            and reviewed_first["duplicate_groups"] == reviewed_second["duplicate_groups"]
        )
    except BrowserReviewError:
        review_equal = False
        reviewed_first = None
    _set_gate(
        gates,
        "BA-05",
        "passed" if review_equal else "failed",
        "repeat_review_equal" if review_equal else "repeat_review_mismatch",
    )

    if ledger is None:
        _set_gate(gates, "BA-06", "deferred", "decision_ledger_not_supplied")
    else:
        try:
            ledger_result = validate_ledger(ledger)
            if ledger_result["status"] != "passed" or reviewed_first is None:
                raise BrowserLifecycleError("browser decision ledger is invalid")
            queue_first = build_review_queue(
                reviewed_first["items"], ledger, as_of=review_date
            )
            queue_second = build_review_queue(
                reviewed_first["items"], ledger, as_of=review_date
            )
            if queue_first != queue_second:
                raise BrowserLifecycleError("browser decision queue is unstable")
            counts["queued_count"] = len(queue_first["queued"])
            counts["suppressed_count"] = len(queue_first["suppressed"])
            _set_gate(gates, "BA-06", "passed", "repeat_decision_memory_equal")
        except BrowserLifecycleError:
            _set_gate(gates, "BA-06", "failed", "decision_memory_invalid_or_unstable")

    plan: dict[str, Any] | None = None
    if operations is None:
        _set_gate(gates, "BA-07", "deferred", "operations_not_supplied")
    else:
        try:
            first_plan = build_plan(export, operations, created_at=captured)
            second_plan = build_plan(export, operations, created_at=captured)
            preflight = verify_preapply(first_plan, export)
            if first_plan != second_plan or preflight["status"] != "passed":
                raise BrowserTransactionError("browser plan is not deterministic")
            plan = first_plan
            counts["planned_operation_count"] = len(plan["operations"])
            _set_gate(gates, "BA-07", "passed", "repeat_plan_and_preapply_equal")
            blocked = apply_live_safari(plan, export)
            if blocked.get("status") != "blocked" or blocked.get("writes_performed") is not False:
                _set_gate(gates, "BA-08", "failed", "live_apply_boundary_failed")
        except (BrowserTransactionError, ValueError, KeyError):
            _set_gate(gates, "BA-07", "failed", "plan_or_preapply_invalid")

    if plan is None or post_export is None:
        reason = "plan_not_available" if plan is None and post_export is not None else "post_export_not_supplied"
        _set_gate(gates, "BA-09", "deferred", reason)
    else:
        verification = verify_post_export(plan, post_export)
        counts["verified_operation_count"] = verification.get("verified_operation_count")
        counts["failed_operation_count"] = verification.get("failed_operation_count")
        if verification["status"] == "passed":
            _set_gate(gates, "BA-09", "passed", "post_export_counts_match")
        else:
            _set_gate(gates, "BA-09", "failed", "post_export_mismatch")

    return _summary(
        captured_at=captured,
        capability=observed,
        gates=gates,
        counts=counts,
    )


def main(
    argv: list[str] | None = None,
    *,
    capability_provider: Callable[[], Mapping[str, Any]] = browser_sources.inspect_safari,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate the tracked BR-08 acceptance contract")
    live = subparsers.add_parser("inspect-live", help="inspect one explicit private Safari export")
    live.add_argument("export", type=Path)
    live.add_argument("--ledger", type=Path)
    live.add_argument("--operations", type=Path)
    live.add_argument("--post-export", type=Path)
    live.add_argument("--as-of")
    live.add_argument("--captured-at")
    args = parser.parse_args(argv)

    if args.command == "validate":
        result = validate_contract()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "passed" else 1
    try:
        ledger = _load_json(args.ledger, expected=dict) if args.ledger else None
        operations = _load_json(args.operations, expected=list) if args.operations else None
        result = inspect_live(
            args.export,
            capability=capability_provider(),
            ledger=ledger,
            operations=operations,
            post_export=args.post_export,
            as_of=args.as_of,
            captured_at=args.captured_at,
        )
    except BrowserAcceptanceError as exc:
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": "browser_live_acceptance_error",
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
    return 0 if result["status"] in {"passed", "partial"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
