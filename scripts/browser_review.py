#!/usr/bin/env python3
"""Create private, explainable URL and duplicate review proposals without writes."""

# Mutation action ID: browser.private-review-export

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import unquote_plus, urlsplit, urlunsplit

from safari_export import SafariExportError, parse_export
from schema_contract import SchemaContractError, load_and_validate, validate_document
from transaction_contract import require_confirmation, transaction_metadata


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / "Private"
POLICY_PATH = ROOT / "settings" / "browser-url-normalization.json"
PRIVATE_REVIEW_ACTION_ID = "browser.private-review-export"
PRIVATE_REVIEW_CONFIRMATION = "EXPORT PRIVATE BROWSER REVIEW"


class BrowserReviewError(RuntimeError):
    """A privacy-safe browser normalization or review failure."""


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    try:
        policy = load_and_validate(path, "browser-url-policy")
    except SchemaContractError as exc:
        raise BrowserReviewError("browser URL normalization policy is invalid") from exc
    if not isinstance(policy, dict):
        raise BrowserReviewError("browser URL normalization policy is invalid")
    return policy


def _semantic_policy_errors(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    removable = [row.get("name") for row in policy.get("removable_query_parameters", [])]
    protected = policy.get("protected_query_parameters", [])
    semantic = policy.get("semantic_parameters_never_remove", [])
    if len(removable) != len(set(removable)):
        errors.append("removable query parameter names must be unique")
    if len(protected) != len(set(protected)):
        errors.append("protected query parameter names must be unique")
    if len(semantic) != len(set(semantic)):
        errors.append("semantic query parameter names must be unique")
    overlap = set(removable) & (set(protected) | set(semantic))
    if overlap:
        errors.append("removable query parameters overlap protected or semantic parameters")
    if policy.get("allowed_schemes") != ["http", "https"]:
        errors.append("allowed schemes must remain exactly http and https")
    if policy.get("cross_identity_grouping") is not False:
        errors.append("cross-identity grouping must remain disabled")
    if policy.get("execution_authorized") is not False:
        errors.append("normalization policy must not authorize execution")
    return errors


def validate_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    try:
        policy = load_policy(path)
        errors = _semantic_policy_errors(policy)
    except BrowserReviewError as exc:
        errors = [str(exc)]
        policy = {}
    return {
        "schema_version": 1,
        "status": "passed" if not errors else "failed",
        "policy_version": policy.get("policy_version"),
        "removable_parameters": len(policy.get("removable_query_parameters", [])),
        "cross_identity_grouping": False,
        "execution_authorized": False,
        "errors": errors,
    }


def _query_segments(query: str) -> list[tuple[str, str]]:
    rows = []
    if not query:
        return rows
    for raw_segment in query.split("&"):
        raw_key = raw_segment.partition("=")[0]
        try:
            comparable_key = unquote_plus(raw_key).casefold()
        except (UnicodeDecodeError, ValueError):
            comparable_key = raw_key.casefold()
        rows.append((raw_segment, comparable_key))
    return rows


def normalize_url(raw_url: str, *, policy: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a private normalization proposal without echoing a blocked URL."""

    selected = policy or load_policy()
    semantic_errors = _semantic_policy_errors(selected)
    if semantic_errors:
        raise BrowserReviewError("browser URL normalization policy is invalid")

    result = {
        "status": "blocked",
        "canonical_url": None,
        "policy_version": selected["policy_version"],
        "changed": False,
        "removed_parameters": [],
        "rule_ids": [],
        "blocked_reasons": [],
        "path_preserved": True,
        "fragment_preserved": True,
        "query_order_preserved": True,
        "repeated_parameters_preserved": True,
        "execution_authorized": False,
    }
    if not isinstance(raw_url, str) or not raw_url or any(ord(char) < 0x20 for char in raw_url):
        result["blocked_reasons"].append("invalid_url")
        return result
    if "\\" in raw_url:
        result["blocked_reasons"].append("ambiguous_authority")
        return result

    try:
        parsed = urlsplit(raw_url)
    except ValueError:
        result["blocked_reasons"].append("invalid_url")
        return result
    scheme = parsed.scheme.casefold()
    if scheme not in selected["allowed_schemes"]:
        result["blocked_reasons"].append("unsupported_scheme")
        return result
    if parsed.username is not None or parsed.password is not None:
        result["blocked_reasons"].append("userinfo_present")
        return result
    try:
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        result["blocked_reasons"].append("invalid_port")
        return result
    if not hostname:
        result["blocked_reasons"].append("missing_host")
        return result
    if ";" in parsed.query:
        result["blocked_reasons"].append("ambiguous_query_separator")
        return result

    segments = _query_segments(parsed.query)
    protected_names = set(selected["protected_query_parameters"])
    protected_prefixes = tuple(selected["protected_query_prefixes"])
    if any(
        key in protected_names or key.startswith(protected_prefixes)
        for _segment, key in segments
    ):
        result["blocked_reasons"].append("protected_query_parameter")
        return result

    normalized_host = hostname.casefold()
    rendered_host = f"[{normalized_host}]" if ":" in normalized_host else normalized_host
    default_port = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    normalized_netloc = rendered_host if port is None or default_port else f"{rendered_host}:{port}"

    if parsed.scheme != scheme or normalized_host not in parsed.netloc:
        result["rule_ids"].append("lowercase_scheme_and_host")
    if default_port:
        result["rule_ids"].append("remove_default_port")

    removable = {row["name"] for row in selected["removable_query_parameters"]}
    kept_segments: list[str] = []
    for raw_segment, comparable_key in segments:
        if comparable_key in removable:
            result["removed_parameters"].append(comparable_key)
        else:
            kept_segments.append(raw_segment)
    if result["removed_parameters"]:
        result["rule_ids"].append("remove_allowlisted_tracking_parameters")

    normalized_query = "&".join(kept_segments)
    canonical = urlunsplit(
        (scheme, normalized_netloc, parsed.path, normalized_query, parsed.fragment)
    )
    before_fragment = raw_url.split("#", 1)[0]
    if "?" in before_fragment and parsed.query == "" and not result["removed_parameters"]:
        if "#" in canonical:
            head, tail = canonical.split("#", 1)
            canonical = f"{head}?#{tail}"
        else:
            canonical += "?"
    if "#" in raw_url and parsed.fragment == "" and not canonical.endswith("#"):
        canonical += "#"
    result["status"] = "proposed"
    result["canonical_url"] = canonical
    result["changed"] = canonical != raw_url
    return result


def _identity_boundary(item: dict[str, Any]) -> tuple[Any, ...]:
    source = item["source"]
    return (
        source["browser"],
        source["profile_scope"],
        source["profile_ref"],
        source["account_ref"],
    )


def _boundary_object(boundary: tuple[Any, ...]) -> dict[str, Any]:
    return {
        "browser": boundary[0],
        "profile_scope": boundary[1],
        "profile_ref": boundary[2],
        "account_ref": boundary[3],
    }


def _append_evidence(
    item: dict[str, Any],
    *,
    evidence_type: str,
    related_item_id: str,
    confidence: str,
) -> None:
    summaries = {
        "exact_url_match": "Exact URL match inside one browser identity boundary.",
        "canonical_url_match": "Proposed canonical URL match inside one browser identity boundary.",
        "title_mismatch": "Titles differ and require human review.",
        "collection_mismatch": "Collections differ and require human review.",
    }
    evidence = {
        "evidence_type": evidence_type,
        "related_item_id": related_item_id,
        "confidence": confidence,
        "summary": summaries[evidence_type],
    }
    if evidence not in item["conflict_evidence"]:
        item["conflict_evidence"].append(evidence)


def review_items(
    items: list[dict[str, Any]],
    *,
    policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize and group private items without crossing identity boundaries."""

    selected = policy or load_policy()
    if _semantic_policy_errors(selected):
        raise BrowserReviewError("browser URL normalization policy is invalid")
    reviewed = copy.deepcopy(items)
    seen_ids: set[str] = set()
    normalization_rows = []
    grouped: dict[tuple[tuple[Any, ...], str], list[dict[str, Any]]] = defaultdict(list)
    url_boundaries: dict[str, set[tuple[Any, ...]]] = defaultdict(set)

    for item in reviewed:
        errors = validate_document(item, "browser-item")
        if errors:
            raise BrowserReviewError("browser item failed schema validation")
        item_id = item["item_id"]
        if item_id in seen_ids:
            raise BrowserReviewError("browser item IDs must be unique")
        seen_ids.add(item_id)

        proposal = normalize_url(item["url"]["original"], policy=selected)
        normalization_rows.append(
            {
                "item_id": item_id,
                "status": proposal["status"],
                "changed": proposal["changed"],
                "removed_parameters": proposal["removed_parameters"],
                "rule_ids": proposal["rule_ids"],
                "blocked_reasons": proposal["blocked_reasons"],
                "execution_authorized": False,
            }
        )
        if proposal["status"] == "proposed":
            item["url"]["canonical"] = proposal["canonical_url"]
            item["url"]["canonicalization_status"] = "proposed"
            item["url"]["canonicalization_version"] = selected["policy_version"]
            comparison_url = proposal["canonical_url"]
        else:
            comparison_url = item["url"]["original"]

        boundary = _identity_boundary(item)
        grouped[(boundary, comparison_url)].append(item)
        url_boundaries[comparison_url].add(boundary)

    duplicate_groups = []
    for (boundary, comparison_url), members in grouped.items():
        if len(members) < 2:
            continue
        members.sort(key=lambda row: row["item_id"])
        member_ids = [row["item_id"] for row in members]
        originals = {row["url"]["original"] for row in members}
        match_type = "exact_url_match" if len(originals) == 1 else "canonical_url_match"
        confidence = "high" if match_type == "exact_url_match" else "medium"
        evidence_types = [match_type]
        if len({row["title"] for row in members}) > 1:
            evidence_types.append("title_mismatch")
        if len(
            {
                (row["collection"]["kind"], tuple(row["collection"]["path"]))
                for row in members
            }
        ) > 1:
            evidence_types.append("collection_mismatch")

        group_seed = "\0".join(member_ids).encode("utf-8")
        duplicate_groups.append(
            {
                "group_id": "brg_" + hashlib.sha256(group_seed).hexdigest()[:24],
                "identity_boundary": _boundary_object(boundary),
                "canonical_url": comparison_url,
                "member_item_ids": member_ids,
                "match_type": match_type,
                "confidence": confidence,
                "evidence_types": evidence_types,
                "cross_identity_boundary": False,
                "proposed_action": "review_only",
                "execution_authorized": False,
            }
        )
        for index, member in enumerate(members):
            related = members[1 if index == 0 else 0]["item_id"]
            for evidence_type in evidence_types:
                _append_evidence(
                    member,
                    evidence_type=evidence_type,
                    related_item_id=related,
                    confidence=confidence,
                )

    duplicate_groups.sort(key=lambda row: row["group_id"])
    for item in reviewed:
        if validate_document(item, "browser-item"):
            raise BrowserReviewError("reviewed browser item failed schema validation")

    suppressed = sum(1 for boundaries in url_boundaries.values() if len(boundaries) > 1)
    return {
        "schema_version": 1,
        "kind": "browser_duplicate_review",
        "policy_version": selected["policy_version"],
        "items": reviewed,
        "normalization": normalization_rows,
        "duplicate_groups": duplicate_groups,
        "cross_identity_groups": 0,
        "cross_identity_collisions_suppressed": suppressed,
        "writes_performed": False,
        "execution_authorized": False,
    }


def redacted_summary(parsed: dict[str, Any], reviewed: dict[str, Any]) -> dict[str, Any]:
    normalizations = reviewed["normalization"]
    groups = reviewed["duplicate_groups"]
    return {
        "schema_version": 1,
        "kind": "browser_review_redacted_summary",
        "status": "passed",
        "source": "safari_export_zip",
        "bookmark_count": parsed["bookmark_count"],
        "reading_list_count": parsed["reading_list_count"],
        "normalization_proposal_count": sum(row["status"] == "proposed" for row in normalizations),
        "normalization_blocked_count": sum(row["status"] == "blocked" for row in normalizations),
        "duplicate_group_count": len(groups),
        "duplicate_item_count": sum(len(group["member_item_ids"]) for group in groups),
        "cross_identity_groups": 0,
        "cross_identity_collisions_suppressed": reviewed["cross_identity_collisions_suppressed"],
        "private_content_emitted": False,
        "writes_performed": False,
        "execution_authorized": False,
    }


def build_private_duplicate_review(
    parsed: Mapping[str, Any], reviewed: Mapping[str, Any]
) -> dict[str, Any]:
    """Build a Private-only review artifact containing duplicate members."""

    item_map = {item["item_id"]: item for item in reviewed["items"]}
    groups = []
    duplicate_item_count = 0
    for group in reviewed["duplicate_groups"]:
        members = []
        for item_id in group["member_item_ids"]:
            item = item_map[item_id]
            members.append(
                {
                    "item_id": item["item_id"],
                    "item_type": item["item_type"],
                    "title": item["title"],
                    "original_url": item["url"]["original"],
                    "canonical_url": item["url"]["canonical"],
                    "canonicalization_status": item["url"]["canonicalization_status"],
                    "collection": copy.deepcopy(item["collection"]),
                    "read_state": item["read_state"],
                }
            )
        duplicate_item_count += len(members)
        groups.append(
            {
                "group_id": group["group_id"],
                "identity_boundary": copy.deepcopy(group["identity_boundary"]),
                "canonical_url": group["canonical_url"],
                "match_type": group["match_type"],
                "confidence": group["confidence"],
                "evidence_types": list(group["evidence_types"]),
                "proposed_action": "review_only",
                "members": members,
            }
        )
    artifact_ref = parsed.get("artifact_ref")
    if not isinstance(artifact_ref, str) or not artifact_ref.startswith("safari-export:"):
        raise BrowserReviewError("Safari export artifact binding is invalid")
    artifact = {
        "schema_version": 1,
        "kind": "browser_private_duplicate_review",
        "source": {
            "browser": "safari",
            "interface": "safari_export_zip",
            "artifact_sha256": artifact_ref.removeprefix("safari-export:"),
            "bookmark_count": parsed["bookmark_count"],
            "reading_list_count": parsed["reading_list_count"],
            "item_count": len(parsed["items"]),
        },
        "policy_version": reviewed["policy_version"],
        "duplicate_group_count": len(groups),
        "duplicate_item_count": duplicate_item_count,
        "groups": groups,
        "privacy": {
            "provenance": "private_export",
            "storage_layer": "private_icloud",
            "contains_private_content": True,
            "git_allowed": False,
            "redaction_required": True,
        },
        "execution_authorized": False,
    }
    if validate_document(artifact, "browser-private-duplicate-review"):
        raise BrowserReviewError("private browser review failed schema validation")
    return artifact


def resolve_private_output(
    output: Path,
    *,
    root: Path = ROOT,
    private_root: Path = PRIVATE_ROOT,
) -> Path:
    """Resolve one JSON destination strictly below Private/browser/."""

    candidate = output.expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve(strict=False)
    browser_root = (private_root / "browser").resolve(strict=False)
    try:
        candidate.relative_to(browser_root)
    except ValueError as exc:
        raise BrowserReviewError("private review output must stay under Private/browser") from exc
    if candidate == browser_root or candidate.suffix.casefold() != ".json":
        raise BrowserReviewError("private review output must be a JSON file under Private/browser")
    return candidate


def _private_review_bytes(artifact: Mapping[str, Any]) -> bytes:
    return (json.dumps(artifact, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _private_export_summary(
    artifact: Mapping[str, Any], *, status: str, writes: bool, would_write: bool
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "browser_private_review_export_summary",
        "action_id": PRIVATE_REVIEW_ACTION_ID,
        "status": status,
        "duplicate_group_count": artifact["duplicate_group_count"],
        "duplicate_item_count": artifact["duplicate_item_count"],
        "output_layer": "private_icloud",
        "would_write": would_write,
        "private_content_emitted": False,
        "writes_performed": writes,
        "browser_writes_performed": False,
        "execution_authorized": False,
    }


def export_private_duplicate_review(
    artifact: Mapping[str, Any],
    output: Path,
    *,
    apply: bool,
    confirmation: str,
    root: Path = ROOT,
    private_root: Path = PRIVATE_ROOT,
) -> dict[str, Any]:
    """Preview or atomically write one non-authorizing Private review file."""

    errors = validate_document(dict(artifact), "browser-private-duplicate-review")
    if errors:
        raise BrowserReviewError("private browser review failed schema validation")
    destination = resolve_private_output(
        output,
        root=root,
        private_root=private_root,
    )
    if artifact["duplicate_group_count"] == 0:
        return _private_export_summary(
            artifact, status="no_candidates", writes=False, would_write=False
        )
    if not apply:
        return _private_export_summary(
            artifact, status="preview", writes=False, would_write=True
        )
    try:
        require_confirmation(PRIVATE_REVIEW_ACTION_ID, confirmation)
    except ValueError as exc:
        raise BrowserReviewError(str(exc)) from exc

    payload = _private_review_bytes(artifact)
    writes = False
    if destination.exists():
        if destination.is_symlink() or not destination.is_file():
            raise BrowserReviewError("private review destination is not a regular file")
        try:
            existing = destination.read_bytes()
        except OSError as exc:
            raise BrowserReviewError("private review destination is unreadable") from exc
        if existing != payload:
            raise BrowserReviewError("refusing to overwrite a different private browser review")
        status = "unchanged"
        if destination.stat().st_mode & 0o777 != 0o600:
            try:
                os.chmod(destination, 0o600)
            except OSError as exc:
                raise BrowserReviewError("failed to secure private browser review") from exc
            status = "permissions_corrected"
            writes = True
    else:
        temporary: Path | None = None
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.parent.resolve() != (private_root / "browser").resolve() and not (
                destination.parent.resolve().is_relative_to((private_root / "browser").resolve())
            ):
                raise BrowserReviewError("private review output must stay under Private/browser")
            with tempfile.NamedTemporaryFile(
                mode="wb",
                dir=destination.parent,
                prefix=".browser-review-",
                delete=False,
            ) as target:
                temporary = Path(target.name)
                target.write(payload)
                target.flush()
                os.fsync(target.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, destination)
        except BrowserReviewError:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            raise
        except OSError as exc:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            raise BrowserReviewError("failed to write private browser review") from exc
        status = "written"
        writes = True

    try:
        verified = json.loads(destination.read_text(encoding="utf-8"))
        mode = destination.stat().st_mode & 0o777
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BrowserReviewError("private browser review failed read-back") from exc
    if verified != dict(artifact) or mode != 0o600 or validate_document(
        verified, "browser-private-duplicate-review"
    ):
        raise BrowserReviewError("private browser review failed verification")
    transaction_metadata(
        PRIVATE_REVIEW_ACTION_ID,
        phase="record",
        status=status,
        targets=["private_browser_duplicate_review"],
    )
    return _private_export_summary(
        artifact,
        status=status,
        writes=writes,
        would_write=False,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate-policy", help="validate the tracked normalization policy")
    inspect_parser = subparsers.add_parser(
        "inspect-safari-export",
        help="emit a redacted normalization and duplicate summary for one explicit export",
    )
    inspect_parser.add_argument("export", type=Path)
    private_parser = subparsers.add_parser(
        "export-private-duplicates",
        help="preview or exact-confirm a Private duplicate review export",
    )
    private_parser.add_argument("export", type=Path)
    private_parser.add_argument("--output", type=Path, required=True)
    private_parser.add_argument("--apply", action="store_true")
    private_parser.add_argument("--confirm", default="")
    args = parser.parse_args(argv)

    if args.command == "validate-policy":
        result = validate_policy()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "passed" else 1

    try:
        parsed = parse_export(args.export)
        reviewed = review_items(parsed["items"])
        if args.command == "export-private-duplicates":
            artifact = build_private_duplicate_review(parsed, reviewed)
            result = export_private_duplicate_review(
                artifact,
                args.output,
                apply=args.apply,
                confirmation=args.confirm,
                root=ROOT,
                private_root=PRIVATE_ROOT,
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0
    except (SafariExportError, BrowserReviewError) as exc:
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": "browser_review_redacted_summary",
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
    print(json.dumps(redacted_summary(parsed, reviewed), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
