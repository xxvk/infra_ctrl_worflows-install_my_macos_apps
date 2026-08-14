#!/usr/bin/env python3
"""Build a deterministic, non-authorizing release-candidate manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

from schema_contract import SchemaContractError, load_registry, schema_for, validate_instance
from state_paths import add_state_dir_argument, resolve_state_dir


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_INPUTS = (
    "VERSION",
    "references/app-catalog.json",
    "references/release-acceptance-matrix.json",
    "references/schema-registry.json",
    "references/source-policy.json",
    "references/mutation-contracts.json",
    "settings/privacy.yaml",
    "settings/machine-roles.json",
    "settings/performance-budgets.json",
    "settings/publication-audit-policy.json",
    "settings/storage-policy.json",
)
PLATFORM_SUPPORT = (
    {
        "host": "apple_silicon_public_macos",
        "status": "primary_release_candidate",
        "boundary": "Live behavior depends on applications, permissions, accounts, and hardware.",
    },
    {
        "host": "apple_silicon_prerelease_macos",
        "status": "best_effort",
        "boundary": "Beta results are not stable-platform release evidence.",
    },
    {
        "host": "intel_macos",
        "status": "unverified",
        "boundary": "No completed Intel acceptance run.",
    },
    {
        "host": "linux_or_windows_managed_host",
        "status": "unsupported",
        "boundary": "macOS host integrations are required.",
    },
)
KNOWN_LIMITATIONS = (
    "No stable tag or published release exists.",
    "A genuine unused Clean-Mac acceptance run remains externally deferred.",
    "Intel Mac behavior is unverified.",
    "Protected permissions, credentials, purchases, and security confirmations remain interactive.",
    "Not every application source or internal preference has portable verification evidence.",
    "Machine-local effects must be verified independently on every Mac.",
)


class ReleaseManifestError(RuntimeError):
    pass


def canonical_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashed_file(relative: str, *, root: Path = ROOT) -> dict[str, Any]:
    path = root / relative
    if not path.is_file():
        raise ReleaseManifestError(f"required public input is missing: {relative}")
    return {"path": relative, "sha256": sha256_file(path), "bytes": path.stat().st_size}


def release_status(*, root: Path = ROOT) -> str:
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    text = (root / "references/release-roadmap.md").read_text(encoding="utf-8")
    match = re.search(
        rf"## {re.escape(version)}\b.*?^Status: \*\*([^*]+)\*\*",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        raise ReleaseManifestError(f"cannot resolve {version} roadmap status")
    return match.group(1).strip()


def source_provenance(
    *,
    root: Path = ROOT,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    revision = runner(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=False)
    if revision.returncode != 0 or not re.fullmatch(r"[0-9a-fA-F]{40}", revision.stdout.strip()):
        raise ReleaseManifestError("cannot resolve the source commit")
    status = runner(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if status.returncode != 0:
        raise ReleaseManifestError("cannot inspect the candidate worktree")
    changes = [line for line in status.stdout.splitlines() if line]
    return {
        "commit": revision.stdout.strip().lower(),
        "worktree": "dirty" if changes else "clean",
        "change_count": len(changes),
    }


def schema_rows(*, root: Path = ROOT) -> list[dict[str, Any]]:
    registry = load_registry(root / "references/schema-registry.json", root=root)
    rows = []
    for kind, entry in sorted(registry["formats"].items()):
        rows.append(
            {
                "kind": kind,
                "version": entry["current_version"],
                **hashed_file(entry["schema"], root=root),
            }
        )
    return rows


def summarize_release_result(value: dict[str, Any]) -> dict[str, Any]:
    rows = value.get("results", []) if isinstance(value, dict) else []
    return {
        "status": value.get("status", "unavailable") if isinstance(value, dict) else "unavailable",
        "mode": value.get("mode", "unavailable") if isinstance(value, dict) else "unavailable",
        "checks_run": value.get("checks_run", 0) if isinstance(value, dict) else 0,
        "checks": [
            {"id": row.get("id", "unknown"), "status": row.get("status", "failed")}
            for row in rows
            if isinstance(row, dict)
        ],
    }


def summarize_benchmark(value: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"status": "unavailable", "baseline_present": False, "operations": []}
    comparison = value.get("comparison", {})
    operations = []
    for name, row in sorted(value.get("operations", {}).items()):
        if not isinstance(row, dict) or not isinstance(row.get("summary"), dict):
            continue
        summary = row["summary"]
        operations.append(
            {
                "id": name,
                "cold_elapsed_ms": summary.get("cold_elapsed_ms"),
                "warm_elapsed_ms": summary.get("warm_elapsed_ms"),
                "peak_rss_bytes": summary.get("peak_rss_bytes"),
                "output_bytes": summary.get("output_bytes"),
                "state_growth_bytes": summary.get("state_growth_bytes"),
            }
        )
    return {
        "status": comparison.get("status", "unavailable"),
        "baseline_present": bool(comparison.get("baseline_present")),
        "operations": operations,
    }


def latest_benchmark(*, state_dir: Path) -> dict[str, Any] | None:
    paths = sorted((state_dir / "benchmarks").glob("benchmark-*.json"))
    for path in reversed(paths):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict) and value.get("kind") == "performance_benchmark":
            return value
    return None


def run_release_check(
    *,
    root: Path = ROOT,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    completed = runner(
        [sys.executable, "scripts/release_check.py"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ReleaseManifestError("release check did not return JSON") from exc
    if not isinstance(value, dict):
        raise ReleaseManifestError("release check result must be an object")
    return value


def build_manifest(
    *,
    root: Path = ROOT,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    release_result: dict[str, Any] | None = None,
    benchmark: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source = source_provenance(root=root, runner=runner)
    validation = summarize_release_result(release_result or run_release_check(root=root, runner=runner))
    benchmark_summary = summarize_benchmark(benchmark)
    blockers = []
    if source["worktree"] != "clean":
        blockers.append("dirty_worktree")
    if validation["status"] != "passed":
        blockers.append("release_validation_not_passed")
    if benchmark_summary["status"] != "passed":
        blockers.append("benchmark_not_passed_or_unavailable")
    manifest: dict[str, Any] = {
        "schema_version": 1,
        "kind": "macomrade_release_manifest",
        "status": "candidate" if not blockers else "review_required",
        "blockers": blockers,
        "candidate": {
            "version": (root / "VERSION").read_text(encoding="utf-8").strip(),
            "release_status": release_status(root=root),
        },
        "source": source,
        "schemas": schema_rows(root=root),
        "public_inputs": [hashed_file(path, root=root) for path in PUBLIC_INPUTS],
        "platform_support": list(PLATFORM_SUPPORT),
        "validation": validation,
        "benchmark": benchmark_summary,
        "known_limitations": list(KNOWN_LIMITATIONS),
        "artifacts": {
            "distribution": "source_only",
            "files": [],
            "provenance": "No binary, package, archive, tag, or GitHub Release is produced by this preview.",
        },
        "authority": {
            "commit_authorized": False,
            "tag_authorized": False,
            "push_authorized": False,
            "release_authorized": False,
            "visibility_change_authorized": False,
        },
    }
    manifest["manifest_sha256"] = hashlib.sha256(canonical_bytes(manifest)).hexdigest()
    try:
        schema, _entry = schema_for("release-manifest", root=root)
        errors = validate_instance(manifest, schema)
    except SchemaContractError as exc:
        errors = [str(exc)]
    if errors:
        raise ReleaseManifestError("generated manifest is invalid: " + "; ".join(errors))
    return manifest


def preview(manifest: dict[str, Any], *, output: Path | None = None) -> dict[str, Any]:
    return {
        "status": "preview",
        "output_requested": output is not None,
        "manifest": manifest,
        "write_authorized": False,
        "publication_authorized": False,
    }


def validate_definition(*, root: Path = ROOT) -> dict[str, Any]:
    errors = []
    try:
        schema, entry = schema_for("release-manifest", root=root)
        if not entry.get("tracked_examples"):
            errors.append("release-manifest requires a tracked fixture")
        for relative in PUBLIC_INPUTS:
            hashed_file(relative, root=root)
        for relative in entry.get("tracked_examples", []):
            value = json.loads((root / relative).read_text(encoding="utf-8"))
            errors.extend(f"{relative}: {error}" for error in validate_instance(value, schema))
    except (ReleaseManifestError, SchemaContractError, OSError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
    return {
        "schema_version": 1,
        "status": "passed" if not errors else "failed",
        "public_inputs": len(PUBLIC_INPUTS),
        "platform_rows": len(PLATFORM_SUPPORT),
        "known_limitations": len(KNOWN_LIMITATIONS),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")
    preview_parser = subparsers.add_parser("preview")
    preview_parser.add_argument("--output", type=Path, help="show intent only; preview never writes")
    add_state_dir_argument(preview_parser)
    args = parser.parse_args()
    if args.command == "validate":
        result = validate_definition()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "passed" else 1
    try:
        state_dir = resolve_state_dir(args.state_dir)
        result = preview(
            build_manifest(benchmark=latest_benchmark(state_dir=state_dir)),
            output=args.output,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except ReleaseManifestError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
