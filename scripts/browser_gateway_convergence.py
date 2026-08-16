#!/usr/bin/env python3
"""Compile a bounded Safari gateway and generate a deterministic import package."""

# Mutation action IDs: browser.gateway-convergence-freeze, browser.import-package-write

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Sequence

from browser_gateway import DEFAULT_POLICY, policy_errors
from browser_gateway_order import BrowserGatewayOrderError, ordered_active_sources
from safari_export import NetscapeBookmarkParser
from schema_contract import load_json, validate_document
from transaction_contract import require_confirmation, transaction_metadata


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / "Private"
FREEZE_ACTION_ID = "browser.gateway-convergence-freeze"
PACKAGE_ACTION_ID = "browser.import-package-write"
FREEZE_CONFIRMATION = "FREEZE PRIVATE BROWSER GATEWAY CONVERGENCE 1"
PACKAGE_CONFIRMATION = "GENERATE PRIVATE SAFARI IMPORT PACKAGE"
EXPECTED_CODES = {
    "11", "12", "13", "21", "22", "23", "31", "32", "33",
    "41", "42", "43", "51", "52", "53",
}
SAFARI_PARENT_COLLECTION = "Favorites"
IMPORT_FOLDER_DEPTH = 1


class BrowserGatewayConvergenceError(RuntimeError):
    """A privacy-safe convergence compilation or package error."""


def _canonical_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_object(path: Path) -> dict[str, Any]:
    value = load_json(path)
    if not isinstance(value, dict):
        raise BrowserGatewayConvergenceError("JSON input must be an object")
    return value


def _iso_date(value: str) -> dt.date:
    try:
        result = dt.date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise BrowserGatewayConvergenceError("created_at must be an ISO date") from exc
    if result.isoformat() != value:
        raise BrowserGatewayConvergenceError("created_at must be an ISO date")
    return result


def _target_code(collection: Any) -> str | None:
    if not isinstance(collection, list) or not collection:
        return None
    match = re.match(r"^([0-9]{2})｜", str(collection[-1]))
    return match.group(1) if match else None


def _active_taxonomy(organization: dict[str, Any]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for top in organization["taxonomy"]["top_levels"]:
        if top["role"] != "active":
            continue
        for child in top["children"]:
            result[child["code"]] = [top["folder_name"], child["folder_name"]]
    if set(result) != EXPECTED_CODES:
        raise BrowserGatewayConvergenceError("organization taxonomy is incomplete")
    return result


def _new_source(
    row: dict[str, Any], *, origin: str, target: list[str], created: dt.date
) -> dict[str, Any]:
    required = {
        "title", "url", "source_type", "evidence_url", "evidence_checked_on", "verification"
    }
    if not required.issubset(row):
        raise BrowserGatewayConvergenceError("trial source fields are incomplete")
    url = str(row["url"])
    if not url.startswith("https://"):
        raise BrowserGatewayConvergenceError("trial source URLs must use HTTPS")
    return {
        "source_id": "bgs_" + hashlib.sha256(url.encode()).hexdigest()[:24],
        "origin": origin,
        "status": "trial_new",
        "title": row["title"],
        "url": url,
        "target_collection": target,
        "source_type": row["source_type"],
        "evidence_url": row["evidence_url"],
        "evidence_checked_on": row["evidence_checked_on"],
        "verification": row["verification"],
        "review_after": (created + dt.timedelta(days=45)).isoformat(),
        "execution_authorized": False,
    }


def compile_convergence(
    organization: dict[str, Any],
    pilot: dict[str, Any],
    spec: dict[str, Any],
    policy: dict[str, Any],
) -> dict[str, Any]:
    organization_errors = validate_document(organization, "browser-organization")
    pilot_errors = validate_document(pilot, "browser-gateway-pilot")
    gateway_errors = policy_errors(policy)
    if organization_errors:
        raise BrowserGatewayConvergenceError("browser organization is invalid")
    if pilot_errors:
        raise BrowserGatewayConvergenceError("browser gateway pilot is invalid")
    if gateway_errors:
        raise BrowserGatewayConvergenceError("browser gateway policy is invalid")
    if organization.get("execution_authorized") is not False:
        raise BrowserGatewayConvergenceError("organization must remain non-executable")
    if pilot.get("execution_authorized") is not False or pilot.get("safari_execution_authorized") is not False:
        raise BrowserGatewayConvergenceError("pilot must remain non-executable")
    if pilot["source"]["organization_id"] != organization["organization_id"]:
        raise BrowserGatewayConvergenceError("pilot and organization identity differ")
    if pilot["source"]["organization_artifact_sha256"] != organization["source"]["artifact_sha256"]:
        raise BrowserGatewayConvergenceError("pilot and organization source binding differ")

    required_spec = {
        "candidate_id", "created_at", "target_active", "legacy_keep_urls",
        "quota_fill_sources", "execution_authorized", "safari_execution_authorized",
    }
    if set(spec) != required_spec:
        raise BrowserGatewayConvergenceError("convergence spec fields are invalid")
    if not re.fullmatch(r"bgconv_[A-Za-z0-9_-]{8,}", str(spec["candidate_id"])):
        raise BrowserGatewayConvergenceError("candidate_id is invalid")
    created = _iso_date(str(spec["created_at"]))
    if not (
        policy["capacity"]["minimum_active"]
        <= spec["target_active"]
        <= policy["capacity"]["maximum_active"]
    ):
        raise BrowserGatewayConvergenceError("target_active is outside the public operating range")
    if spec["execution_authorized"] is not False or spec["safari_execution_authorized"] is not False:
        raise BrowserGatewayConvergenceError("convergence spec must not authorize execution")

    taxonomy = _active_taxonomy(organization)
    active = [
        row for row in organization["decisions"]
        if row.get("item_type") == "bookmark" and row.get("disposition") == "move"
    ]
    active_by_url: dict[str, list[dict[str, Any]]] = {}
    for row in active:
        active_by_url.setdefault(row["original_url"], []).append(row)

    pilot_retirements = {
        row["item_id"]: row for group in pilot["groups"] for row in group["retirements"]
    }
    keep_spec = spec["legacy_keep_urls"]
    if not isinstance(keep_spec, dict) or set(keep_spec) != EXPECTED_CODES:
        raise BrowserGatewayConvergenceError("legacy keep URLs must cover all taxonomy codes")
    legacy_sources: list[dict[str, Any]] = []
    selected_ids: set[str] = set()
    selected_urls: set[str] = set()
    for code in sorted(EXPECTED_CODES):
        rows = keep_spec[code]
        if not isinstance(rows, list):
            raise BrowserGatewayConvergenceError("legacy keep URL groups must be arrays")
        for url in rows:
            matches = active_by_url.get(url, [])
            if len(matches) != 1:
                raise BrowserGatewayConvergenceError("legacy keep URL is missing or ambiguous")
            source = matches[0]
            if source["item_id"] in pilot_retirements:
                raise BrowserGatewayConvergenceError("pilot retirement cannot be retained")
            if source["item_id"] in selected_ids or url in selected_urls:
                raise BrowserGatewayConvergenceError("legacy keep source is duplicated")
            if _target_code(source["target_collection"]) != code:
                raise BrowserGatewayConvergenceError("legacy keep source is assigned to the wrong subdomain")
            selected_ids.add(source["item_id"])
            selected_urls.add(url)
            legacy_sources.append(
                {
                    "source_id": source["item_id"],
                    "origin": "legacy",
                    "status": "keep_gateway",
                    "item_fingerprint": source["item_fingerprint"],
                    "title": source["suggested_title"] or source["original_title"],
                    "url": source["original_url"],
                    "target_collection": taxonomy[code],
                    "execution_authorized": False,
                }
            )

    trial_sources: list[dict[str, Any]] = []
    for group in pilot["groups"]:
        row = dict(group["new_source"])
        row["verification"] = "approved_pilot_evidence"
        trial_sources.append(
            _new_source(row, origin="pilot_wave_1", target=taxonomy[group["subdomain_code"]], created=created)
        )
    fill = spec["quota_fill_sources"]
    if not isinstance(fill, list):
        raise BrowserGatewayConvergenceError("quota_fill_sources must be an array")
    for row in fill:
        if not isinstance(row, dict) or row.get("code") not in EXPECTED_CODES:
            raise BrowserGatewayConvergenceError("trial source code is invalid")
        trial_sources.append(
            _new_source(row, origin="convergence_review", target=taxonomy[row["code"]], created=created)
        )

    all_urls = [row["url"] for row in legacy_sources + trial_sources]
    if len(all_urls) != len(set(all_urls)):
        raise BrowserGatewayConvergenceError("final active source URLs must be unique")
    target = spec["target_active"]
    if len(all_urls) != target:
        raise BrowserGatewayConvergenceError("final active source count must equal the reviewed target")
    quotas = {row["code"]: row["total_slots"] for row in policy["subdomains"]}
    counts = Counter(_target_code(row["target_collection"]) for row in legacy_sources + trial_sources)
    if any(counts[code] > quotas[code] for code in EXPECTED_CODES):
        raise BrowserGatewayConvergenceError("final per-subdomain count exceeds policy")
    if sum(counts.values()) != target:
        raise BrowserGatewayConvergenceError("final per-subdomain counts do not match the reviewed target")

    excluded: list[dict[str, Any]] = []
    for source in organization["decisions"]:
        if source.get("item_type") != "bookmark" or source["item_id"] in selected_ids:
            continue
        pilot_row = pilot_retirements.get(source["item_id"])
        if source["disposition"] == "archive" or (pilot_row and pilot_row["action"] == "archive"):
            disposition = "archive"
        elif source["disposition"] == "delete" or (pilot_row and pilot_row["action"] == "stage_for_purge"):
            disposition = "delete"
        elif pilot_row and pilot_row["action"] == "promote_then_stage":
            disposition = "promote_to_obsidian"
        else:
            disposition = "retire_legacy"
        excluded.append(
            {
                "item_id": source["item_id"],
                "item_fingerprint": source["item_fingerprint"],
                "title": source["suggested_title"] or source["original_title"],
                "url": source["original_url"],
                "source_collection": source["source_collection"],
                "disposition": disposition,
                "execution_authorized": False,
            }
        )

    active_sources = sorted(
        legacy_sources + trial_sources,
        key=lambda row: (_target_code(row["target_collection"]) or "", row["title"].casefold(), row["url"]),
    )
    excluded.sort(key=lambda row: (row["disposition"], row["title"].casefold(), row["url"]))
    document = {
        "schema_version": 1,
        "kind": "browser_gateway_convergence",
        "convergence_id": spec["candidate_id"],
        "created_at": spec["created_at"],
        "policy_version": policy["policy_version"],
        "source": {
            "organization_id": organization["organization_id"],
            "organization_artifact_sha256": organization["source"]["artifact_sha256"],
            "pilot_id": pilot["pilot_id"],
            "pilot_sha256": _sha256(_canonical_bytes(pilot)),
            "source_bookmark_count": organization["source"]["bookmark_count"],
            "source_reading_list_count": organization["source"]["reading_list_count"],
        },
        "target": {
            "active_bookmark_count": target,
            "reading_list_mode": "preserve_in_safari_exclude_from_import",
            "reading_list_count": organization["source"]["reading_list_count"],
            "archive_mode": "private_ledger_exclude_from_import",
            "subdomains": [
                {"code": code, "active_count": counts[code], "target_count": quotas[code]}
                for code in sorted(EXPECTED_CODES)
            ],
        },
        "active_sources": active_sources,
        "excluded_sources": excluded,
        "summary": {
            "active_count": len(active_sources),
            "legacy_keep_count": len(legacy_sources),
            "trial_new_count": len(trial_sources),
            "pilot_new_count": sum(row["origin"] == "pilot_wave_1" for row in trial_sources),
            "convergence_new_count": sum(row["origin"] == "convergence_review" for row in trial_sources),
            "excluded_old_bookmark_count": len(excluded),
            "archive_count": sum(row["disposition"] == "archive" for row in excluded),
            "delete_count": sum(row["disposition"] == "delete" for row in excluded),
            "promote_to_obsidian_count": sum(row["disposition"] == "promote_to_obsidian" for row in excluded),
            "retire_legacy_count": sum(row["disposition"] == "retire_legacy" for row in excluded),
            "reading_list_count": organization["source"]["reading_list_count"],
        },
        "privacy": {
            "provenance": "private_user_data",
            "storage_layer": "private_icloud",
            "contains_private_content": True,
            "git_allowed": False,
            "redaction_required": True,
        },
        "import_package_authorized": False,
        "safari_execution_authorized": False,
        "execution_authorized": False,
    }
    errors = validate_document(document, "browser-gateway-convergence")
    if errors:
        raise BrowserGatewayConvergenceError("compiled convergence ledger is invalid: " + "; ".join(errors))
    return document


def _summary(document: dict[str, Any], *, status: str, writes: bool) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "browser_gateway_convergence_summary",
        "action_id": FREEZE_ACTION_ID,
        "status": status,
        **document["summary"],
        "target_active": document["target"]["active_bookmark_count"],
        "subdomain_count": len(document["target"]["subdomains"]),
        "private_content_emitted": False,
        "writes_performed": writes,
        "browser_writes_performed": False,
        "execution_authorized": False,
    }


def _ensure_private_output(destination: Path, pattern: str, private_root: Path, root: Path) -> None:
    allowed = (private_root / "browser" / "gateway").resolve(strict=False)
    if destination.parent != allowed or not re.fullmatch(pattern, destination.name):
        raise BrowserGatewayConvergenceError("output must use the approved Private path and name")
    ignored = subprocess.run(
        ["git", "-C", str(root), "check-ignore", "-q", "--", str(destination)],
        capture_output=True,
        text=True,
        check=False,
    )
    if ignored.returncode != 0:
        raise BrowserGatewayConvergenceError("output must be ignored by Git")


def _write_exact(destination: Path, payload: bytes) -> tuple[str, bool]:
    if destination.exists():
        if destination.is_symlink() or not destination.is_file() or destination.read_bytes() != payload:
            raise BrowserGatewayConvergenceError("refusing to overwrite a different output")
        return "unchanged", False
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=destination.parent, prefix=".browser-gateway-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, destination)
    except OSError as exc:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
        raise BrowserGatewayConvergenceError("failed to write output") from exc
    return "written", True


def freeze(
    organization_path: Path,
    pilot_path: Path,
    spec_path: Path,
    output: Path,
    *,
    policy_path: Path = DEFAULT_POLICY,
    apply: bool,
    confirmation: str,
    root: Path = ROOT,
    private_root: Path = PRIVATE_ROOT,
) -> dict[str, Any]:
    document = compile_convergence(
        _load_object(organization_path), _load_object(pilot_path), _load_object(spec_path), _load_object(policy_path)
    )
    destination = output.expanduser().resolve(strict=False)
    _ensure_private_output(destination, r"convergence-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}\.json", private_root, root)
    if not apply:
        return _summary(document, status="preview", writes=False)
    require_confirmation(FREEZE_ACTION_ID, confirmation)
    payload = _canonical_bytes(document)
    status, writes = _write_exact(destination, payload)
    if destination.stat().st_mode & 0o777 != 0o600:
        os.chmod(destination, 0o600)
        writes = True
    verified = _load_object(destination)
    if _canonical_bytes(verified) != payload or validate_document(verified, "browser-gateway-convergence"):
        raise BrowserGatewayConvergenceError("convergence ledger failed read-back")
    transaction_metadata(FREEZE_ACTION_ID, phase="record", status=status, targets=[destination.name])
    return _summary(verified, status=status, writes=writes)


def render_import_html(document: dict[str, Any], order: dict[str, Any]) -> bytes:
    errors = validate_document(document, "browser-gateway-convergence")
    if errors:
        raise BrowserGatewayConvergenceError("convergence ledger is invalid")
    if document.get("execution_authorized") is not False or document.get("safari_execution_authorized") is not False:
        raise BrowserGatewayConvergenceError("convergence ledger must remain non-executable")
    # Keep the five top-level domains as governance metadata, but project only
    # the 15 subdomains into Safari. Safari 27 imports these package top-level
    # folders as direct children of its system Favorites collection. Encoding
    # another Favorites folder here would risk creating Favorites/Favorites.
    grouped = ordered_active_sources(order, document)
    if len(grouped) != len(EXPECTED_CODES):
        raise BrowserGatewayConvergenceError("import package must contain all 15 subdomain folders")
    lines = [
        "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
        '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
        "<TITLE>macomrade Safari Gateway</TITLE>",
        "<H1>macomrade Safari Gateway</H1>",
        "<DL><p>",
    ]
    for folder, rows in grouped:
        lines.append(f"    <DT><H3>{html.escape(folder)}</H3>")
        lines.append("    <DL><p>")
        for row in rows:
            lines.append(
                f'        <DT><A HREF="{html.escape(row["url"], quote=True)}">{html.escape(row["title"])}</A>'
            )
        lines.append("    </DL><p>")
    lines.append("</DL><p>")
    return ("\n".join(lines) + "\n").encode("utf-8")


def validate_import_html(payload: bytes, document: dict[str, Any], order: dict[str, Any]) -> dict[str, Any]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise BrowserGatewayConvergenceError("import package must be UTF-8") from exc
    parser = NetscapeBookmarkParser()
    parser.feed(text)
    parser.close()
    if any(row["reading_list"] for row in parser.entries):
        raise BrowserGatewayConvergenceError("import package must not contain Reading List items")
    expected = Counter(
        (row["url"], row["title"], (row["target_collection"][-1],))
        for row in document["active_sources"]
    )
    observed = Counter(
        (row["url"], row["title"], tuple(row["folder_path"])) for row in parser.entries
    )
    if observed != expected:
        raise BrowserGatewayConvergenceError("import package does not match the frozen convergence ledger")
    expected_order = [
        (row["url"], row["title"], (folder,))
        for folder, rows in ordered_active_sources(order, document)
        for row in rows
    ]
    observed_order = [
        (row["url"], row["title"], tuple(row["folder_path"])) for row in parser.entries
    ]
    if observed_order != expected_order:
        raise BrowserGatewayConvergenceError("import package order does not match the frozen display order")
    return {"bookmark_count": len(parser.entries), "reading_list_count": 0, "order_verified": True, "sha256": _sha256(payload)}


def generate_package(
    ledger_path: Path,
    order_path: Path,
    output: Path,
    *,
    apply: bool,
    confirmation: str,
    root: Path = ROOT,
    private_root: Path = PRIVATE_ROOT,
) -> dict[str, Any]:
    document = _load_object(ledger_path)
    order = _load_object(order_path)
    payload = render_import_html(document, order)
    validation = validate_import_html(payload, document, order)
    destination = output.expanduser().resolve(strict=False)
    allowed = (private_root / "browser" / "imports").resolve(strict=False)
    if destination.parent != allowed or not re.fullmatch(r"safari-gateway-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{2}\.html", destination.name):
        raise BrowserGatewayConvergenceError("import package must use the approved Private path and name")
    ignored = subprocess.run(
        ["git", "-C", str(root), "check-ignore", "-q", "--", str(destination)],
        capture_output=True, text=True, check=False,
    )
    if ignored.returncode != 0:
        raise BrowserGatewayConvergenceError("import package must be ignored by Git")
    result = {
        "schema_version": 1,
        "kind": "browser_import_package_summary",
        "action_id": PACKAGE_ACTION_ID,
        "status": "preview",
        "bookmark_count": validation["bookmark_count"],
        "reading_list_count": 0,
        "target_folder_count": len(document["target"]["subdomains"]),
        "target_folder_depth": IMPORT_FOLDER_DEPTH,
        "safari_parent_collection": SAFARI_PARENT_COLLECTION,
        "display_order_verified": validation["order_verified"],
        "private_content_emitted": False,
        "writes_performed": False,
        "browser_writes_performed": False,
        "execution_authorized": False,
    }
    if not apply:
        return result
    require_confirmation(PACKAGE_ACTION_ID, confirmation)
    status, writes = _write_exact(destination, payload)
    if destination.stat().st_mode & 0o777 != 0o600:
        os.chmod(destination, 0o600)
        writes = True
    if destination.read_bytes() != payload:
        raise BrowserGatewayConvergenceError("import package failed byte read-back")
    validate_import_html(destination.read_bytes(), document, order)
    transaction_metadata(PACKAGE_ACTION_ID, phase="record", status=status, targets=[destination.name])
    result.update(status=status, writes_performed=writes)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    freeze_parser = sub.add_parser("freeze")
    freeze_parser.add_argument("organization", type=Path)
    freeze_parser.add_argument("pilot", type=Path)
    freeze_parser.add_argument("--spec", type=Path, required=True)
    freeze_parser.add_argument("--output", type=Path, required=True)
    freeze_parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    freeze_parser.add_argument("--apply", action="store_true")
    freeze_parser.add_argument("--confirm", default="")
    package = sub.add_parser("generate-import")
    package.add_argument("ledger", type=Path)
    package.add_argument("--order", type=Path, required=True)
    package.add_argument("--output", type=Path, required=True)
    package.add_argument("--apply", action="store_true")
    package.add_argument("--confirm", default="")
    validate = sub.add_parser("validate")
    validate.add_argument("ledger", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "freeze":
            result = freeze(
                args.organization, args.pilot, args.spec, args.output,
                policy_path=args.policy, apply=args.apply, confirmation=args.confirm,
            )
        elif args.command == "generate-import":
            result = generate_package(
                args.ledger, args.order, args.output, apply=args.apply, confirmation=args.confirm
            )
        else:
            errors = validate_document(_load_object(args.ledger), "browser-gateway-convergence")
            result = {
                "schema_version": 1,
                "kind": "browser_gateway_convergence_validation",
                "status": "passed" if not errors else "failed",
                "error_count": len(errors),
                "private_content_emitted": False,
                "execution_authorized": False,
            }
            if errors:
                raise BrowserGatewayConvergenceError("convergence ledger is invalid")
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (BrowserGatewayConvergenceError, BrowserGatewayOrderError, OSError, ValueError) as exc:
        print(json.dumps({"status": "failed", "error": str(exc), "private_content_emitted": False}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
