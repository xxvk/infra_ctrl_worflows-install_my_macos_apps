#!/usr/bin/env python3
# Mutation action ID: browser.gateway-order-freeze
"""Compile and freeze an explicit per-folder Safari gateway display order."""

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

from schema_contract import load_json, validate_document
from transaction_contract import require_confirmation, transaction_metadata


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / "Private"
ACTION_ID = "browser.gateway-order-freeze"
CONFIRMATION = "FREEZE PRIVATE BROWSER GATEWAY ORDER 1"
TIERS = ("pinned", "core", "monitor", "trial", "low_frequency")
REASONS = {"manual_pin", "personal_relevance", "recurring_value", "authority", "recency", "low_frequency"}
EXPECTED_CODES = {
    "11", "12", "13", "21", "22", "23", "31", "32", "33",
    "41", "42", "43", "51", "52", "53",
}


class BrowserGatewayOrderError(RuntimeError):
    """Raised when a Private display-order contract is invalid."""


def canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_object(path: Path) -> dict[str, Any]:
    value = load_json(path)
    if not isinstance(value, dict):
        raise BrowserGatewayOrderError("JSON input must be an object")
    return value


def _target_code(collection: Any) -> str | None:
    if not isinstance(collection, list) or not collection:
        return None
    match = re.match(r"^([0-9]{2})｜", str(collection[-1]))
    return match.group(1) if match else None


def _validate_date(value: Any) -> str:
    try:
        parsed = dt.date.fromisoformat(str(value))
    except ValueError as exc:
        raise BrowserGatewayOrderError("created_at must be an ISO date") from exc
    if parsed.isoformat() != value:
        raise BrowserGatewayOrderError("created_at must be an ISO date")
    return str(value)


def compile_order(convergence: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    errors = validate_document(convergence, "browser-gateway-convergence")
    if errors:
        raise BrowserGatewayOrderError("convergence ledger is invalid")
    if convergence.get("execution_authorized") is not False:
        raise BrowserGatewayOrderError("convergence ledger must remain non-executable")
    required = {"order_id", "created_at", "folders", "safari_execution_authorized", "execution_authorized"}
    if set(spec) != required:
        raise BrowserGatewayOrderError("order spec fields are invalid")
    if not re.fullmatch(r"bgo_[A-Za-z0-9_-]{8,}", str(spec["order_id"])):
        raise BrowserGatewayOrderError("order_id is invalid")
    _validate_date(spec["created_at"])
    if spec["safari_execution_authorized"] is not False or spec["execution_authorized"] is not False:
        raise BrowserGatewayOrderError("order spec must not authorize Safari or execution")

    sources = {row["source_id"]: row for row in convergence["active_sources"]}
    if len(sources) != len(convergence["active_sources"]):
        raise BrowserGatewayOrderError("convergence source IDs are not unique")
    folders = spec["folders"]
    if not isinstance(folders, list) or len(folders) != len(EXPECTED_CODES):
        raise BrowserGatewayOrderError("order spec must contain 15 folders")

    seen_codes: set[str] = set()
    seen_sources: set[str] = set()
    compiled_folders: list[dict[str, Any]] = []
    tier_counts: Counter[str] = Counter()
    tier_index = {name: index for index, name in enumerate(TIERS)}
    for folder in folders:
        if not isinstance(folder, dict) or set(folder) != {"code", "items"}:
            raise BrowserGatewayOrderError("folder order fields are invalid")
        code = folder["code"]
        if code not in EXPECTED_CODES or code in seen_codes:
            raise BrowserGatewayOrderError("folder code is invalid or duplicated")
        seen_codes.add(code)
        items = folder["items"]
        if not isinstance(items, list) or not items:
            raise BrowserGatewayOrderError("every folder order must contain items")
        compiled_items = []
        folder_name: str | None = None
        previous_tier = -1
        pinned_count = 0
        for rank, item in enumerate(items, start=1):
            if not isinstance(item, dict) or set(item) != {"source_id", "tier", "reason"}:
                raise BrowserGatewayOrderError("ordered item fields are invalid")
            source_id = item["source_id"]
            tier = item["tier"]
            reason = item["reason"]
            source = sources.get(source_id)
            if source is None or source_id in seen_sources:
                raise BrowserGatewayOrderError("ordered source is missing or duplicated")
            if _target_code(source["target_collection"]) != code:
                raise BrowserGatewayOrderError("ordered source is assigned to the wrong folder")
            if tier not in tier_index or reason not in REASONS:
                raise BrowserGatewayOrderError("tier or reason is invalid")
            if tier_index[tier] < previous_tier:
                raise BrowserGatewayOrderError("tier blocks must follow the public priority order")
            previous_tier = tier_index[tier]
            if tier == "pinned":
                pinned_count += 1
            if pinned_count > 3:
                raise BrowserGatewayOrderError("a folder may contain at most three pinned sources")
            current_folder_name = source["target_collection"][-1]
            if folder_name is None:
                folder_name = current_folder_name
            elif folder_name != current_folder_name:
                raise BrowserGatewayOrderError("folder name is inconsistent inside one code")
            seen_sources.add(source_id)
            tier_counts[tier] += 1
            compiled_items.append({
                "source_id": source_id,
                "tier": tier,
                "display_rank": rank,
                "reason": reason,
                "execution_authorized": False,
            })
        compiled_folders.append({"code": code, "folder_name": folder_name, "items": compiled_items})
    if seen_codes != EXPECTED_CODES or seen_sources != set(sources):
        raise BrowserGatewayOrderError("order spec must cover every folder and source exactly once")

    compiled_folders.sort(key=lambda row: row["code"])
    document = {
        "schema_version": 1,
        "kind": "browser_gateway_order",
        "order_id": spec["order_id"],
        "created_at": spec["created_at"],
        "source": {
            "convergence_id": convergence["convergence_id"],
            "convergence_sha256": _sha256(canonical_bytes(convergence)),
            "active_bookmark_count": len(sources),
        },
        "policy": {
            "tiers": list(TIERS),
            "max_pinned_per_folder": 3,
            "fallback": "explicit_display_rank_only",
        },
        "folders": compiled_folders,
        "summary": {
            "folder_count": len(compiled_folders),
            "item_count": len(seen_sources),
            **{f"{tier}_count": tier_counts[tier] for tier in TIERS},
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
    schema_errors = validate_document(document, "browser-gateway-order")
    if schema_errors:
        raise BrowserGatewayOrderError("compiled order is invalid: " + "; ".join(schema_errors))
    return document


def ordered_active_sources(order: dict[str, Any], convergence: dict[str, Any]) -> list[tuple[str, list[dict[str, Any]]]]:
    if validate_document(order, "browser-gateway-order"):
        raise BrowserGatewayOrderError("browser gateway order is invalid")
    if validate_document(convergence, "browser-gateway-convergence"):
        raise BrowserGatewayOrderError("convergence ledger is invalid")
    if order["source"]["convergence_id"] != convergence["convergence_id"]:
        raise BrowserGatewayOrderError("order and convergence IDs differ")
    if order["source"]["convergence_sha256"] != _sha256(canonical_bytes(convergence)):
        raise BrowserGatewayOrderError("order and convergence hash binding differ")
    sources = {row["source_id"]: row for row in convergence["active_sources"]}
    seen: set[str] = set()
    result = []
    for folder in sorted(order["folders"], key=lambda row: row["code"]):
        ranks = [row["display_rank"] for row in folder["items"]]
        if ranks != list(range(1, len(ranks) + 1)):
            raise BrowserGatewayOrderError("display ranks must be contiguous")
        rows = []
        for item in folder["items"]:
            source = sources.get(item["source_id"])
            if source is None or item["source_id"] in seen:
                raise BrowserGatewayOrderError("order source coverage is invalid")
            if _target_code(source["target_collection"]) != folder["code"]:
                raise BrowserGatewayOrderError("order source folder binding is invalid")
            seen.add(item["source_id"])
            rows.append(source)
        result.append((folder["folder_name"], rows))
    if seen != set(sources):
        raise BrowserGatewayOrderError("order does not cover the convergence ledger")
    return result


def _summary(document: dict[str, Any], *, status: str, writes: bool) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "browser_gateway_order_summary",
        "action_id": ACTION_ID,
        "status": status,
        **document["summary"],
        "private_content_emitted": False,
        "writes_performed": writes,
        "browser_writes_performed": False,
        "execution_authorized": False,
    }


def _ensure_private_output(destination: Path, private_root: Path, root: Path) -> None:
    allowed = (private_root / "browser" / "gateway").resolve(strict=False)
    if destination.parent != allowed or not re.fullmatch(r"order-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}\.json", destination.name):
        raise BrowserGatewayOrderError("output must use the approved Private order path")
    ignored = subprocess.run(
        ["git", "-C", str(root), "check-ignore", "-q", "--", str(destination)],
        capture_output=True, text=True, check=False,
    )
    if ignored.returncode != 0:
        raise BrowserGatewayOrderError("output must be ignored by Git")


def _write_exact(destination: Path, payload: bytes) -> tuple[str, bool]:
    if destination.exists():
        if destination.is_symlink() or not destination.is_file() or destination.read_bytes() != payload:
            raise BrowserGatewayOrderError("refusing to overwrite a different order")
        return "unchanged", False
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=destination.parent, prefix=".browser-order-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
    except OSError as exc:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise BrowserGatewayOrderError("failed to write order") from exc
    return "written", True


def freeze(convergence_path: Path, spec_path: Path, output: Path, *, apply: bool, confirmation: str,
           root: Path = ROOT, private_root: Path = PRIVATE_ROOT) -> dict[str, Any]:
    document = compile_order(_load_object(convergence_path), _load_object(spec_path))
    destination = output.expanduser().resolve(strict=False)
    _ensure_private_output(destination, private_root, root)
    if not apply:
        return _summary(document, status="preview", writes=False)
    require_confirmation(ACTION_ID, confirmation)
    payload = canonical_bytes(document)
    status, writes = _write_exact(destination, payload)
    if destination.stat().st_mode & 0o777 != 0o600:
        os.chmod(destination, 0o600)
        writes = True
    verified = _load_object(destination)
    if canonical_bytes(verified) != payload or validate_document(verified, "browser-gateway-order"):
        raise BrowserGatewayOrderError("order failed read-back")
    ordered_active_sources(verified, _load_object(convergence_path))
    transaction_metadata(ACTION_ID, phase="record", status=status, targets=[destination.name])
    return _summary(verified, status=status, writes=writes)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("convergence", type=Path)
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--confirm", default="")
    args = parser.parse_args(argv)
    try:
        result = freeze(args.convergence, args.spec, args.output, apply=args.apply, confirmation=args.confirm)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (BrowserGatewayOrderError, OSError, ValueError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc), "private_content_emitted": False}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
