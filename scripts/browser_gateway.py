#!/usr/bin/env python3
"""Validate, audit, and persist reviewed Safari knowledge-gateway waves."""

# Mutation action ID: browser.gateway-wave-sync

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Sequence
from urllib.parse import urlsplit

from schema_contract import SchemaContractError, load_json, validate_document
from transaction_contract import require_confirmation, transaction_metadata


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POLICY = ROOT / "settings" / "browser-gateway-policy.json"
PRIVATE_ROOT = ROOT / "Private"
ACTION_ID = "browser.gateway-wave-sync"
CONFIRMATION = "APPROVE BROWSER GATEWAY WAVE 1"
EXPECTED_CODES = {
    "11", "12", "13", "21", "22", "23", "31", "32", "33",
    "41", "42", "43", "51", "52", "53",
}


class BrowserGatewayError(RuntimeError):
    """Raised when a gateway policy or organization cannot be audited safely."""


def _canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _iso_date(value: str) -> dt.date:
    try:
        parsed = dt.date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise BrowserGatewayError("evidence_checked_on must be an ISO date") from exc
    if parsed.isoformat() != value:
        raise BrowserGatewayError("evidence_checked_on must be an ISO date")
    return parsed


def _host(url: str) -> str:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.hostname:
        raise BrowserGatewayError("new source and evidence URLs must use HTTPS")
    return parsed.hostname.lower().removeprefix("www.")


def _load_object(path: Path) -> dict[str, Any]:
    value = load_json(path)
    if not isinstance(value, dict):
        raise BrowserGatewayError("JSON input must be an object")
    return value


def policy_errors(policy: dict[str, Any]) -> list[str]:
    try:
        errors = list(validate_document(policy, "browser-gateway-policy"))
    except SchemaContractError as exc:
        return [str(exc)]
    if errors:
        return errors

    capacity = policy["capacity"]
    if not (
        capacity["minimum_active"]
        <= capacity["target_active"]
        <= capacity["maximum_active"]
    ):
        errors.append("active capacity must satisfy minimum <= target <= maximum")
    if capacity["core_slots"] + capacity["trial_slots"] != capacity["target_active"]:
        errors.append("core_slots plus trial_slots must equal target_active")

    rows = policy["subdomains"]
    codes = [row["code"] for row in rows]
    if len(codes) != len(set(codes)):
        errors.append("subdomain codes must be unique")
    if set(codes) != EXPECTED_CODES:
        errors.append("subdomain codes must match the fixed 15-domain taxonomy")
    for row in rows:
        if row["core_slots"] + row["trial_slots"] != row["total_slots"]:
            errors.append(f"{row['code']}: core_slots plus trial_slots must equal total_slots")
    if sum(row["core_slots"] for row in rows) != capacity["core_slots"]:
        errors.append("subdomain core slot sum must equal capacity.core_slots")
    if sum(row["trial_slots"] for row in rows) != capacity["trial_slots"]:
        errors.append("subdomain trial slot sum must equal capacity.trial_slots")
    if sum(row["total_slots"] for row in rows) != capacity["target_active"]:
        errors.append("subdomain total slot sum must equal capacity.target_active")
    if sum(policy["selection_score"]["weights"].values()) != 100:
        errors.append("selection score weights must sum to 100")
    if len(policy["source_mix"]) != len(set(policy["source_mix"])):
        errors.append("source_mix values must be unique")
    if len(policy["decisions"]) != len(set(policy["decisions"])):
        errors.append("decision values must be unique")
    return errors


def validate_policy(path: Path = DEFAULT_POLICY) -> dict[str, Any]:
    policy = _load_object(path)
    errors = policy_errors(policy)
    if errors:
        raise BrowserGatewayError("browser gateway policy is invalid: " + "; ".join(errors))
    return policy


def _target_code(decision: dict[str, Any]) -> str | None:
    target = decision.get("target_collection")
    if not isinstance(target, list) or not target:
        return None
    match = re.match(r"^([0-9]{2})", str(target[-1]))
    return match.group(1) if match else None


def audit_organization(
    organization: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    errors = policy_errors(policy)
    if errors:
        raise BrowserGatewayError("browser gateway policy is invalid: " + "; ".join(errors))
    try:
        organization_errors = validate_document(organization, "browser-organization")
    except SchemaContractError as exc:
        raise BrowserGatewayError(str(exc)) from exc
    if organization_errors:
        raise BrowserGatewayError("browser organization is invalid: " + "; ".join(organization_errors))
    if organization.get("execution_authorized") is not False:
        raise BrowserGatewayError("browser organization must not authorize execution")

    active = [
        decision
        for decision in organization["decisions"]
        if decision.get("item_type") == "bookmark" and decision.get("disposition") == "move"
    ]
    counts: Counter[str] = Counter()
    unknown = 0
    for decision in active:
        code = _target_code(decision)
        if code in EXPECTED_CODES:
            counts[code] += 1
        else:
            unknown += 1
    if unknown:
        raise BrowserGatewayError("active bookmark targets must use the fixed 15-domain taxonomy")

    rows = []
    retirement_review_count = 0
    new_source_capacity = 0
    retained_if_caps_applied = 0
    for quota in policy["subdomains"]:
        actual = counts[quota["code"]]
        retire = max(actual - quota["total_slots"], 0)
        add = max(quota["total_slots"] - actual, 0)
        retained = min(actual, quota["total_slots"])
        retirement_review_count += retire
        new_source_capacity += add
        retained_if_caps_applied += retained
        rows.append(
            {
                "code": quota["code"],
                "label": quota["label"],
                "priority": quota["priority"],
                "current_active": actual,
                "core_slots": quota["core_slots"],
                "trial_slots": quota["trial_slots"],
                "target_slots": quota["total_slots"],
                "retirement_review_count": retire,
                "new_source_capacity": add,
            }
        )

    capacity = policy["capacity"]
    active_count = len(active)
    reading_list_count = sum(
        1 for decision in organization["decisions"] if decision.get("item_type") == "reading_list"
    )
    return {
        "schema_version": 1,
        "kind": "browser_gateway_audit_summary",
        "status": "passed",
        "policy_version": policy["policy_version"],
        "current_active_bookmarks": active_count,
        "reading_list_items": reading_list_count,
        "target_minimum": capacity["minimum_active"],
        "target_active": capacity["target_active"],
        "target_maximum": capacity["maximum_active"],
        "current_over_target_count": max(active_count - capacity["target_active"], 0),
        "retirement_review_count": retirement_review_count,
        "retirement_review_percent": round((retirement_review_count / active_count * 100), 1) if active_count else 0.0,
        "retained_if_caps_applied": retained_if_caps_applied,
        "new_source_capacity": new_source_capacity,
        "over_quota_subdomain_count": sum(1 for row in rows if row["retirement_review_count"]),
        "empty_subdomain_count": sum(1 for row in rows if row["current_active"] == 0),
        "priority_subdomain_count": sum(1 for row in rows if row["priority"]),
        "subdomains": rows,
        "private_content_emitted": False,
        "writes": False,
        "execution_authorized": False,
    }


def build_wave(
    organization: dict[str, Any],
    spec: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    audit = audit_organization(organization, policy)
    if set(spec) != {"wave_id", "created_at", "proposals"}:
        raise BrowserGatewayError("wave spec fields are invalid")
    if not re.fullmatch(r"bgw_[A-Za-z0-9_-]{8,}", str(spec["wave_id"])):
        raise BrowserGatewayError("wave_id is invalid")
    created = _iso_date(str(spec["created_at"]))
    proposals = spec.get("proposals")
    if not isinstance(proposals, list) or not proposals:
        raise BrowserGatewayError("wave proposals must be a non-empty list")

    active = {
        row["item_id"]: row
        for row in organization["decisions"]
        if row.get("item_type") == "bookmark" and row.get("disposition") == "move"
    }
    active_hosts: dict[str, set[str]] = {}
    for item_id, row in active.items():
        parsed = urlsplit(row["original_url"])
        if parsed.hostname:
            active_hosts.setdefault(parsed.hostname.lower().removeprefix("www."), set()).add(item_id)

    used_retirements: set[str] = set()
    used_new_urls: set[str] = set()
    compiled = []
    proposal_ids: set[str] = set()
    for proposal in proposals:
        if not isinstance(proposal, dict) or set(proposal) != {
            "proposal_id", "subdomain_code", "new_source", "retirements"
        }:
            raise BrowserGatewayError("proposal fields are invalid")
        proposal_id = str(proposal["proposal_id"])
        if not re.fullmatch(r"bgp_[A-Za-z0-9_-]{8,}", proposal_id) or proposal_id in proposal_ids:
            raise BrowserGatewayError("proposal_id is invalid or duplicated")
        proposal_ids.add(proposal_id)
        code = str(proposal["subdomain_code"])
        if code not in EXPECTED_CODES:
            raise BrowserGatewayError("proposal subdomain is invalid")
        new_source = proposal["new_source"]
        if not isinstance(new_source, dict) or set(new_source) != {
            "title", "url", "operator", "source_type", "evidence_url", "evidence_checked_on"
        }:
            raise BrowserGatewayError("new source fields are invalid")
        if new_source["source_type"] not in policy["source_mix"]:
            raise BrowserGatewayError("new source type is invalid")
        new_host = _host(str(new_source["url"]))
        _host(str(new_source["evidence_url"]))
        checked = _iso_date(str(new_source["evidence_checked_on"]))
        age = (created - checked).days
        if age < 0 or age > policy["renewal"]["source_recency_days"]:
            raise BrowserGatewayError("new source evidence is outside the recency window")
        if new_source["url"] in used_new_urls:
            raise BrowserGatewayError("new source URLs must be unique")
        used_new_urls.add(new_source["url"])

        retirement_specs = proposal["retirements"]
        minimum = (
            policy["renewal"]["above_target_retirements_per_new"]
            if audit["current_active_bookmarks"] > policy["capacity"]["target_active"]
            else 1
        )
        if not isinstance(retirement_specs, list) or len(retirement_specs) < minimum:
            raise BrowserGatewayError("proposal does not satisfy the retirement ratio")
        retirement_rows = []
        for retirement in retirement_specs:
            if not isinstance(retirement, dict) or set(retirement) != {"item_id", "decision"}:
                raise BrowserGatewayError("retirement fields are invalid")
            item_id = str(retirement["item_id"])
            decision = str(retirement["decision"])
            if decision not in {"replace_by", "promote_to_obsidian", "archive", "delete"}:
                raise BrowserGatewayError("retirement decision is invalid")
            if item_id in used_retirements or item_id not in active:
                raise BrowserGatewayError("retirement item is missing, inactive, or duplicated")
            used_retirements.add(item_id)
            source = active[item_id]
            retirement_rows.append(
                {
                    "item_id": item_id,
                    "item_fingerprint": source["item_fingerprint"],
                    "original_title": source["original_title"],
                    "original_url": source["original_url"],
                    "original_subdomain_code": _target_code(source),
                    "decision": decision,
                }
            )
        same_host_items = active_hosts.get(new_host, set())
        if same_host_items and not same_host_items.issubset(used_retirements):
            raise BrowserGatewayError("existing same-host sources must be retired in the approved wave")
        compiled.append(
            {
                "proposal_id": proposal_id,
                "subdomain_code": code,
                "new_source": {**new_source, "decision": "trial_new"},
                "retirements": retirement_rows,
                "review_status": "approved",
                "execution_authorized": False,
            }
        )

    retirement_count = sum(len(row["retirements"]) for row in compiled)
    document = {
        "schema_version": 1,
        "kind": "browser_gateway_wave",
        "wave_id": spec["wave_id"],
        "created_at": spec["created_at"],
        "policy_version": policy["policy_version"],
        "source": {
            "organization_id": organization["organization_id"],
            "artifact_sha256": organization["source"]["artifact_sha256"],
            "active_bookmark_count": audit["current_active_bookmarks"],
        },
        "proposals": compiled,
        "summary": {
            "new_source_count": len(compiled),
            "retirement_count": retirement_count,
            "projected_active_count": audit["current_active_bookmarks"] - retirement_count + len(compiled),
            "minimum_retirements_per_new": minimum,
            "private_content_emitted_to_stdout": False,
        },
        "privacy": {
            "provenance": "private_user_data",
            "storage_layer": "private_icloud",
            "contains_private_content": True,
            "git_allowed": False,
            "redaction_required": True,
        },
        "safari_execution_authorized": False,
        "execution_authorized": False,
    }
    errors = validate_document(document, "browser-gateway-wave")
    if errors:
        raise BrowserGatewayError("compiled gateway wave is invalid: " + "; ".join(errors))
    return document


def _wave_summary(document: dict[str, Any], *, status: str, writes: bool) -> dict[str, Any]:
    by_domain = Counter(row["subdomain_code"] for row in document["proposals"])
    return {
        "schema_version": 1,
        "kind": "browser_gateway_wave_summary",
        "action_id": ACTION_ID,
        "status": status,
        "new_source_count": document["summary"]["new_source_count"],
        "retirement_count": document["summary"]["retirement_count"],
        "projected_active_count": document["summary"]["projected_active_count"],
        "subdomains": [{"code": code, "new_source_count": by_domain[code]} for code in sorted(by_domain)],
        "output_layer": "private_icloud",
        "private_content_emitted": False,
        "writes_performed": writes,
        "browser_writes_performed": False,
        "execution_authorized": False,
    }


def plan_wave(document: dict[str, Any]) -> dict[str, Any]:
    errors = validate_document(document, "browser-gateway-wave")
    if errors:
        raise BrowserGatewayError("browser gateway wave is invalid: " + "; ".join(errors))
    if document.get("execution_authorized") is not False or document.get("safari_execution_authorized") is not False:
        raise BrowserGatewayError("browser gateway wave must remain non-executable")
    decisions = Counter(
        retirement["decision"]
        for proposal in document["proposals"]
        for retirement in proposal["retirements"]
    )
    return {
        "schema_version": 1,
        "kind": "browser_gateway_migration_plan_summary",
        "status": "blocked",
        "reason": "supported_item_write_interface_unavailable",
        "new_source_count": document["summary"]["new_source_count"],
        "retirement_count": document["summary"]["retirement_count"],
        "projected_active_count": document["summary"]["projected_active_count"],
        "retirement_decisions": [
            {"decision": decision, "count": decisions[decision]}
            for decision in ["delete", "archive", "promote_to_obsidian", "replace_by"]
        ],
        "manual_handoff_only": True,
        "private_content_emitted": False,
        "writes_performed": False,
        "browser_writes_performed": False,
        "execution_authorized": False,
    }


def sync_wave(
    organization_path: Path,
    spec_path: Path,
    output: Path,
    *,
    policy: dict[str, Any],
    apply: bool,
    confirmation: str,
    root: Path = ROOT,
    private_root: Path = PRIVATE_ROOT,
) -> dict[str, Any]:
    document = build_wave(_load_object(organization_path), _load_object(spec_path), policy)
    payload = _canonical_bytes(document)
    destination = output.expanduser().resolve(strict=False)
    allowed = (private_root / "browser" / "gateway").resolve(strict=False)
    if destination.parent != allowed or not re.fullmatch(r"wave-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}\.json", destination.name):
        raise BrowserGatewayError("gateway wave output must use the approved Private path and name")
    ignored = subprocess.run(
        ["git", "-C", str(root), "check-ignore", "-q", "--", str(destination)],
        capture_output=True,
        text=True,
        check=False,
    )
    if ignored.returncode != 0:
        raise BrowserGatewayError("gateway wave output must be ignored by Git")
    if not apply:
        return _wave_summary(document, status="preview", writes=False)
    require_confirmation(ACTION_ID, confirmation)
    writes = False
    if destination.exists():
        if destination.is_symlink() or not destination.is_file() or destination.read_bytes() != payload:
            raise BrowserGatewayError("refusing to overwrite a different gateway wave")
        status = "unchanged"
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=destination.parent, prefix=".browser-gateway-", delete=False
            ) as handle:
                temporary = Path(handle.name)
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, destination)
        except OSError as exc:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            raise BrowserGatewayError("failed to write gateway wave") from exc
        status = "written"
        writes = True
    if destination.stat().st_mode & 0o777 != 0o600:
        os.chmod(destination, 0o600)
        writes = True
    verified = _load_object(destination)
    if _canonical_bytes(verified) != payload or validate_document(verified, "browser-gateway-wave"):
        raise BrowserGatewayError("gateway wave failed read-back validation")
    transaction_metadata(ACTION_ID, phase="record", status=status, targets=[destination.name])
    return _wave_summary(verified, status=status, writes=writes)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate-policy")
    validate.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    audit = subparsers.add_parser("audit-organization")
    audit.add_argument("organization", type=Path)
    audit.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    sync = subparsers.add_parser("sync-wave")
    sync.add_argument("organization", type=Path)
    sync.add_argument("--spec", type=Path, required=True)
    sync.add_argument("--output", type=Path, required=True)
    sync.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    sync.add_argument("--apply", action="store_true")
    sync.add_argument("--confirm", default="")
    plan = subparsers.add_parser("plan-wave")
    plan.add_argument("wave", type=Path)
    plan.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        policy = validate_policy(args.policy)
        if args.command == "validate-policy":
            result = {
                "schema_version": 1,
                "status": "passed",
                "kind": "browser_gateway_policy_validation",
                "target_active": policy["capacity"]["target_active"],
                "core_slots": policy["capacity"]["core_slots"],
                "trial_slots": policy["capacity"]["trial_slots"],
                "subdomain_count": len(policy["subdomains"]),
                "execution_authorized": False,
            }
        elif args.command == "audit-organization":
            result = audit_organization(_load_object(args.organization), policy)
        elif args.command == "sync-wave":
            result = sync_wave(
                args.organization,
                args.spec,
                args.output,
                policy=policy,
                apply=args.apply,
                confirmation=args.confirm,
            )
        else:
            result = plan_wave(_load_object(args.wave))
    except (BrowserGatewayError, OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"schema_version": 1, "status": "failed", "error": str(exc)}), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
