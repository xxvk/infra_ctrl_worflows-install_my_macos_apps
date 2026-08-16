#!/usr/bin/env python3
"""Freeze and verify a manual Safari Browser Gateway pilot."""

# Mutation action ID: browser.gateway-pilot-freeze

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

from safari_export import SafariExportError, parse_export
from schema_contract import SchemaContractError, load_json, validate_document
from transaction_contract import require_confirmation, transaction_metadata


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / "Private"
ACTION_ID = "browser.gateway-pilot-freeze"
CONFIRMATION = "FREEZE BROWSER GATEWAY PILOT 1"
TEMPORARY_COLLECTION = ["98｜Wave 1 待删除（验证后清除）"]
EXPECTED_GROUP_IDS = {f"A{index}" for index in range(1, 6)} | {
    f"B{index}" for index in range(1, 6)
}
CHECKPOINTS = {
    "batch-1": {
        "bookmark_count": 316,
        "reading_list_count": 89,
        "conceptual_active_count": 277,
        "new_source_count": 5,
        "archive_count": 2,
        "staged_count": 8,
        "purged_count": 0,
    },
    "batch-2": {
        "bookmark_count": 321,
        "reading_list_count": 89,
        "conceptual_active_count": 272,
        "new_source_count": 10,
        "archive_count": 4,
        "staged_count": 16,
        "purged_count": 0,
    },
    "purge": {
        "bookmark_count": 305,
        "reading_list_count": 89,
        "conceptual_active_count": 272,
        "new_source_count": 10,
        "archive_count": 4,
        "staged_count": 0,
        "purged_count": 16,
    },
}


class BrowserGatewayPilotError(RuntimeError):
    """Raised when a pilot cannot be frozen or verified safely."""


def _canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_object(path: Path) -> dict[str, Any]:
    value = load_json(path)
    if not isinstance(value, dict):
        raise BrowserGatewayPilotError("JSON input must be an object")
    return value


def _iso_date(value: str) -> dt.date:
    try:
        parsed = dt.date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise BrowserGatewayPilotError("created_at must be an ISO date") from exc
    if parsed.isoformat() != value:
        raise BrowserGatewayPilotError("created_at must be an ISO date")
    return parsed


def _validate_inputs(
    organization: dict[str, Any], wave: dict[str, Any], spec: dict[str, Any]
) -> None:
    organization_errors = validate_document(organization, "browser-organization")
    wave_errors = validate_document(wave, "browser-gateway-wave")
    if organization_errors:
        raise BrowserGatewayPilotError("browser organization is invalid")
    if wave_errors:
        raise BrowserGatewayPilotError("browser gateway wave is invalid")
    if organization.get("execution_authorized") is not False:
        raise BrowserGatewayPilotError("organization must remain non-executable")
    if wave.get("execution_authorized") is not False or wave.get("safari_execution_authorized") is not False:
        raise BrowserGatewayPilotError("superseded wave must remain non-executable")
    if wave["source"]["organization_id"] != organization["organization_id"]:
        raise BrowserGatewayPilotError("wave does not bind the organization")
    if wave["source"]["artifact_sha256"] != organization["source"]["artifact_sha256"]:
        raise BrowserGatewayPilotError("wave and organization source hashes differ")
    if set(spec) != {"pilot_id", "created_at", "groups", "required_directories"}:
        raise BrowserGatewayPilotError("pilot spec fields are invalid")
    if not re.fullmatch(r"bgpilot_[A-Za-z0-9_-]{8,}", str(spec["pilot_id"])):
        raise BrowserGatewayPilotError("pilot_id is invalid")
    _iso_date(str(spec["created_at"]))


def build_pilot(
    organization: dict[str, Any], wave: dict[str, Any], spec: dict[str, Any]
) -> dict[str, Any]:
    """Compile a final manual-execution ledger from an immutable approved wave."""

    _validate_inputs(organization, wave, spec)
    wave_proposals = {row["proposal_id"]: row for row in wave["proposals"]}
    organization_items = {row["item_id"]: row for row in organization["decisions"]}
    groups = spec["groups"]
    if not isinstance(groups, list) or len(groups) != 10:
        raise BrowserGatewayPilotError("pilot must contain exactly 10 exchange groups")
    if {str(row.get("group_id")) for row in groups if isinstance(row, dict)} != EXPECTED_GROUP_IDS:
        raise BrowserGatewayPilotError("pilot group IDs must be A1-A5 and B1-B5")
    if {str(row.get("proposal_id")) for row in groups if isinstance(row, dict)} != set(wave_proposals):
        raise BrowserGatewayPilotError("pilot must supersede every old wave proposal exactly once")

    compiled: list[dict[str, Any]] = []
    used_retirements: set[str] = set()
    for row in groups:
        if not isinstance(row, dict) or set(row) != {
            "group_id", "batch", "proposal_id", "title", "target_collection", "retirements"
        }:
            raise BrowserGatewayPilotError("pilot group fields are invalid")
        group_id = str(row["group_id"])
        expected_batch = "batch-1" if group_id.startswith("A") else "batch-2"
        if row["batch"] != expected_batch:
            raise BrowserGatewayPilotError("group is assigned to the wrong batch")
        proposal = wave_proposals[str(row["proposal_id"])]
        target = row["target_collection"]
        if not isinstance(target, list) or len(target) != 2 or not all(isinstance(v, str) and v for v in target):
            raise BrowserGatewayPilotError("new-source target must be a two-level collection")
        if not str(target[-1]).startswith(proposal["subdomain_code"] + "｜"):
            raise BrowserGatewayPilotError("new-source target does not match its subdomain")
        action_specs = row["retirements"]
        proposal_retirements = {item["item_id"]: item for item in proposal["retirements"]}
        if not isinstance(action_specs, list) or {
            str(item.get("item_id")) for item in action_specs if isinstance(item, dict)
        } != set(proposal_retirements):
            raise BrowserGatewayPilotError("group retirement manifest differs from the approved wave")
        retirements = []
        for action_spec in action_specs:
            allowed_fields = {"item_id", "action", "target_collection", "knowledge_note_required"}
            if not isinstance(action_spec, dict) or set(action_spec) != allowed_fields:
                raise BrowserGatewayPilotError("retirement action fields are invalid")
            item_id = str(action_spec["item_id"])
            if item_id in used_retirements:
                raise BrowserGatewayPilotError("retirement item is duplicated")
            used_retirements.add(item_id)
            action = action_spec["action"]
            if action not in {"archive", "stage_for_purge", "promote_then_stage"}:
                raise BrowserGatewayPilotError("retirement action is invalid")
            target_collection = action_spec["target_collection"]
            if action == "archive":
                if not isinstance(target_collection, list) or len(target_collection) != 2:
                    raise BrowserGatewayPilotError("archive action requires a two-level target")
            elif target_collection != TEMPORARY_COLLECTION:
                raise BrowserGatewayPilotError("staged actions must use the fixed temporary collection")
            note_required = action_spec["knowledge_note_required"]
            if not isinstance(note_required, bool) or (action == "promote_then_stage") != note_required:
                raise BrowserGatewayPilotError("knowledge-note prerequisite is inconsistent")
            old = proposal_retirements[item_id]
            source = organization_items.get(item_id)
            if source is None or source["item_fingerprint"] != old["item_fingerprint"]:
                raise BrowserGatewayPilotError("retirement source binding drifted")
            retirements.append(
                {
                    "item_id": item_id,
                    "item_fingerprint": old["item_fingerprint"],
                    "original_title": old["original_title"],
                    "original_url": old["original_url"],
                    "source_collection": source["source_collection"],
                    "superseded_decision": old["decision"],
                    "action": action,
                    "target_collection": target_collection,
                    "knowledge_note_required": note_required,
                    "execution_authorized": False,
                }
            )
        compiled.append(
            {
                "group_id": group_id,
                "batch": expected_batch,
                "proposal_id": proposal["proposal_id"],
                "subdomain_code": proposal["subdomain_code"],
                "new_source": {
                    **proposal["new_source"],
                    "title": row["title"],
                    "target_collection": target,
                    "review_after_days": 45,
                },
                "retirements": retirements,
                "execution_authorized": False,
            }
        )

    compiled.sort(key=lambda item: item["group_id"])
    action_counts = Counter(
        retirement["action"] for group in compiled for retirement in group["retirements"]
    )
    batch_counts = Counter(group["batch"] for group in compiled)
    if action_counts != Counter({"stage_for_purge": 15, "archive": 4, "promote_then_stage": 1}):
        raise BrowserGatewayPilotError("pilot must contain 4 archives and 16 staged removals")
    if batch_counts != Counter({"batch-1": 5, "batch-2": 5}):
        raise BrowserGatewayPilotError("pilot must contain five groups per batch")
    directories = spec["required_directories"]
    if not isinstance(directories, list) or TEMPORARY_COLLECTION not in directories:
        raise BrowserGatewayPilotError("required directories must include the temporary collection")

    document = {
        "schema_version": 1,
        "kind": "browser_gateway_pilot",
        "pilot_id": spec["pilot_id"],
        "created_at": spec["created_at"],
        "source": {
            "organization_id": organization["organization_id"],
            "organization_artifact_sha256": organization["source"]["artifact_sha256"],
            "supersedes_wave_id": wave["wave_id"],
            "supersedes_wave_sha256": _sha256(_canonical_bytes(wave)),
            "baseline_export_sha256": organization["source"]["artifact_sha256"],
            "baseline_bookmark_count": organization["source"]["bookmark_count"],
            "baseline_reading_list_count": organization["source"]["reading_list_count"],
        },
        "required_directories": directories,
        "temporary_collection": TEMPORARY_COLLECTION,
        "groups": compiled,
        "checkpoints": [
            {"checkpoint": name, **values} for name, values in CHECKPOINTS.items()
        ],
        "summary": {
            "group_count": 10,
            "new_source_count": 10,
            "archive_count": 4,
            "stage_for_purge_count": 16,
            "untouched_old_bookmark_count": 291,
            "final_bookmark_count": 305,
            "reading_list_count": 89,
        },
        "execution_policy": {
            "mode": "manual_safari_only",
            "batch_size": 5,
            "purge_confirmation": "PURGE BROWSER GATEWAY PILOT 1",
            "reading_list_changes_allowed": False,
            "non_manifest_changes_allowed": False,
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
    errors = validate_pilot(document)
    if errors:
        raise BrowserGatewayPilotError("compiled pilot is invalid: " + "; ".join(errors))
    return document


def validate_pilot(document: dict[str, Any]) -> list[str]:
    errors = list(validate_document(document, "browser-gateway-pilot"))
    if errors:
        return errors
    groups = document["groups"]
    if len(groups) != 10 or {row["group_id"] for row in groups} != EXPECTED_GROUP_IDS:
        errors.append("pilot must contain A1-A5 and B1-B5 exactly once")
    proposal_ids = [row["proposal_id"] for row in groups]
    if len(proposal_ids) != len(set(proposal_ids)):
        errors.append("proposal IDs must be unique")
    retirement_ids = [item["item_id"] for row in groups for item in row["retirements"]]
    if len(retirement_ids) != 20 or len(retirement_ids) != len(set(retirement_ids)):
        errors.append("retirement manifest must contain 20 unique items")
    if document["checkpoints"] != [
        {"checkpoint": name, **values} for name, values in CHECKPOINTS.items()
    ]:
        errors.append("checkpoint expectations differ from the pilot contract")
    if document["temporary_collection"] != TEMPORARY_COLLECTION:
        errors.append("temporary collection differs from the pilot contract")
    if document.get("execution_authorized") is not False or document.get("safari_execution_authorized") is not False:
        errors.append("pilot must remain non-executable")
    return errors


def _summary(document: dict[str, Any], *, status: str, writes: bool) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "browser_gateway_pilot_summary",
        "action_id": ACTION_ID,
        "status": status,
        **document["summary"],
        "supersedes_wave": True,
        "output_layer": "private_icloud",
        "private_content_emitted": False,
        "writes_performed": writes,
        "browser_writes_performed": False,
        "execution_authorized": False,
    }


def freeze_pilot(
    organization_path: Path,
    wave_path: Path,
    spec_path: Path,
    output: Path,
    *,
    apply: bool,
    confirmation: str,
    root: Path = ROOT,
    private_root: Path = PRIVATE_ROOT,
) -> dict[str, Any]:
    document = build_pilot(
        _load_object(organization_path), _load_object(wave_path), _load_object(spec_path)
    )
    payload = _canonical_bytes(document)
    destination = output.expanduser().resolve(strict=False)
    allowed = (private_root / "browser" / "gateway").resolve(strict=False)
    if destination.parent != allowed or not re.fullmatch(
        r"pilot-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}\.json", destination.name
    ):
        raise BrowserGatewayPilotError("pilot output must use the approved Private path and name")
    ignored = subprocess.run(
        ["git", "-C", str(root), "check-ignore", "-q", "--", str(destination)],
        capture_output=True,
        text=True,
        check=False,
    )
    if ignored.returncode != 0:
        raise BrowserGatewayPilotError("pilot output must be ignored by Git")
    if not apply:
        return _summary(document, status="preview", writes=False)
    require_confirmation(ACTION_ID, confirmation)
    writes = False
    if destination.exists():
        if destination.is_symlink() or not destination.is_file() or destination.read_bytes() != payload:
            raise BrowserGatewayPilotError("refusing to overwrite a different browser gateway pilot")
        status = "unchanged"
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=destination.parent, prefix=".browser-gateway-pilot-", delete=False
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
            raise BrowserGatewayPilotError("failed to write browser gateway pilot") from exc
        status = "written"
        writes = True
    if destination.stat().st_mode & 0o777 != 0o600:
        os.chmod(destination, 0o600)
        writes = True
    verified = _load_object(destination)
    if _canonical_bytes(verified) != payload or validate_pilot(verified):
        raise BrowserGatewayPilotError("browser gateway pilot failed read-back validation")
    transaction_metadata(ACTION_ID, phase="record", status=status, targets=[destination.name])
    return _summary(verified, status=status, writes=writes)


def _item_key(item: dict[str, Any]) -> tuple[str, str, str, tuple[str, ...]]:
    return (
        item["item_type"],
        item["url"]["original"],
        item.get("title") or "",
        tuple(item["collection"]["path"]),
    )


def _matches_target(item: dict[str, Any], target: list[str]) -> bool:
    path = item["collection"]["path"]
    return len(path) >= len(target) and path[-len(target):] == target


def _semantic_counter(items: list[dict[str, Any]]) -> Counter[tuple[str, str, str, tuple[str, ...]]]:
    return Counter(_item_key(item) for item in items)


def verify_checkpoint(
    pilot: dict[str, Any],
    source_export: Path,
    baseline_export: Path,
    current_export: Path,
    checkpoint: str,
    *,
    observed_on: str,
) -> dict[str, Any]:
    errors = validate_pilot(pilot)
    if errors:
        raise BrowserGatewayPilotError("browser gateway pilot is invalid")
    if checkpoint not in CHECKPOINTS:
        raise BrowserGatewayPilotError("checkpoint is invalid")
    observed = _iso_date(observed_on)
    source = parse_export(source_export)
    baseline = parse_export(baseline_export)
    current = parse_export(current_export)
    reasons: list[str] = []
    if source["artifact_ref"].removeprefix("safari-export:") != pilot["source"]["baseline_export_sha256"]:
        reasons.append("source_export_hash_mismatch")
    if (source["bookmark_count"], source["reading_list_count"]) != (311, 89):
        reasons.append("source_count_mismatch")
    if _semantic_counter(source["items"]) != _semantic_counter(baseline["items"]):
        reasons.append("baseline_semantic_drift")

    baseline_bookmarks = [item for item in baseline["items"] if item["item_type"] == "bookmark"]
    current_bookmarks = [item for item in current["items"] if item["item_type"] == "bookmark"]
    baseline_reading = [item for item in baseline["items"] if item["item_type"] == "reading_list"]
    current_reading = [item for item in current["items"] if item["item_type"] == "reading_list"]
    if _semantic_counter(baseline_reading) != _semantic_counter(current_reading):
        reasons.append("reading_list_drift")

    active_batches = {"batch-1"}
    if checkpoint in {"batch-2", "purge"}:
        active_batches.add("batch-2")
    manifest_urls = {
        retirement["original_url"]
        for group in pilot["groups"]
        for retirement in group["retirements"]
    }
    untouched_baseline = [item for item in baseline_bookmarks if item["url"]["original"] not in manifest_urls]
    untouched_current = [
        item
        for item in current_bookmarks
        if item["url"]["original"] not in manifest_urls
        and item["url"]["original"] not in {group["new_source"]["url"] for group in pilot["groups"]}
    ]
    if _semantic_counter(untouched_baseline) != _semantic_counter(untouched_current):
        reasons.append("non_manifest_bookmark_drift")

    partial_groups = 0
    target_errors = 0
    duplicate_errors = 0
    for group in pilot["groups"]:
        active = group["batch"] in active_batches
        new_matches = [item for item in current_bookmarks if item["url"]["original"] == group["new_source"]["url"]]
        expected_new = 1 if active else 0
        if len(new_matches) != expected_new:
            duplicate_errors += 1
        elif active and not _matches_target(new_matches[0], group["new_source"]["target_collection"]):
            target_errors += 1
        group_ok = len(new_matches) == expected_new
        for retirement in group["retirements"]:
            matches = [item for item in current_bookmarks if item["url"]["original"] == retirement["original_url"]]
            expected_present = not (checkpoint == "purge" and active and retirement["action"] != "archive")
            if len(matches) != (1 if expected_present else 0):
                duplicate_errors += 1
                group_ok = False
                continue
            if expected_present:
                if not active:
                    original = [item for item in baseline_bookmarks if item["url"]["original"] == retirement["original_url"]]
                    if len(original) != 1 or _item_key(matches[0]) != _item_key(original[0]):
                        target_errors += 1
                        group_ok = False
                else:
                    expected_target = retirement["target_collection"]
                    if not _matches_target(matches[0], expected_target):
                        target_errors += 1
                        group_ok = False
                    if (matches[0].get("title") or "") != retirement["original_title"]:
                        target_errors += 1
                        group_ok = False
        if not group_ok:
            partial_groups += 1
    if duplicate_errors:
        reasons.append("missing_or_duplicate_pilot_items")
    if target_errors:
        reasons.append("pilot_target_or_content_drift")
    if partial_groups:
        reasons.append("partial_exchange_groups")

    expected = CHECKPOINTS[checkpoint]
    if current["bookmark_count"] != expected["bookmark_count"]:
        reasons.append("bookmark_count_mismatch")
    if current["reading_list_count"] != expected["reading_list_count"]:
        reasons.append("reading_list_count_mismatch")
    reasons = sorted(set(reasons))
    return {
        "schema_version": 1,
        "kind": "browser_gateway_pilot_verification",
        "status": "passed" if not reasons else "failed",
        "checkpoint": checkpoint,
        "expected": expected,
        "observed": {
            "bookmark_count": current["bookmark_count"],
            "reading_list_count": current["reading_list_count"],
            "partial_group_count": partial_groups,
            "target_error_count": target_errors,
            "duplicate_or_missing_count": duplicate_errors,
        },
        "new_source_review_after": (observed + dt.timedelta(days=45)).isoformat(),
        "reasons": reasons,
        "private_content_emitted": False,
        "writes_performed": False,
        "browser_writes_performed": False,
        "execution_authorized": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    freeze = subparsers.add_parser("freeze")
    freeze.add_argument("organization", type=Path)
    freeze.add_argument("wave", type=Path)
    freeze.add_argument("--spec", type=Path, required=True)
    freeze.add_argument("--output", type=Path, required=True)
    freeze.add_argument("--apply", action="store_true")
    freeze.add_argument("--confirm", default="")
    validate = subparsers.add_parser("validate")
    validate.add_argument("pilot", type=Path)
    verify = subparsers.add_parser("verify")
    verify.add_argument("pilot", type=Path)
    verify.add_argument("--checkpoint", choices=tuple(CHECKPOINTS), required=True)
    verify.add_argument("--source-export", type=Path, required=True)
    verify.add_argument("--baseline-export", type=Path, required=True)
    verify.add_argument("--current-export", type=Path, required=True)
    verify.add_argument("--observed-on", default=dt.date.today().isoformat())
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "freeze":
            result = freeze_pilot(
                args.organization,
                args.wave,
                args.spec,
                args.output,
                apply=args.apply,
                confirmation=args.confirm,
            )
        elif args.command == "validate":
            pilot = _load_object(args.pilot)
            errors = validate_pilot(pilot)
            result = {
                "schema_version": 1,
                "kind": "browser_gateway_pilot_validation",
                "status": "passed" if not errors else "failed",
                "errors": errors,
                "private_content_emitted": False,
                "writes_performed": False,
                "execution_authorized": False,
            }
        else:
            result = verify_checkpoint(
                _load_object(args.pilot),
                args.source_export,
                args.baseline_export,
                args.current_export,
                args.checkpoint,
                observed_on=args.observed_on,
            )
    except (
        BrowserGatewayPilotError,
        SafariExportError,
        SchemaContractError,
        OSError,
        json.JSONDecodeError,
        ValueError,
    ) as exc:
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": "browser_gateway_pilot_result",
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
    return 0 if result.get("status") != "failed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
