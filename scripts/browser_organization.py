#!/usr/bin/env python3
"""Compile reviewed Safari taxonomy decisions into one Private fact source."""

# Mutation action ID: browser.organization-sync

from __future__ import annotations

import argparse
import copy
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit

from browser_lifecycle import item_fingerprint
from browser_review import BrowserReviewError, review_items
from safari_export import SafariExportError, parse_export
from schema_contract import validate_document
from transaction_contract import require_confirmation, transaction_metadata


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / "Private"
ACTION_ID = "browser.organization-sync"
CONFIRMATION = "SYNC PRIVATE BROWSER ORGANIZATION"
SUMMARY_KEYS = (
    "directory_rule_item_count",
    "ambiguous_item_count",
    "duplicate_group_count",
    "active_move_count",
    "archive_count",
    "bookmark_delete_count",
    "reading_list_delete_later_count",
    "reading_list_deferred_count",
    "bookmark_operation_count",
    "item_count",
)


class BrowserOrganizationError(RuntimeError):
    """A privacy-safe browser organization compilation failure."""


def _parse_created_at(value: Any) -> None:
    if not isinstance(value, str):
        raise BrowserOrganizationError("organization created_at is invalid")
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BrowserOrganizationError("organization created_at is invalid") from exc
    if parsed.tzinfo is None:
        raise BrowserOrganizationError("organization created_at is invalid")


def _private_json(path: Path, *, expected: type) -> Any:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BrowserOrganizationError("private organization input is unavailable or invalid") from exc
    if not isinstance(value, expected):
        raise BrowserOrganizationError("private organization input is unavailable or invalid")
    return value


def _normalized_token(value: str) -> str:
    return "".join(character for character in value.casefold() if character.isalnum())


def suggest_title(original_title: str | None, original_url: str) -> dict[str, Any]:
    """Return a conservative, deterministic suggestion without changing the source."""

    if original_title is None:
        return {"suggested_title": None, "rule_ids": []}
    title = original_title
    normalized = re.sub(r"\s+", " ", title).strip()
    rules: list[str] = []
    if normalized != title:
        rules.append("normalize_whitespace")
    candidate = normalized
    try:
        hostname = (urlsplit(original_url).hostname or "").casefold()
    except ValueError:
        hostname = ""
    host_parts = [part for part in hostname.split(".") if part and part != "www"]
    comparable_hosts = {_normalized_token(hostname)}
    if len(host_parts) >= 2:
        comparable_hosts.add(_normalized_token(host_parts[-2]))
        comparable_hosts.add(_normalized_token(".".join(host_parts[-2:])))
    for separator in (" - ", " | ", " · ", " _ "):
        if separator not in candidate:
            continue
        head, suffix = candidate.rsplit(separator, 1)
        if head and _normalized_token(suffix) in comparable_hosts:
            candidate = head.strip()
            rules.append("remove_matching_site_suffix")
            break
    return {
        "suggested_title": candidate if candidate != original_title else None,
        "rule_ids": rules,
    }


def _validate_taxonomy(taxonomy: Mapping[str, Any]) -> tuple[set[tuple[str, ...]], dict[tuple[str, ...], str]]:
    if taxonomy.get("primary_axis") != "long_term_domains":
        raise BrowserOrganizationError("browser taxonomy primary axis is invalid")
    if taxonomy.get("max_semantic_depth") != 2:
        raise BrowserOrganizationError("browser taxonomy depth is invalid")
    if taxonomy.get("project_context_owner") != "obsidian":
        raise BrowserOrganizationError("browser taxonomy project boundary is invalid")
    if taxonomy.get("reading_list_role") != "temporary_inbox":
        raise BrowserOrganizationError("browser taxonomy Reading List role is invalid")
    top_levels = taxonomy.get("top_levels")
    if not isinstance(top_levels, list) or len(top_levels) != 6:
        raise BrowserOrganizationError("browser taxonomy must contain five active domains and one archive")
    codes: set[str] = set()
    names: set[str] = set()
    paths: set[tuple[str, ...]] = set()
    roles: dict[tuple[str, ...], str] = {}
    role_counts: Counter[str] = Counter()
    for top in top_levels:
        if not isinstance(top, dict):
            raise BrowserOrganizationError("browser taxonomy contains an invalid domain")
        code = top.get("code")
        name = top.get("folder_name")
        role = top.get("role")
        children = top.get("children")
        if not isinstance(code, str) or not isinstance(name, str) or role not in {"active", "archive"}:
            raise BrowserOrganizationError("browser taxonomy contains an invalid domain")
        if code in codes or name in names:
            raise BrowserOrganizationError("browser taxonomy names and codes must be unique")
        codes.add(code)
        names.add(name)
        role_counts[role] += 1
        if not isinstance(children, list):
            raise BrowserOrganizationError("browser taxonomy children are invalid")
        expected_children = 5 if role == "archive" else None
        if (role == "active" and not 1 <= len(children) <= 3) or (
            expected_children is not None and len(children) != expected_children
        ):
            raise BrowserOrganizationError("browser taxonomy child count is invalid")
        for child in children:
            if not isinstance(child, dict):
                raise BrowserOrganizationError("browser taxonomy contains an invalid child")
            child_code = child.get("code")
            child_name = child.get("folder_name")
            if not isinstance(child_code, str) or not isinstance(child_name, str):
                raise BrowserOrganizationError("browser taxonomy contains an invalid child")
            if child_code in codes or child_name in names:
                raise BrowserOrganizationError("browser taxonomy names and codes must be unique")
            codes.add(child_code)
            names.add(child_name)
            path = ("Favorites", name, child_name)
            paths.add(path)
            roles[path] = role
    if role_counts != Counter({"active": 5, "archive": 1}):
        raise BrowserOrganizationError("browser taxonomy must contain five active domains and one archive")
    return paths, roles


def _validate_spec(spec: Mapping[str, Any]) -> None:
    _parse_created_at(spec.get("created_at"))
    if not isinstance(spec.get("organization_id"), str) or not spec["organization_id"].startswith("borg_"):
        raise BrowserOrganizationError("organization ID is invalid")
    privacy = spec.get("privacy")
    if privacy != {
        "provenance": "private_user_data",
        "storage_layer": "private_icloud",
        "contains_private_content": True,
        "git_allowed": False,
        "redaction_required": True,
    }:
        raise BrowserOrganizationError("organization privacy boundary is invalid")
    if spec.get("execution_authorized") is not False:
        raise BrowserOrganizationError("organization must not authorize execution")
    expected = spec.get("expected")
    if not isinstance(expected, dict) or set(expected) != set(SUMMARY_KEYS):
        raise BrowserOrganizationError("organization expected counts are invalid")
    if any(not isinstance(expected[key], int) or expected[key] < 0 for key in SUMMARY_KEYS):
        raise BrowserOrganizationError("organization expected counts are invalid")
    for field in ("path_rules", "item_overrides", "duplicate_resolutions"):
        if not isinstance(spec.get(field), list):
            raise BrowserOrganizationError("organization decision specification is invalid")


def _target_errors(
    disposition: str,
    target: Any,
    *,
    allowed_paths: set[tuple[str, ...]],
    roles: Mapping[tuple[str, ...], str],
) -> list[str]:
    if disposition in {"delete", "delete_later", "defer"}:
        return [] if target is None else ["non-move decision cannot have a target"]
    if not isinstance(target, list) or tuple(target) not in allowed_paths:
        return ["organization target is outside the taxonomy"]
    expected_role = "archive" if disposition == "archive" else "active"
    return [] if roles[tuple(target)] == expected_role else ["organization target role is invalid"]


def build_organization(parsed: Mapping[str, Any], spec: Mapping[str, Any]) -> dict[str, Any]:
    """Compile every exported item exactly once under reviewed Private rules."""

    _validate_spec(spec)
    taxonomy = spec.get("taxonomy")
    if not isinstance(taxonomy, dict):
        raise BrowserOrganizationError("browser taxonomy is invalid")
    allowed_paths, roles = _validate_taxonomy(taxonomy)
    artifact_ref = parsed.get("artifact_ref")
    items = parsed.get("items")
    if not isinstance(artifact_ref, str) or not artifact_ref.startswith("safari-export:"):
        raise BrowserOrganizationError("Safari export binding is invalid")
    if not isinstance(items, list):
        raise BrowserOrganizationError("Safari export items are invalid")
    try:
        reviewed = review_items(items)
    except BrowserReviewError as exc:
        raise BrowserOrganizationError("Safari export review failed") from exc
    reviewed_items = reviewed["items"]
    item_map = {item["item_id"]: item for item in reviewed_items}
    if len(item_map) != len(reviewed_items):
        raise BrowserOrganizationError("Safari item IDs must be unique")

    rules = spec["path_rules"]
    rule_ids = [row.get("rule_id") for row in rules if isinstance(row, dict)]
    if len(rule_ids) != len(rules) or len(rule_ids) != len(set(rule_ids)):
        raise BrowserOrganizationError("organization path rule IDs must be unique")
    overrides = spec["item_overrides"]
    override_ids = [row.get("item_id") for row in overrides if isinstance(row, dict)]
    if len(override_ids) != len(overrides) or len(override_ids) != len(set(override_ids)):
        raise BrowserOrganizationError("organization item overrides must be unique")
    unknown_overrides = set(override_ids) - set(item_map)
    if unknown_overrides:
        raise BrowserOrganizationError("organization override references an unknown item")

    rule_counts: Counter[str] = Counter()
    decisions: list[dict[str, Any]] = []
    decision_map: dict[str, dict[str, Any]] = {}
    for item in reviewed_items:
        item_id = item["item_id"]
        title = suggest_title(item["title"], item["url"]["original"])
        if item["item_type"] == "reading_list":
            decision = {
                "assignment_basis": "reading_list_policy",
                "rule_id": None,
                "disposition": "defer",
                "target_collection": None,
                "note": None,
            }
        else:
            matching_rules = [
                row
                for row in rules
                if isinstance(row, dict)
                and row.get("source_path") == item["collection"]["path"]
            ]
            matching_overrides = [row for row in overrides if row.get("item_id") == item_id]
            if len(matching_rules) + len(matching_overrides) != 1:
                raise BrowserOrganizationError(
                    "every bookmark must have exactly one base assignment"
                )
            if matching_rules:
                rule = matching_rules[0]
                target = rule.get("target_path")
                decision = {
                    "assignment_basis": "path_rule",
                    "rule_id": rule.get("rule_id"),
                    "disposition": "move",
                    "target_collection": copy.deepcopy(target),
                    "note": None,
                }
                rule_counts[str(rule.get("rule_id"))] += 1
            else:
                override = matching_overrides[0]
                decision = {
                    "assignment_basis": "item_override",
                    "rule_id": None,
                    "disposition": override.get("disposition"),
                    "target_collection": copy.deepcopy(override.get("target_collection")),
                    "note": override.get("note"),
                }
        target_errors = _target_errors(
            str(decision["disposition"]),
            decision["target_collection"],
            allowed_paths=allowed_paths,
            roles=roles,
        )
        if target_errors:
            raise BrowserOrganizationError(target_errors[0])
        row = {
            "item_id": item_id,
            "item_fingerprint": item_fingerprint(item),
            "item_type": item["item_type"],
            "original_title": item["title"],
            "suggested_title": title["suggested_title"],
            "title_suggestion_rule_ids": title["rule_ids"],
            "original_url": item["url"]["original"],
            "source_collection": copy.deepcopy(item["collection"]["path"]),
            **decision,
            "duplicate_group_id": None,
            "execution_authorized": False,
        }
        decisions.append(row)
        decision_map[item_id] = row

    reviewed_groups = {row["group_id"]: row for row in reviewed["duplicate_groups"]}
    supplied_groups = spec["duplicate_resolutions"]
    supplied_ids = [row.get("group_id") for row in supplied_groups if isinstance(row, dict)]
    if len(supplied_ids) != len(supplied_groups) or len(supplied_ids) != len(set(supplied_ids)):
        raise BrowserOrganizationError("duplicate resolutions must have unique group IDs")
    if set(supplied_ids) != set(reviewed_groups):
        raise BrowserOrganizationError("every duplicate group must be resolved exactly once")
    for resolution in supplied_groups:
        group_id = resolution["group_id"]
        actual_members = set(reviewed_groups[group_id]["member_item_ids"])
        members = resolution.get("members")
        if not isinstance(members, list):
            raise BrowserOrganizationError("duplicate resolution members are invalid")
        resolved_ids = [row.get("item_id") for row in members if isinstance(row, dict)]
        if len(resolved_ids) != len(members) or set(resolved_ids) != actual_members:
            raise BrowserOrganizationError("duplicate resolution members do not match the group")
        for member in members:
            row = decision_map[member["item_id"]]
            resolution_name = member.get("resolution")
            if resolution_name == "keep":
                pass
            elif resolution_name == "delete" and row["item_type"] == "bookmark":
                row["disposition"] = "delete"
                row["target_collection"] = None
            elif resolution_name == "delete_later" and row["item_type"] == "reading_list":
                row["disposition"] = "delete_later"
                row["target_collection"] = None
            else:
                raise BrowserOrganizationError("duplicate resolution is incompatible with item type")
            row["duplicate_group_id"] = group_id

    dispositions = Counter(row["disposition"] for row in decisions)
    summary = {
        "directory_rule_item_count": sum(rule_counts.values()),
        "ambiguous_item_count": len(overrides),
        "duplicate_group_count": len(supplied_groups),
        "active_move_count": dispositions["move"],
        "archive_count": dispositions["archive"],
        "bookmark_delete_count": sum(
            row["item_type"] == "bookmark" and row["disposition"] == "delete"
            for row in decisions
        ),
        "reading_list_delete_later_count": dispositions["delete_later"],
        "reading_list_deferred_count": dispositions["defer"],
        "bookmark_operation_count": sum(row["item_type"] == "bookmark" for row in decisions),
        "item_count": len(decisions),
    }
    if summary != spec["expected"]:
        raise BrowserOrganizationError("compiled organization counts differ from reviewed expectations")
    compiled_rules = [
        {
            "rule_id": row["rule_id"],
            "source_path": copy.deepcopy(row["source_path"]),
            "target_path": copy.deepcopy(row["target_path"]),
            "matched_item_count": rule_counts[row["rule_id"]],
        }
        for row in rules
    ]
    if any(row["matched_item_count"] == 0 for row in compiled_rules):
        raise BrowserOrganizationError("organization path rule matched no items")
    organization = {
        "schema_version": 1,
        "kind": "browser_organization",
        "organization_id": spec["organization_id"],
        "created_at": spec["created_at"],
        "source": {
            "browser": "safari",
            "interface": "safari_export_zip",
            "artifact_sha256": artifact_ref.removeprefix("safari-export:"),
            "bookmark_count": parsed["bookmark_count"],
            "reading_list_count": parsed["reading_list_count"],
            "item_count": len(decisions),
        },
        "taxonomy": copy.deepcopy(taxonomy),
        "title_policy": {
            "mode": "conservative_deterministic_suggestions",
            "preserve_original": True,
            "translation_allowed": False,
            "summary_allowed": False,
            "execution_authorized": False,
            "allowed_rule_ids": [
                "normalize_whitespace",
                "remove_matching_site_suffix",
            ],
        },
        "path_rules": compiled_rules,
        "item_overrides": copy.deepcopy(overrides),
        "duplicate_resolutions": copy.deepcopy(supplied_groups),
        "decisions": decisions,
        "summary": summary,
        "privacy": copy.deepcopy(spec["privacy"]),
        "execution_authorized": False,
    }
    errors = validate_organization(organization)
    if errors:
        raise BrowserOrganizationError("compiled organization failed validation")
    return organization


def validate_organization(organization: Mapping[str, Any]) -> list[str]:
    errors = validate_document(dict(organization), "browser-organization")
    if errors:
        return errors
    try:
        allowed_paths, roles = _validate_taxonomy(organization["taxonomy"])
    except BrowserOrganizationError as exc:
        return [str(exc)]
    decisions = organization["decisions"]
    item_ids = [row["item_id"] for row in decisions]
    if len(item_ids) != len(set(item_ids)):
        errors.append("organization item IDs must be unique")
    summary = organization["summary"]
    dispositions = Counter(row["disposition"] for row in decisions)
    computed = {
        "directory_rule_item_count": sum(
            row["assignment_basis"] == "path_rule" for row in decisions
        ),
        "ambiguous_item_count": sum(
            row["assignment_basis"] == "item_override" for row in decisions
        ),
        "duplicate_group_count": len(organization["duplicate_resolutions"]),
        "active_move_count": dispositions["move"],
        "archive_count": dispositions["archive"],
        "bookmark_delete_count": sum(
            row["item_type"] == "bookmark" and row["disposition"] == "delete"
            for row in decisions
        ),
        "reading_list_delete_later_count": dispositions["delete_later"],
        "reading_list_deferred_count": dispositions["defer"],
        "bookmark_operation_count": sum(row["item_type"] == "bookmark" for row in decisions),
        "item_count": len(decisions),
    }
    if computed != summary:
        errors.append("organization summary does not match decisions")
    source = organization["source"]
    if source["item_count"] != len(decisions):
        errors.append("organization source item count is invalid")
    if source["bookmark_count"] != sum(row["item_type"] == "bookmark" for row in decisions):
        errors.append("organization source bookmark count is invalid")
    if source["reading_list_count"] != sum(row["item_type"] == "reading_list" for row in decisions):
        errors.append("organization source Reading List count is invalid")
    for row in decisions:
        errors.extend(
            _target_errors(
                row["disposition"],
                row["target_collection"],
                allowed_paths=allowed_paths,
                roles=roles,
            )
        )
        if row["item_type"] == "bookmark" and row["disposition"] not in {"move", "archive", "delete"}:
            errors.append("bookmark disposition is invalid")
        if row["item_type"] == "reading_list" and row["disposition"] not in {"delete_later", "defer"}:
            errors.append("Reading List disposition is invalid")
        if row["suggested_title"] == row["original_title"] and row["suggested_title"] is not None:
            errors.append("title suggestion must differ from the original")
        if row["execution_authorized"]:
            errors.append("organization decision authorizes execution")
    if organization["execution_authorized"]:
        errors.append("organization authorizes execution")
    return sorted(set(errors))


def resolve_private_output(
    output: Path,
    *,
    root: Path = ROOT,
    private_root: Path = PRIVATE_ROOT,
) -> Path:
    candidate = output.expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve(strict=False)
    browser_root = (private_root / "browser").resolve(strict=False)
    try:
        candidate.relative_to(browser_root)
    except ValueError as exc:
        raise BrowserOrganizationError("organization output must stay under Private/browser") from exc
    if candidate == browser_root or candidate.suffix.casefold() != ".json":
        raise BrowserOrganizationError("organization output must be a JSON file under Private/browser")
    return candidate


def _organization_bytes(organization: Mapping[str, Any]) -> bytes:
    return (json.dumps(organization, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _assert_private_destination(organization: Mapping[str, Any], destination: Path, root: Path) -> None:
    expected_privacy = {
        "provenance": "private_user_data",
        "storage_layer": "private_icloud",
        "contains_private_content": True,
        "git_allowed": False,
        "redaction_required": True,
    }
    if organization.get("privacy") != expected_privacy:
        raise BrowserOrganizationError("organization persistence requires Private privacy metadata")
    probe = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        return
    ignored = subprocess.run(
        ["git", "-C", str(root), "check-ignore", "-q", "--", str(destination)],
        capture_output=True,
        text=True,
        check=False,
    )
    if ignored.returncode != 0:
        raise BrowserOrganizationError("organization destination must be ignored by Git")


def _summary(organization: Mapping[str, Any], *, status: str, writes: bool, would_write: bool) -> dict[str, Any]:
    summary = organization["summary"]
    return {
        "schema_version": 1,
        "kind": "browser_organization_redacted_summary",
        "action_id": ACTION_ID,
        "status": status,
        **{key: summary[key] for key in SUMMARY_KEYS},
        "title_suggestion_count": sum(
            row["suggested_title"] is not None for row in organization["decisions"]
        ),
        "would_write": would_write,
        "private_content_emitted": False,
        "writes_performed": writes,
        "browser_writes_performed": False,
        "execution_authorized": False,
    }


def sync_private_organization(
    organization: Mapping[str, Any],
    output: Path,
    *,
    apply: bool,
    confirmation: str,
    root: Path = ROOT,
    private_root: Path = PRIVATE_ROOT,
) -> dict[str, Any]:
    errors = validate_organization(organization)
    if errors:
        raise BrowserOrganizationError("organization is invalid")
    destination = resolve_private_output(output, root=root, private_root=private_root)
    _assert_private_destination(organization, destination, root)
    if not apply:
        return _summary(organization, status="preview", writes=False, would_write=True)
    try:
        require_confirmation(ACTION_ID, confirmation)
    except (ValueError, KeyError) as exc:
        raise BrowserOrganizationError(str(exc)) from exc
    payload = _organization_bytes(organization)
    writes = False
    if destination.exists():
        if destination.is_symlink() or not destination.is_file():
            raise BrowserOrganizationError("organization destination is not a regular file")
        try:
            existing = destination.read_bytes()
        except OSError as exc:
            raise BrowserOrganizationError("organization destination is unreadable") from exc
        if existing != payload:
            raise BrowserOrganizationError("refusing to overwrite a different browser organization")
        status = "unchanged"
        if destination.stat().st_mode & 0o777 != 0o600:
            os.chmod(destination, 0o600)
            status = "permissions_corrected"
            writes = True
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.parent.resolve().is_relative_to((private_root / "browser").resolve()):
            raise BrowserOrganizationError("organization output must stay under Private/browser")
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=destination.parent,
                prefix=".browser-organization-",
                delete=False,
            ) as target:
                temporary = Path(target.name)
                target.write(payload)
                target.flush()
                os.fsync(target.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, destination)
        except OSError as exc:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            raise BrowserOrganizationError("failed to write browser organization") from exc
        status = "written"
        writes = True
    try:
        verified = json.loads(destination.read_text(encoding="utf-8"))
        mode = destination.stat().st_mode & 0o777
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BrowserOrganizationError("browser organization failed read-back") from exc
    if verified != dict(organization) or mode != 0o600 or validate_organization(verified):
        raise BrowserOrganizationError("browser organization failed verification")
    transaction_metadata(
        ACTION_ID,
        phase="record",
        status=status,
        targets=[organization["organization_id"]],
    )
    return _summary(organization, status=status, writes=writes, would_write=False)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate", help="validate one Private organization")
    validate_parser.add_argument("organization", type=Path)
    compile_parser = subparsers.add_parser(
        "compile-safari-export",
        help="compile one reviewed private spec against an explicit Safari export",
    )
    compile_parser.add_argument("export", type=Path)
    compile_parser.add_argument("--spec", type=Path, required=True)
    compile_parser.add_argument("--output", type=Path, required=True)
    compile_parser.add_argument("--apply", action="store_true")
    compile_parser.add_argument("--confirm", default="")
    args = parser.parse_args(argv)

    try:
        if args.command == "validate":
            organization = _private_json(args.organization, expected=dict)
            errors = validate_organization(organization)
            result = {
                "schema_version": 1,
                "kind": "browser_organization_redacted_summary",
                "status": "passed" if not errors else "failed",
                "item_count": len(organization.get("decisions", [])),
                "errors": errors,
                "private_content_emitted": False,
                "writes_performed": False,
                "execution_authorized": False,
            }
        else:
            parsed = parse_export(args.export)
            spec = _private_json(args.spec, expected=dict)
            organization = build_organization(parsed, spec)
            result = sync_private_organization(
                organization,
                args.output,
                apply=args.apply,
                confirmation=args.confirm,
                root=ROOT,
                private_root=PRIVATE_ROOT,
            )
    except (BrowserOrganizationError, BrowserReviewError, SafariExportError) as exc:
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": "browser_organization_redacted_summary",
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
    return 0 if result["status"] in {"passed", "preview", "written", "unchanged", "permissions_corrected"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
