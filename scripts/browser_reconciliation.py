#!/usr/bin/env python3
"""Reconcile a Private browser organization against one newer Safari export."""

# Mutation action ID: browser.reconciliation-candidate-write

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

from browser_lifecycle import item_fingerprint
from browser_organization import build_organization, validate_organization
from browser_review import BrowserReviewError, review_items
from safari_export import SafariExportError, parse_export
from transaction_contract import require_confirmation, transaction_metadata


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / "Private"
ACTION_ID = "browser.reconciliation-candidate-write"
CONFIRMATION = "WRITE PRIVATE BROWSER RECONCILIATION CANDIDATE"


class BrowserReconciliationError(RuntimeError):
    """A privacy-safe browser reconciliation failure."""


def _date(value: str) -> str:
    try:
        parsed = dt.date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise BrowserReconciliationError("reconciled-on must be an ISO calendar date") from exc
    if parsed.isoformat() != value:
        raise BrowserReconciliationError("reconciled-on must be an ISO calendar date")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BrowserReconciliationError("Private browser organization is unavailable") from exc
    if not isinstance(value, dict):
        raise BrowserReconciliationError("Private browser organization is unavailable")
    return value


def _fingerprint_matches(
    old_decisions: list[dict[str, Any]],
    new_items: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], set[str]]:
    old_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    new_buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in old_decisions:
        old_buckets[row["item_fingerprint"]].append(row)
    for item in new_items:
        new_buckets[item_fingerprint(item)].append(item)
    old_for_new: dict[str, dict[str, Any]] = {}
    matched_old: set[str] = set()
    for fingerprint in sorted(set(old_buckets) & set(new_buckets)):
        old_rows = old_buckets[fingerprint]
        new_rows = new_buckets[fingerprint]
        if len(old_rows) != len(new_rows):
            continue
        for old_row, new_item in zip(old_rows, new_rows):
            old_for_new[new_item["item_id"]] = old_row
            matched_old.add(old_row["item_id"])
    return old_for_new, matched_old


def _duplicate_reconciliation(
    old: Mapping[str, Any],
    reviewed: Mapping[str, Any],
    new_items: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], set[str], int, int]:
    old_decisions = {row["item_id"]: row for row in old["decisions"]}
    old_by_signature: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for group in old["duplicate_resolutions"]:
        signature = tuple(
            sorted(old_decisions[row["item_id"]]["item_fingerprint"] for row in group["members"])
        )
        old_by_signature[signature].append(group)

    new_item_map = {item["item_id"]: item for item in new_items}
    new_by_signature: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for group in reviewed["duplicate_groups"]:
        signature = tuple(
            sorted(item_fingerprint(new_item_map[item_id]) for item_id in group["member_item_ids"])
        )
        new_by_signature[signature].append(group)

    resolutions: list[dict[str, Any]] = []
    review_ids: set[str] = set()
    stable = 0
    matched_old_groups: set[str] = set()
    resolution_order = {"keep": 0, "delete": 1, "delete_later": 2}
    for signature, new_groups in new_by_signature.items():
        old_groups = old_by_signature.get(signature, [])
        if len(old_groups) != 1 or len(new_groups) != 1:
            for group in new_groups:
                review_ids.update(group["member_item_ids"])
            continue
        old_group = old_groups[0]
        new_group = new_groups[0]
        matched_old_groups.add(old_group["group_id"])
        old_resolutions: dict[str, list[str]] = defaultdict(list)
        for member in old_group["members"]:
            fingerprint = old_decisions[member["item_id"]]["item_fingerprint"]
            old_resolutions[fingerprint].append(member["resolution"])
        new_members: dict[str, list[str]] = defaultdict(list)
        for item_id in new_group["member_item_ids"]:
            new_members[item_fingerprint(new_item_map[item_id])].append(item_id)
        transferred = []
        compatible = True
        for fingerprint in sorted(new_members):
            item_ids = sorted(new_members[fingerprint])
            member_resolutions = sorted(
                old_resolutions.get(fingerprint, []),
                key=lambda value: resolution_order[value],
            )
            if len(item_ids) != len(member_resolutions):
                compatible = False
                break
            transferred.extend(
                {"item_id": item_id, "resolution": resolution}
                for item_id, resolution in zip(item_ids, member_resolutions)
            )
        if not compatible:
            review_ids.update(new_group["member_item_ids"])
            continue
        resolutions.append({"group_id": new_group["group_id"], "members": transferred})
        stable += 1
    unmatched_old = len(old["duplicate_resolutions"]) - len(matched_old_groups)
    unmatched_new = len(reviewed["duplicate_groups"]) - stable
    return resolutions, review_ids, stable, unmatched_old + unmatched_new


def _expected_counts(
    items: list[dict[str, Any]],
    rules: list[dict[str, Any]],
    overrides: list[dict[str, Any]],
    duplicate_resolutions: list[dict[str, Any]],
) -> dict[str, int]:
    rule_paths = {tuple(row["source_path"]): row for row in rules}
    override_map = {row["item_id"]: row for row in overrides}
    dispositions: dict[str, str] = {}
    types: dict[str, str] = {}
    direct = 0
    for item in items:
        item_id = item["item_id"]
        types[item_id] = item["item_type"]
        if item["item_type"] == "reading_list":
            dispositions[item_id] = "defer"
        elif tuple(item["collection"]["path"]) in rule_paths:
            dispositions[item_id] = "move"
            direct += 1
        else:
            dispositions[item_id] = override_map[item_id]["disposition"]
    for group in duplicate_resolutions:
        for member in group["members"]:
            if member["resolution"] == "delete":
                dispositions[member["item_id"]] = "delete"
            elif member["resolution"] == "delete_later":
                dispositions[member["item_id"]] = "delete_later"
    counts = Counter(dispositions.values())
    return {
        "directory_rule_item_count": direct,
        "ambiguous_item_count": len(overrides),
        "duplicate_group_count": len(duplicate_resolutions),
        "active_move_count": counts["move"],
        "archive_count": counts["archive"],
        "bookmark_delete_count": sum(
            types[item_id] == "bookmark" and disposition == "delete"
            for item_id, disposition in dispositions.items()
        ),
        "reading_list_delete_later_count": counts["delete_later"],
        "reading_list_deferred_count": counts["defer"],
        "bookmark_operation_count": sum(value == "bookmark" for value in types.values()),
        "item_count": len(items),
    }


def reconcile_organization(
    old: Mapping[str, Any],
    new_export: Path,
    *,
    reconciled_on: str,
) -> dict[str, Any]:
    date = _date(reconciled_on)
    if validate_organization(old):
        raise BrowserReconciliationError("existing browser organization is invalid")
    try:
        parsed = parse_export(new_export)
        reviewed = review_items(parsed["items"])
    except (SafariExportError, BrowserReviewError) as exc:
        raise BrowserReconciliationError("new Safari export is invalid") from exc
    new_hash = parsed["artifact_ref"].removeprefix("safari-export:")
    old_hash = old["source"]["artifact_sha256"]
    new_items = reviewed["items"]
    source_changed = new_hash != old_hash
    old_for_new, matched_old = _fingerprint_matches(old["decisions"], new_items)
    removed_count = len(old["decisions"]) - len(matched_old)

    rules_by_path: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for rule in old["path_rules"]:
        rules_by_path[tuple(rule["source_path"])].append(rule)
    used_rule_ids: set[str] = set()
    overrides: list[dict[str, Any]] = []
    review_ids: set[str] = set()
    path_applied = 0
    for item in new_items:
        item_id = item["item_id"]
        if item["item_type"] == "reading_list":
            if item_id not in old_for_new:
                review_ids.add(item_id)
            continue
        rules = rules_by_path.get(tuple(item["collection"]["path"]), [])
        if len(rules) == 1:
            used_rule_ids.add(rules[0]["rule_id"])
            path_applied += 1
            continue
        if len(rules) > 1:
            review_ids.add(item_id)
            continue
        old_row = old_for_new.get(item_id)
        if old_row is None or old_row["assignment_basis"] != "item_override":
            review_ids.add(item_id)
            continue
        overrides.append(
            {
                "item_id": item_id,
                "disposition": old_row["disposition"],
                "target_collection": copy.deepcopy(old_row["target_collection"]),
                "note": old_row["note"],
            }
        )

    duplicate_resolutions, duplicate_review, stable_groups, changed_groups = (
        _duplicate_reconciliation(old, reviewed, new_items)
    )
    review_ids.update(duplicate_review)
    candidate_ready = (
        source_changed
        and not review_ids
        and removed_count == 0
        and changed_groups == 0
    )
    candidate = None
    if candidate_ready:
        rules = [
            {
                "rule_id": row["rule_id"],
                "source_path": copy.deepcopy(row["source_path"]),
                "target_path": copy.deepcopy(row["target_path"]),
            }
            for row in old["path_rules"]
            if row["rule_id"] in used_rule_ids
        ]
        expected = _expected_counts(new_items, rules, overrides, duplicate_resolutions)
        spec = {
            "organization_id": f"borg_reconcile_{new_hash[:24]}",
            "created_at": f"{date}T00:00:00+00:00",
            "taxonomy": copy.deepcopy(old["taxonomy"]),
            "path_rules": rules,
            "item_overrides": overrides,
            "duplicate_resolutions": duplicate_resolutions,
            "expected": expected,
            "privacy": {
                "provenance": "private_user_data",
                "storage_layer": "private_icloud",
                "contains_private_content": True,
                "git_allowed": False,
                "redaction_required": True,
            },
            "execution_authorized": False,
        }
        candidate = build_organization(parsed, spec)

    summary = {
        "schema_version": 1,
        "kind": "browser_reconciliation_redacted_summary",
        "action_id": ACTION_ID,
        "status": "candidate_ready" if candidate_ready else ("source_unchanged" if not source_changed else "review_required"),
        "source_hash_changed": source_changed,
        "old_item_count": len(old["decisions"]),
        "new_item_count": len(new_items),
        "fingerprint_inherited_count": len(old_for_new),
        "path_rule_applied_count": path_applied,
        "removed_item_count": removed_count,
        "review_required_count": len(review_ids),
        "stable_duplicate_group_count": stable_groups,
        "changed_duplicate_group_count": changed_groups,
        "candidate_ready": candidate_ready,
        "canonical_switch_performed": False,
        "private_content_emitted": False,
        "writes_performed": False,
        "browser_writes_performed": False,
        "execution_authorized": False,
    }
    return {"summary": summary, "candidate": candidate}


def _candidate_path(candidate: Mapping[str, Any], date: str, private_root: Path) -> Path:
    digest = candidate["source"]["artifact_sha256"]
    return private_root / "browser" / "versions" / f"organization-{date}-{digest[:12]}.json"


def _assert_ignored(path: Path, root: Path) -> None:
    probe = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode == 0:
        ignored = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "-q", "--", str(path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if ignored.returncode != 0:
            raise BrowserReconciliationError("candidate destination must be ignored by Git")


def write_candidate(
    candidate: Mapping[str, Any] | None,
    *,
    reconciled_on: str,
    apply: bool,
    confirmation: str,
    root: Path = ROOT,
    private_root: Path = PRIVATE_ROOT,
) -> dict[str, Any]:
    date = _date(reconciled_on)
    if candidate is None or validate_organization(candidate):
        raise BrowserReconciliationError("reconciliation candidate is unavailable or invalid")
    destination = _candidate_path(candidate, date, private_root).resolve(strict=False)
    versions_root = (private_root / "browser" / "versions").resolve(strict=False)
    if destination.parent != versions_root:
        raise BrowserReconciliationError("candidate destination escapes Private versions")
    _assert_ignored(destination, root)
    summary = {
        "schema_version": 1,
        "kind": "browser_reconciliation_candidate_summary",
        "action_id": ACTION_ID,
        "status": "preview",
        "item_count": candidate["summary"]["item_count"],
        "candidate_written": False,
        "canonical_switch_performed": False,
        "private_content_emitted": False,
        "writes_performed": False,
        "browser_writes_performed": False,
        "execution_authorized": False,
    }
    if not apply:
        return summary
    require_confirmation(ACTION_ID, confirmation)
    payload = (json.dumps(candidate, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    writes = False
    if destination.exists() or destination.is_symlink():
        if destination.is_symlink() or not destination.is_file():
            raise BrowserReconciliationError("candidate destination is not a regular file")
        if destination.read_bytes() != payload:
            raise BrowserReconciliationError("refusing to overwrite a different reconciliation candidate")
        status = "unchanged"
        if destination.stat().st_mode & 0o777 != 0o600:
            os.chmod(destination, 0o600)
            status = "permissions_corrected"
            writes = True
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=destination.parent,
                prefix=".browser-reconciliation-",
                delete=False,
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
            raise BrowserReconciliationError("failed to write reconciliation candidate") from exc
        status = "written"
        writes = True
    try:
        verified = json.loads(destination.read_text(encoding="utf-8"))
        mode = destination.stat().st_mode & 0o777
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BrowserReconciliationError("reconciliation candidate failed read-back") from exc
    if verified != dict(candidate) or mode != 0o600 or validate_organization(verified):
        raise BrowserReconciliationError("reconciliation candidate failed read-back")
    transaction_metadata(ACTION_ID, phase="record", status=status, targets=[candidate["organization_id"]])
    summary.update(
        {
            "status": status,
            "candidate_written": True,
            "writes_performed": writes,
        }
    )
    return summary


def validate_policy() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "browser_reconciliation_policy_summary",
        "status": "passed",
        "action_id": ACTION_ID,
        "versioned_candidate_only": True,
        "canonical_switch_supported": False,
        "private_content_emitted": False,
        "writes_performed": False,
        "browser_writes_performed": False,
        "execution_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate-policy")
    reconcile_parser = subparsers.add_parser("reconcile-safari-export")
    reconcile_parser.add_argument("organization", type=Path)
    reconcile_parser.add_argument("export", type=Path)
    reconcile_parser.add_argument("--reconciled-on", required=True)
    reconcile_parser.add_argument("--apply", action="store_true")
    reconcile_parser.add_argument("--confirm", default="")
    args = parser.parse_args(argv)
    try:
        if args.command == "validate-policy":
            result = validate_policy()
        else:
            old = _load_json(args.organization)
            reconciliation = reconcile_organization(
                old,
                args.export,
                reconciled_on=args.reconciled_on,
            )
            result = reconciliation["summary"]
            if args.apply:
                record = write_candidate(
                    reconciliation["candidate"],
                    reconciled_on=args.reconciled_on,
                    apply=True,
                    confirmation=args.confirm,
                )
                result = {**result, **record, "kind": "browser_reconciliation_redacted_summary"}
    except (BrowserReconciliationError, ValueError, KeyError) as exc:
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": "browser_reconciliation_redacted_summary",
                    "status": "failed",
                    "error": str(exc),
                    "private_content_emitted": False,
                    "writes_performed": False,
                    "browser_writes_performed": False,
                    "execution_authorized": False,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {
        "passed", "candidate_ready", "review_required", "source_unchanged",
        "preview", "written", "unchanged", "permissions_corrected"
    } else 1


if __name__ == "__main__":
    raise SystemExit(main())
