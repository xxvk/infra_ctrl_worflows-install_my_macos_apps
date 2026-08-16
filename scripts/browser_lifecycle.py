#!/usr/bin/env python3
"""Classify private browser items and suppress unchanged reviewed items."""

from __future__ import annotations

import argparse
import copy
import datetime as dt
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

from browser_review import BrowserReviewError, review_items
from safari_export import SafariExportError, parse_export
from schema_contract import SchemaContractError, load_and_validate, validate_document


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "settings" / "browser-lifecycle-policy.json"
BUILTIN_CLASSIFICATIONS = ["inbox", "project", "reference", "read_later", "archive"]
FINGERPRINT_FIELDS = [
    "source.browser",
    "source.profile_scope",
    "source.profile_ref",
    "source.account_ref",
    "item_type",
    "url.comparison",
    "title",
    "collection.kind",
    "collection.path",
    "tags",
    "read_state",
]


class BrowserLifecycleError(RuntimeError):
    """A privacy-safe browser lifecycle failure."""


def _parse_datetime(value: str) -> dt.datetime:
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise BrowserLifecycleError("decision timestamp must be ISO 8601") from exc
    if parsed.tzinfo is None:
        raise BrowserLifecycleError("decision timestamp must include a time zone")
    return parsed


def _parse_date(value: str) -> dt.date:
    try:
        return dt.date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise BrowserLifecycleError("review date must be an ISO date") from exc


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    try:
        policy = load_and_validate(path, "browser-lifecycle-policy")
    except SchemaContractError as exc:
        raise BrowserLifecycleError("browser lifecycle policy is invalid") from exc
    errors = _policy_errors(policy)
    if errors:
        raise BrowserLifecycleError("browser lifecycle policy is invalid")
    return policy


def _policy_errors(policy: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    ids = [row.get("id") for row in policy.get("builtin_classifications", [])]
    if ids != BUILTIN_CLASSIFICATIONS:
        errors.append("builtin classification order and membership must remain stable")
    if policy.get("fingerprint_fields") != FINGERPRINT_FIELDS:
        errors.append("private fingerprint fields must remain explicit and stable")
    if policy.get("cross_identity_memory") is not False:
        errors.append("cross-identity memory must remain disabled")
    if policy.get("execution_authorized") is not False:
        errors.append("browser lifecycle policy must not authorize execution")
    custom = policy.get("custom_classifications", {})
    if any(
        not isinstance(row.get("default_review_days"), int)
        or row["default_review_days"] > 3650
        for row in policy.get("builtin_classifications", [])
    ):
        errors.append("builtin review periods must not exceed 3650 days")
    if custom.get("max_definitions", 0) > 1000:
        errors.append("custom classification limit must not exceed 1000")
    if custom.get("default_review_days", 0) > 3650 or custom.get("max_review_days", 0) > 3650:
        errors.append("custom review periods must not exceed 3650 days")
    if custom.get("default_review_days", 0) > custom.get("max_review_days", 0):
        errors.append("custom default review period exceeds the maximum")
    return errors


def validate_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    try:
        policy = load_and_validate(path, "browser-lifecycle-policy")
        errors = _policy_errors(policy)
    except SchemaContractError:
        policy = {}
        errors = ["browser lifecycle policy is invalid"]
    return {
        "schema_version": 1,
        "status": "passed" if not errors else "failed",
        "policy_version": policy.get("policy_version"),
        "builtin_classifications": [
            row.get("id") for row in policy.get("builtin_classifications", [])
        ],
        "custom_classifications_enabled": bool(
            policy.get("custom_classifications", {}).get("enabled")
        ),
        "cross_identity_memory": False,
        "execution_authorized": False,
        "errors": errors,
    }


def _identity_boundary(item: Mapping[str, Any]) -> dict[str, Any]:
    source = item["source"]
    return {
        "browser": source["browser"],
        "profile_scope": source["profile_scope"],
        "profile_ref": source["profile_ref"],
        "account_ref": source["account_ref"],
    }


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _validate_item(item: Mapping[str, Any]) -> None:
    errors = validate_document(dict(item), "browser-item")
    if errors:
        raise BrowserLifecycleError("browser item failed schema validation")


def item_fingerprint(item: Mapping[str, Any]) -> str:
    """Hash private semantic content; the result must never enter public output."""

    _validate_item(item)
    url = item["url"]
    comparison_url = (
        url["canonical"]
        if url.get("canonicalization_status") in {"proposed", "confirmed"}
        and url.get("canonical")
        else url["original"]
    )
    payload = {
        "identity_boundary": _identity_boundary(item),
        "item_type": item["item_type"],
        "comparison_url": comparison_url,
        "title": item["title"],
        "collection": {
            "kind": item["collection"]["kind"],
            "path": item["collection"]["path"],
        },
        "tags": sorted(item["tags"]),
        "read_state": item["read_state"],
    }
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


def _ledger_errors(ledger: Mapping[str, Any], policy: Mapping[str, Any]) -> list[str]:
    errors = validate_document(dict(ledger), "browser-decision-ledger")
    if errors:
        return ["browser decision ledger failed schema validation"]

    custom_rows = ledger.get("custom_classifications", [])
    max_definitions = policy["custom_classifications"]["max_definitions"]
    if len(custom_rows) > max_definitions:
        errors.append("custom classification limit exceeded")
    custom_ids = [row["classification_id"] for row in custom_rows]
    if len(custom_ids) != len(set(custom_ids)):
        errors.append("custom classification IDs must be unique")
    labels = [row["label"].casefold() for row in custom_rows]
    if len(labels) != len(set(labels)):
        errors.append("custom classification labels must be unique")
    if any(
        row["review_days"] > policy["custom_classifications"]["max_review_days"]
        for row in custom_rows
    ):
        errors.append("custom review period exceeds policy maximum")

    known = set(BUILTIN_CLASSIFICATIONS) | set(custom_ids)
    decision_ids: set[str] = set()
    active_keys: set[tuple[str, str]] = set()
    for row in ledger.get("decisions", []):
        if row["decision_id"] in decision_ids:
            errors.append("decision IDs must be unique")
        decision_ids.add(row["decision_id"])
        if row["classification_id"] not in known:
            errors.append("decision references an unknown classification")
        try:
            decided = _parse_datetime(row["decided_at"])
            review = _parse_date(row["review_after"])
            if review <= decided.date():
                errors.append("review date must be after the decision date")
        except BrowserLifecycleError as exc:
            errors.append(str(exc))
        if row["status"] == "active":
            boundary_key = hashlib.sha256(
                _canonical_json(row["identity_boundary"])
            ).hexdigest()
            key = (row["item_id"], boundary_key)
            if key in active_keys:
                errors.append("only one active decision is allowed per item and identity")
            active_keys.add(key)
    return errors


def validate_ledger(
    ledger: Mapping[str, Any], *, policy: Mapping[str, Any] | None = None
) -> dict[str, Any]:
    selected = dict(policy or load_policy())
    errors = _ledger_errors(ledger, selected)
    return {
        "schema_version": 1,
        "kind": "browser_history_redacted_summary",
        "status": "passed" if not errors else "failed",
        "custom_classification_count": len(ledger.get("custom_classifications", [])),
        "decision_count": len(ledger.get("decisions", [])),
        "active_decision_count": sum(
            row.get("status") == "active" for row in ledger.get("decisions", [])
        ),
        "private_content_emitted": False,
        "execution_authorized": False,
        "errors": errors,
    }


def _load_ledger(path: Path, *, policy: Mapping[str, Any]) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BrowserLifecycleError("browser decision ledger is unavailable or invalid") from exc
    if not isinstance(value, dict) or _ledger_errors(value, policy):
        raise BrowserLifecycleError("browser decision ledger is unavailable or invalid")
    return value


def _classification_review_days(
    classification_id: str,
    *,
    policy: Mapping[str, Any],
    ledger: Mapping[str, Any],
) -> int:
    builtins = {
        row["id"]: row["default_review_days"]
        for row in policy["builtin_classifications"]
    }
    if classification_id in builtins:
        return int(builtins[classification_id])
    custom = {
        row["classification_id"]: row
        for row in ledger.get("custom_classifications", [])
    }.get(classification_id)
    if not custom or custom["status"] != "active":
        raise BrowserLifecycleError("classification is unknown or retired")
    return int(custom["review_days"])


def build_decision(
    item: Mapping[str, Any],
    classification_id: str,
    *,
    ledger: Mapping[str, Any],
    decided_at: str,
    review_after: str | None = None,
    note: str | None = None,
    policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    selected = dict(policy or load_policy())
    if _ledger_errors(ledger, selected):
        raise BrowserLifecycleError("browser decision ledger is invalid")
    _validate_item(item)
    decided = _parse_datetime(decided_at)
    days = _classification_review_days(
        classification_id, policy=selected, ledger=ledger
    )
    review = _parse_date(review_after) if review_after else decided.date() + dt.timedelta(days=days)
    if review <= decided.date():
        raise BrowserLifecycleError("review date must be after the decision date")
    fingerprint = item_fingerprint(item)
    seed = {
        "item_id": item["item_id"],
        "fingerprint": fingerprint,
        "classification_id": classification_id,
        "decided_at": decided_at,
    }
    return {
        "decision_id": "bdd_" + hashlib.sha256(_canonical_json(seed)).hexdigest()[:24],
        "item_id": item["item_id"],
        "identity_boundary": _identity_boundary(item),
        "item_fingerprint": fingerprint,
        "classification_id": classification_id,
        "decided_at": decided_at,
        "review_after": review.isoformat(),
        "status": "active",
        "note": note,
        "execution_authorized": False,
    }


def record_decision(
    ledger: Mapping[str, Any],
    decision: Mapping[str, Any],
    *,
    policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Return an updated private ledger in memory; never write it to disk."""

    selected = dict(policy or load_policy())
    if _ledger_errors(ledger, selected):
        raise BrowserLifecycleError("browser decision ledger is invalid")
    updated = copy.deepcopy(dict(ledger))
    if any(
        row["decision_id"] == decision.get("decision_id")
        for row in updated["decisions"]
    ):
        raise BrowserLifecycleError("decision already exists")
    for row in updated["decisions"]:
        if (
            row["status"] == "active"
            and row["item_id"] == decision.get("item_id")
            and row["identity_boundary"] == decision.get("identity_boundary")
        ):
            row["status"] = "superseded"
    updated["decisions"].append(copy.deepcopy(dict(decision)))
    updated["updated_at"] = str(decision.get("decided_at"))
    if _ledger_errors(updated, selected):
        raise BrowserLifecycleError("new decision would make the ledger invalid")
    return updated


def _effect(row: Mapping[str, Any], as_of: dt.date) -> tuple[str, str]:
    if _parse_date(row["review_after"]) <= as_of:
        return "queued", "review_due"
    return "suppressed", "review_not_due"


def build_review_queue(
    items: list[dict[str, Any]],
    ledger: Mapping[str, Any],
    *,
    as_of: str,
    policy: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    selected = dict(policy or load_policy())
    if _ledger_errors(ledger, selected):
        raise BrowserLifecycleError("browser decision ledger is invalid")
    current = _parse_date(as_of)
    active = [row for row in ledger["decisions"] if row["status"] == "active"]
    queued: list[dict[str, Any]] = []
    suppressed: list[dict[str, Any]] = []

    for item in items:
        _validate_item(item)
        boundary = _identity_boundary(item)
        fingerprint = item_fingerprint(item)
        exact = [
            row
            for row in active
            if row["item_id"] == item["item_id"]
            and row["identity_boundary"] == boundary
        ]
        if exact:
            row = exact[0]
            if row["item_fingerprint"] != fingerprint:
                queued.append({"item_id": item["item_id"], "reason": "item_changed"})
                continue
            disposition, reason = _effect(row, current)
            target = suppressed if disposition == "suppressed" else queued
            target.append({"item_id": item["item_id"], "reason": reason})
            continue

        remembered = [
            row
            for row in active
            if row["item_fingerprint"] == fingerprint
            and row["identity_boundary"] == boundary
        ]
        if len(remembered) > 1:
            queued.append({"item_id": item["item_id"], "reason": "ambiguous_memory"})
        elif len(remembered) == 1:
            disposition, reason = _effect(remembered[0], current)
            target = suppressed if disposition == "suppressed" else queued
            target.append({"item_id": item["item_id"], "reason": reason})
        else:
            queued.append({"item_id": item["item_id"], "reason": "unreviewed"})

    return {
        "schema_version": 1,
        "kind": "browser_review_queue",
        "as_of": as_of,
        "queued": queued,
        "suppressed": suppressed,
        "writes_performed": False,
        "execution_authorized": False,
    }


def _redacted_queue_summary(queue: Mapping[str, Any]) -> dict[str, Any]:
    reasons = Counter(row["reason"] for row in queue["queued"])
    return {
        "schema_version": 1,
        "kind": "browser_lifecycle_redacted_summary",
        "status": "passed",
        "queued_count": len(queue["queued"]),
        "suppressed_count": len(queue["suppressed"]),
        "queue_reason_counts": dict(sorted(reasons.items())),
        "private_content_emitted": False,
        "writes_performed": False,
        "execution_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate-policy", help="validate the public lifecycle policy")
    ledger_parser = subparsers.add_parser(
        "inspect-ledger", help="validate an explicit private ledger and emit counts"
    )
    ledger_parser.add_argument("ledger", type=Path)
    review_parser = subparsers.add_parser(
        "review-safari-export",
        help="compare one explicit Safari export with an explicit private ledger",
    )
    review_parser.add_argument("export", type=Path)
    review_parser.add_argument("--ledger", required=True, type=Path)
    review_parser.add_argument("--as-of", required=True)
    args = parser.parse_args(argv)

    if args.command == "validate-policy":
        result = validate_policy()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "passed" else 1

    try:
        policy = load_policy()
        ledger = _load_ledger(args.ledger, policy=policy)
        if args.command == "inspect-ledger":
            result = validate_ledger(ledger, policy=policy)
        else:
            parsed = parse_export(args.export)
            normalized = review_items(parsed["items"])
            queue = build_review_queue(
                normalized["items"], ledger, as_of=args.as_of, policy=policy
            )
            result = _redacted_queue_summary(queue)
    except (BrowserLifecycleError, BrowserReviewError, SafariExportError) as exc:
        summary_kind = (
            "browser_history_redacted_summary"
            if args.command == "inspect-ledger"
            else "browser_lifecycle_redacted_summary"
        )
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
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
