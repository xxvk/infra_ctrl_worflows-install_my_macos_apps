#!/usr/bin/env python3
"""Inventory and classify a repository before any public-visibility decision.

The audit is read-only with respect to Git and the working tree. It records
paths, categories, and counts only; matched text and secret values are never
copied into output. A finding never authorizes history rewrite, force-push, or
repository visibility changes.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import stat
import subprocess
from pathlib import Path
from typing import Any, Callable

from schema_contract import SchemaContractError, load_and_validate
from state_paths import add_state_dir_argument, resolve_state_dir


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "settings" / "publication-audit-policy.json"


class PublicationAuditError(RuntimeError):
    """Raised when the publication audit cannot produce bounded evidence."""


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    try:
        return load_and_validate(path, "publication-audit-policy")
    except SchemaContractError as exc:
        raise PublicationAuditError(str(exc)) from exc


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("kind") != "macomrade_publication_audit_policy":
        raise PublicationAuditError("publication audit policy kind is invalid")
    ids = [item["id"] for item in policy["sensitive_patterns"]]
    if len(ids) != len(set(ids)):
        raise PublicationAuditError("sensitive pattern IDs must be unique")
    for item in policy["sensitive_patterns"]:
        try:
            re.compile(item["pattern"], flags=re.IGNORECASE)
        except re.error as exc:
            raise PublicationAuditError(f"invalid pattern {item['id']}: {exc}") from exc


def validate() -> dict[str, Any]:
    try:
        policy = load_policy()
        validate_policy(policy)
    except PublicationAuditError as exc:
        return {"schema_version": 1, "status": "failed", "errors": [str(exc)]}
    return {
        "schema_version": 1,
        "status": "passed",
        "pattern_count": len(policy["sensitive_patterns"]),
        "governance_file_count": len(policy["governance_files"]),
        "errors": [],
    }


def _path_class(path: str, policy: dict[str, Any]) -> str:
    if any(path.startswith(prefix) for prefix in policy["private_prefixes"]):
        return "private_overlay"
    if path.startswith("tests/") or "/fixtures/" in path:
        return "test_or_fixture"
    if path.startswith("references/") or path.endswith(".md"):
        return "documentation"
    return "implementation_or_config"


def _read_text(path: Path, limit: int) -> str | None:
    try:
        if path.stat().st_size > limit:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    if b"\x00" in data:
        return None
    return data.decode("utf-8", errors="ignore")


def scan_current_tree(root: Path, tracked_files: list[str], policy: dict[str, Any]) -> dict[str, Any]:
    validate_policy(policy)
    private_files, large_files, binary_files = [], [], []
    generated_artifacts, third_party_assets, symlinks, executables = [], [], [], []
    findings: dict[str, dict[str, Any]] = {
        item["id"]: {"id": item["id"], "severity": item["severity"], "paths": [], "path_classes": {}}
        for item in policy["sensitive_patterns"]
    }
    compiled = {item["id"]: re.compile(item["pattern"], re.IGNORECASE) for item in policy["sensitive_patterns"]}
    scan_limit = max(policy["large_file_bytes"], 8 * 1024 * 1024)
    for relative in sorted(set(tracked_files)):
        path = root / relative
        if any(relative.startswith(prefix) for prefix in policy["private_prefixes"]):
            private_files.append(relative)
        try:
            info = path.lstat()
        except OSError:
            continue
        if stat.S_ISLNK(info.st_mode):
            symlinks.append(relative)
            continue
        if info.st_size >= policy["large_file_bytes"]:
            large_files.append({"path": relative, "logical_bytes": info.st_size})
        if info.st_mode & stat.S_IXUSR:
            executables.append(relative)
        lowered = relative.lower()
        if any(relative.startswith(prefix) for prefix in policy["generated_prefixes"]) or any(lowered.endswith(suffix) for suffix in policy["artifact_suffixes"]):
            generated_artifacts.append(relative)
        if relative.startswith(("vendor/", "third_party/", "third-party/")) or any(lowered.endswith(suffix) for suffix in (".a", ".dylib", ".so", ".framework")):
            third_party_assets.append(relative)
        text = _read_text(path, scan_limit)
        if text is None:
            if info.st_size:
                binary_files.append(relative)
            continue
        for pattern_id, expression in compiled.items():
            if expression.search(text):
                row = findings[pattern_id]
                row["paths"].append(relative)
                path_class = _path_class(relative, policy)
                row["path_classes"][path_class] = row["path_classes"].get(path_class, 0) + 1
    sensitive = [row for row in findings.values() if row["paths"]]
    governance = {name: (root / name).is_file() for name in policy["governance_files"]}
    return {
        "tracked_file_count": len(set(tracked_files)),
        "private_files": private_files,
        "large_files": large_files,
        "binary_files": binary_files,
        "generated_artifacts": generated_artifacts,
        "third_party_assets": third_party_assets,
        "symlinks": symlinks,
        "executables": executables,
        "governance_files": governance,
        "missing_governance_files": sorted(name for name, exists in governance.items() if not exists),
        "sensitive_findings": sensitive,
    }


def _git(root: Path, args: list[str], runner: Callable[..., subprocess.CompletedProcess[str]]) -> subprocess.CompletedProcess[str]:
    return runner(["git", *args], cwd=root, capture_output=True, text=True, check=False)


def tracked_files(root: Path, runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> list[str]:
    result = _git(root, ["ls-files", "-z"], runner)
    if result.returncode != 0:
        raise PublicationAuditError("cannot enumerate tracked files")
    return [item for item in result.stdout.split("\0") if item]


def _git_grep_paths(root: Path, commit: str, pattern: str, runner: Callable[..., subprocess.CompletedProcess[str]]) -> list[str]:
    result = _git(root, ["grep", "-I", "-l", "-E", "-i", pattern, commit, "--", "."], runner)
    if result.returncode not in {0, 1}:
        raise PublicationAuditError("Git history pattern scan failed")
    paths = []
    for line in result.stdout.splitlines():
        prefix = f"{commit}:"
        paths.append(line[len(prefix):] if line.startswith(prefix) else line)
    return paths


def scan_history(root: Path, policy: dict[str, Any], runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> dict[str, Any]:
    commits_result = _git(root, ["rev-list", "--all"], runner)
    if commits_result.returncode != 0:
        raise PublicationAuditError("cannot enumerate Git history")
    commits = [item for item in commits_result.stdout.splitlines() if item]
    findings = {item["id"]: {"id": item["id"], "severity": item["severity"], "paths": set(), "commit_count": 0} for item in policy["sensitive_patterns"]}
    for commit in commits:
        for pattern in policy["sensitive_patterns"]:
            paths = _git_grep_paths(root, commit, pattern["pattern"], runner)
            if paths:
                findings[pattern["id"]]["commit_count"] += 1
                findings[pattern["id"]]["paths"].update(paths)
    private_result = _git(root, ["rev-list", "--all", "--", "Private"], runner)
    if private_result.returncode != 0:
        raise PublicationAuditError("cannot inspect Private history")
    return {
        "commit_count": len(commits),
        "private_commit_count": len([item for item in private_result.stdout.splitlines() if item]),
        "sensitive_findings": [
            {**row, "paths": sorted(row["paths"])}
            for row in findings.values()
            if row["paths"]
        ],
    }


def submodules(root: Path, runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> list[dict[str, str]]:
    path = root / ".gitmodules"
    if not path.is_file():
        return []
    result = _git(root, ["config", "--file", ".gitmodules", "--get-regexp", r"^submodule\..*\.path$"], runner)
    if result.returncode not in {0, 1}:
        raise PublicationAuditError("cannot inspect submodule paths")
    rows = []
    for line in result.stdout.splitlines():
        key, _, value = line.partition(" ")
        rows.append({"id": key.removeprefix("submodule.").removesuffix(".path"), "path": value})
    return rows


def classify(current: dict[str, Any], history: dict[str, Any]) -> dict[str, Any]:
    blockers = []
    if current.get("private_files"):
        blockers.append("tracked_private_overlay")
    if current.get("sensitive_findings"):
        blockers.append("current_tree_findings_require_classification")
    if history.get("sensitive_findings") or history.get("private_commit_count"):
        blockers.append("history_findings_require_classification")
    if current.get("missing_governance_files"):
        blockers.append("open_source_governance_incomplete")
    if current.get("large_files") or current.get("binary_files") or current.get("generated_artifacts") or current.get("third_party_assets"):
        blockers.append("artifact_or_license_review_required")
    if current.get("submodules"):
        blockers.append("submodule_visibility_review_required")
    return {
        "status": "review_required" if blockers else "candidate_clear",
        "blockers": blockers,
        "visibility_change_authorized": False,
        "history_rewrite_authorized": False,
        "publication_authorized": False,
    }


def inspect(root: Path = ROOT, runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run) -> dict[str, Any]:
    policy = load_policy()
    validate_policy(policy)
    current = scan_current_tree(root, tracked_files(root, runner), policy)
    current["submodules"] = submodules(root, runner)
    history = scan_history(root, policy, runner)
    return {
        "schema_version": 1,
        "kind": "publication_surface_audit",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "repository_name": root.name,
        "privacy_boundary": "paths_categories_and_counts_only_no_matched_values",
        "current_tree": current,
        "history": history,
        "classification": classify(current, history),
    }


def _write_record(state_dir: Path, value: dict[str, Any]) -> Path:
    destination = state_dir / "publication-audits"
    destination.mkdir(parents=True, exist_ok=True)
    path = destination / f"publication-audit-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)
    return path


def summary(value: dict[str, Any]) -> dict[str, Any]:
    current, history = value["current_tree"], value["history"]
    return {
        "status": value["classification"]["status"],
        "tracked_files": current["tracked_file_count"],
        "private_files": len(current["private_files"]),
        "current_finding_categories": len(current["sensitive_findings"]),
        "history_commits": history["commit_count"],
        "history_finding_categories": len(history["sensitive_findings"]),
        "missing_governance_files": current["missing_governance_files"],
        "blockers": value["classification"]["blockers"],
        "publication_authorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate publication audit policy")
    inspect_parser = subparsers.add_parser("inspect", help="write a path/count-only audit to machine-local state")
    add_state_dir_argument(inspect_parser)
    args = parser.parse_args()
    if args.command == "validate":
        result = validate()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "passed" else 1
    try:
        value = inspect()
        path = _write_record(resolve_state_dir(args.state_dir), value)
        print(json.dumps({"record": str(path), "summary": summary(value)}, ensure_ascii=False, indent=2))
        return 0
    except PublicationAuditError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
