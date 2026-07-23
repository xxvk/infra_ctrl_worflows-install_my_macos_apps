#!/usr/bin/env python3
# Mutation action ID: diagnostics.export
"""Preview or export a bounded, redacted macomrade diagnostic ZIP."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

from schema_contract import SchemaContractError, validate_document


ROOT = Path(__file__).resolve().parents[1]
ACTION_ID = "diagnostics.export"
EXPORT_CONFIRMATION = "EXPORT REDACTED DIAGNOSTICS"
LOG_LIMIT_BYTES = 4096
POLICY_PATHS = (
    "references/source-policy.json",
    "references/schema-registry.json",
    "references/mutation-contracts.json",
    "references/release-acceptance-matrix.json",
    "settings/bootstrap-operational-baseline.yaml",
    "settings/privacy.yaml",
)
IMPLEMENTATION_PATHS = (
    "bin/macomrade",
    "scripts/macomrade.py",
    "scripts/diagnostic_bundle.py",
    "schemas/diagnostic-bundle-v1.schema.json",
    "references/schema-registry.json",
    "references/redacted-diagnostic-bundle.md",
)
CHECKS = (
    ("cli-contract", ("scripts/macomrade.py", "validate", "--json")),
    ("schema-contract", ("scripts/schema_contract.py", "validate-tracked")),
    ("configuration-layers", ("scripts/config_layers.py", "audit")),
    ("release-contract", ("scripts/validate_release_contract.py",)),
    ("mutation-contracts", ("scripts/validate_mutation_contracts.py",)),
    ("bootstrap-definition", ("scripts/bootstrap_validate.py",)),
)
EXCLUDED_CATEGORIES = (
    "credentials",
    "account and session data",
    "private filenames and content",
    "raw TCC databases",
    "Private configuration values",
    "machine-local state records",
)
SECRET_KEYS = {
    "access_token",
    "api_key",
    "authorization",
    "cookie",
    "cookies",
    "credential",
    "credentials",
    "password",
    "private_key",
    "recovery_code",
    "refresh_token",
    "secret",
    "session",
    "session_token",
}
ACCOUNT_KEYS = {
    "account",
    "accounts",
    "apple_id",
    "email",
    "emails",
    "owner",
    "preferred_account",
    "user",
    "user_name",
    "username",
}
HOST_KEYS = {"computer_name", "host", "hostname", "machine_name"}
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
SECRET_RE = re.compile(
    r"(?i)(?:"
    r"\bbearer\s+[A-Za-z0-9._~+/=-]{12,}|"
    r"\bsk-[A-Za-z0-9_-]{12,}|"
    r"\bghp_[A-Za-z0-9]{20,}|"
    r"\bgithub_pat_[A-Za-z0-9_]{20,}|"
    r"\bxox[baprs]-[A-Za-z0-9-]{12,}|"
    r"\bAKIA[A-Z0-9]{16}|"
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----"
    r")"
)
CREDENTIAL_ASSIGNMENT_RE = re.compile(
    r"""(?ix)
    \b(?:access[_-]?token|refresh[_-]?token|session[_-]?token|
    api[_-]?key|password|private[_-]?key|cookie|authorization|secret)
    \b\s*[:=]\s*["']?[^,\s"'}]+
    """
)
ACCOUNT_ASSIGNMENT_RE = re.compile(
    r"""(?ix)
    \b(?:preferred[_-]?account|apple[_-]?id|email|username|owner)
    \b\s*[:=]\s*["']?[^,\s"'}]+
    """
)
URL_QUERY_RE = re.compile(r"(https?://[^\s?#\"']+)\?[^\s#\"']+(?:#[^\s\"']*)?")
HOME_PATH_RE = re.compile(r"/Users/[^/\s\"']+(?:/[^\n\r\"']*)?")
TMP_PATH_RE = re.compile(r"/(?:private/)?var/folders/[^\s\"']+")
PRIVATE_CONFIG_PATH_RE = re.compile(r"(?<![A-Za-z0-9_-])Private/[^\s\"']+")


class DiagnosticBundleError(RuntimeError):
    """Raised when collection, redaction, or export cannot be verified."""


def json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def normalized_key(value: Any) -> str:
    return str(value).strip().casefold().replace("-", "_").replace(" ", "_")


def secret_key(value: str) -> bool:
    return (
        value in SECRET_KEYS
        or value.endswith("_token")
        or value.endswith("_password")
        or value.endswith("_secret")
        or value.endswith("_cookie")
    )


def account_key(value: str) -> bool:
    return (
        value in ACCOUNT_KEYS
        or value.endswith("_email")
        or value.endswith("_account")
        or value.endswith("_username")
    )


def redact_text(
    value: str,
    *,
    root: Path = ROOT,
    counts: Counter[str] | None = None,
) -> str:
    counts = counts if counts is not None else Counter()
    root_text = str(root.resolve())
    if root_text in value:
        value = value.replace(root_text, "<REPO>")
        counts["repository_paths"] += 1

    replacements = (
        (CREDENTIAL_ASSIGNMENT_RE, "<redacted-credential>", "credential_text"),
        (ACCOUNT_ASSIGNMENT_RE, "<redacted-account>", "account_text"),
        (SECRET_RE, "<redacted-secret>", "secret_text"),
        (EMAIL_RE, "<redacted-email>", "email_values_redacted"),
        (URL_QUERY_RE, r"\1?<redacted-query>", "url_queries"),
        (HOME_PATH_RE, "<HOME>/<redacted-path>", "private_paths"),
        (TMP_PATH_RE, "<TMP>/<redacted-path>", "temporary_paths"),
        (
            PRIVATE_CONFIG_PATH_RE,
            "<PRIVATE-CONFIG>/<redacted-path>",
            "private_config_paths",
        ),
    )
    for pattern, replacement, counter in replacements:
        value, changed = pattern.subn(replacement, value)
        counts[counter] += changed
    return value


def sanitize_value(
    value: Any,
    *,
    root: Path = ROOT,
    counts: Counter[str] | None = None,
) -> Any:
    counts = counts if counts is not None else Counter()
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            normalized = normalized_key(key)
            if secret_key(normalized):
                counts["credential_fields_removed"] += 1
                continue
            if account_key(normalized):
                counts["account_fields_removed"] += 1
                continue
            if normalized in HOST_KEYS:
                counts["host_fields_removed"] += 1
                continue
            result[key] = sanitize_value(child, root=root, counts=counts)
        return result
    if isinstance(value, list):
        return [sanitize_value(child, root=root, counts=counts) for child in value]
    if isinstance(value, str):
        return redact_text(value, root=root, counts=counts)
    return value


def sensitive_findings(value: Any) -> list[str]:
    findings: list[str] = []

    def walk(child: Any, path: str) -> None:
        if isinstance(child, dict):
            for key, nested in child.items():
                normalized = normalized_key(key)
                if secret_key(normalized) or account_key(normalized) or normalized in HOST_KEYS:
                    findings.append(f"{path}.{key}: sensitive key")
                walk(nested, f"{path}.{key}")
        elif isinstance(child, list):
            for index, nested in enumerate(child):
                walk(nested, f"{path}[{index}]")
        elif isinstance(child, str):
            if EMAIL_RE.search(child):
                findings.append(f"{path}: email")
            if SECRET_RE.search(child) or CREDENTIAL_ASSIGNMENT_RE.search(child):
                findings.append(f"{path}: credential text")
            if "/Users/" in child:
                findings.append(f"{path}: private home path")
            if URL_QUERY_RE.search(child):
                findings.append(f"{path}: URL query")
            if "TCC.db" in child or "com.apple.TCC" in child:
                findings.append(f"{path}: raw TCC path")
            if PRIVATE_CONFIG_PATH_RE.search(child):
                findings.append(f"{path}: Private configuration path")

    walk(value, "$")
    return findings


def bounded_tail(
    text: str,
    *,
    limit: int = LOG_LIMIT_BYTES,
) -> tuple[str, int, bool]:
    raw = text.encode("utf-8", errors="replace")
    truncated = len(raw) > limit
    tail = raw[-limit:] if truncated else raw
    return tail.decode("utf-8", errors="replace"), len(raw), truncated


def classify_failure(returncode: int, stderr: str) -> str | None:
    if returncode == 0:
        return None
    lowered = stderr.casefold()
    if "timed out" in lowered:
        return "timeout"
    if "permission denied" in lowered or "operation not permitted" in lowered:
        return "permission_denied"
    if "no such file" in lowered or "not found" in lowered:
        return "dependency_unavailable"
    if "invalid" in lowered or "validation" in lowered or "contract" in lowered:
        return "contract_failure"
    return "command_failed"


def run_check(
    check_id: str,
    args: tuple[str, ...],
    *,
    root: Path = ROOT,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    python: str = sys.executable,
) -> dict[str, Any]:
    command = [python, *args]
    try:
        completed = runner(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        returncode = completed.returncode
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
    except subprocess.TimeoutExpired as exc:
        returncode = 124
        stdout = str(exc.stdout or "")
        stderr = f"command timed out after {exc.timeout} seconds"
    except OSError as exc:
        returncode = 127
        stdout = ""
        stderr = f"command unavailable: {exc}"
    stdout_tail, stdout_bytes, stdout_truncated = bounded_tail(stdout)
    stderr_tail, stderr_bytes, stderr_truncated = bounded_tail(stderr)
    return {
        "id": check_id,
        "status": "passed" if returncode == 0 else "failed",
        "returncode": returncode,
        "command": ["python3", *args],
        "failure_class": classify_failure(returncode, stderr),
        "log": {
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
            "stdout_bytes": stdout_bytes,
            "stderr_bytes": stderr_bytes,
            "truncated": stdout_truncated or stderr_truncated,
        },
    }


def run_version(
    command: list[str],
    *,
    root: Path = ROOT,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    try:
        completed = runner(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"
    if completed.returncode != 0:
        return "unavailable"
    first = (completed.stdout or completed.stderr or "").strip().splitlines()
    return first[0] if first else "unavailable"


def implementation_hashes(root: Path = ROOT) -> list[dict[str, Any]]:
    rows = []
    for relative in IMPLEMENTATION_PATHS:
        path = root / relative
        rows.append(
            {
                "path": relative,
                "sha256": sha256_path(path) if path.is_file() else "unavailable",
                "bytes": path.stat().st_size if path.is_file() else 0,
                "status": "hashed_without_content" if path.is_file() else "missing",
            }
        )
    return rows


def source_revision(
    *,
    root: Path = ROOT,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    try:
        guard = runner(
            [
                sys.executable,
                "scripts/icloud_git_guard.py",
                "inspect",
                "--repo",
                ".",
            ],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {
            "guard": "unavailable",
            "revision": "unavailable",
            "worktree_status": "unavailable",
            "change_count": None,
            "implementation_hashes": implementation_hashes(root),
        }
    if guard.returncode != 0 or not re.search(
        r"^status:\s*ready\s*$",
        guard.stdout or "",
        flags=re.MULTILINE,
    ):
        return {
            "guard": "unavailable",
            "revision": "unavailable",
            "worktree_status": "unavailable",
            "change_count": None,
            "implementation_hashes": implementation_hashes(root),
        }
    try:
        revision = runner(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {
            "guard": "ready",
            "revision": "unavailable",
            "worktree_status": "unavailable",
            "change_count": None,
            "implementation_hashes": implementation_hashes(root),
        }
    value = (revision.stdout or "").strip()
    if revision.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", value):
        value = "unavailable"
    try:
        status = runner(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        status = None
    if status is None or status.returncode != 0:
        worktree_status = "unavailable"
        change_count = None
    else:
        change_count = len(
            [line for line in (status.stdout or "").splitlines() if line.strip()]
        )
        worktree_status = "dirty" if change_count else "clean"
    return {
        "guard": "ready",
        "revision": value,
        "worktree_status": worktree_status,
        "change_count": change_count,
        "implementation_hashes": implementation_hashes(root),
    }


def policy_hashes(root: Path = ROOT) -> list[dict[str, Any]]:
    rows = []
    for relative in POLICY_PATHS:
        path = root / relative
        if not path.is_file():
            rows.append(
                {
                    "path": relative,
                    "sha256": "unavailable",
                    "bytes": 0,
                    "status": "missing",
                }
            )
            continue
        rows.append(
            {
                "path": relative,
                "sha256": sha256_path(path),
                "bytes": path.stat().st_size,
                "status": "hashed_without_content",
            }
        )
    return rows


def aggregate_failures(checks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for row in checks:
        failure = row.get("failure_class")
        if failure:
            grouped[str(failure)].append(str(row["id"]))
    return [
        {"class": name, "count": len(ids), "check_ids": sorted(ids)}
        for name, ids in sorted(grouped.items())
    ]


def validate_definition(root: Path = ROOT) -> dict[str, Any]:
    errors = []
    for relative in POLICY_PATHS:
        if relative.startswith(("Private/", "state/")):
            errors.append(f"diagnostic policy path is private or machine-local: {relative}")
        if not (root / relative).is_file():
            errors.append(f"diagnostic policy path not found: {relative}")
    for check_id, args in CHECKS:
        script = args[0] if args else ""
        if not script.startswith("scripts/") or not (root / script).is_file():
            errors.append(f"{check_id}: diagnostic check script not found: {script}")
        if script in {
            "scripts/release_check.py",
            "scripts/macos_permissions.py",
        }:
            errors.append(f"{check_id}: recursive or TCC-bearing check is prohibited")
    if LOG_LIMIT_BYTES > 4096:
        errors.append("diagnostic log limit must not exceed 4096 bytes per stream")
    fixture = root / "tests/fixtures/schema_contract/diagnostic-bundle-v1.json"
    try:
        fixture_value = json.loads(fixture.read_text(encoding="utf-8"))
        errors.extend(validate_document(fixture_value, "diagnostic-bundle", root=root))
    except (OSError, json.JSONDecodeError, SchemaContractError) as exc:
        errors.append(f"diagnostic bundle fixture is invalid: {exc}")
    return {
        "schema_version": 1,
        "status": "passed" if not errors else "failed",
        "checks": len(CHECKS),
        "policy_hashes": len(POLICY_PATHS),
        "log_limit_bytes": LOG_LIMIT_BYTES,
        "errors": errors,
    }


def collect(
    *,
    root: Path = ROOT,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    now: Callable[[], dt.datetime] = lambda: dt.datetime.now(dt.timezone.utc),
) -> dict[str, Any]:
    checks = [
        run_check(check_id, args, root=root, runner=runner)
        for check_id, args in CHECKS
    ]
    brew = shutil.which("brew")
    raw = {
        "schema_version": 1,
        "kind": "redacted_diagnostic_bundle",
        "captured_at": now().isoformat(),
        "product": {
            "version": (root / "VERSION").read_text(encoding="utf-8").strip(),
            "cli_version": run_version(
                [str(root / "bin" / "macomrade"), "--version"],
                root=root,
                runner=runner,
            ),
            "source": source_revision(root=root, runner=runner),
        },
        "platform": {
            "macos_version": run_version(
                ["sw_vers", "-productVersion"],
                root=root,
                runner=runner,
            ),
            "architecture": run_version(["uname", "-m"], root=root, runner=runner),
            "python_version": platform.python_version(),
            "homebrew_version": (
                run_version([brew, "--version"], root=root, runner=runner)
                if brew
                else "unavailable"
            ),
        },
        "checks": checks,
        "failure_classes": aggregate_failures(checks),
        "policy_hashes": policy_hashes(root),
    }
    counts: Counter[str] = Counter()
    sanitized = sanitize_value(raw, root=root, counts=counts)
    truncated = sum(
        1
        for row in sanitized["checks"]
        if row.get("log", {}).get("truncated")
    )
    if truncated:
        counts["bounded_logs_truncated"] += truncated
    sanitized["redaction"] = {
        "applied": True,
        "counts": dict(sorted(counts.items())),
        "excluded_categories": list(EXCLUDED_CATEGORIES),
        "log_limit_bytes": LOG_LIMIT_BYTES,
        "source_scope": "Controlled commands and public tracked policy hashes only.",
    }
    findings = sensitive_findings(sanitized)
    if findings:
        raise DiagnosticBundleError(
            "redaction verification failed: " + "; ".join(findings)
        )
    try:
        schema_errors = validate_document(sanitized, "diagnostic-bundle", root=root)
    except SchemaContractError as exc:
        raise DiagnosticBundleError(str(exc)) from exc
    if schema_errors:
        raise DiagnosticBundleError(
            "diagnostic bundle schema validation failed: " + "; ".join(schema_errors)
        )
    return sanitized


def build_artifacts(diagnostics: dict[str, Any]) -> tuple[dict[str, bytes], dict[str, Any]]:
    report = {
        "schema_version": 1,
        "kind": "diagnostic_redaction_report",
        "captured_at": diagnostics["captured_at"],
        **diagnostics["redaction"],
        "verification": "No sensitive pattern remained after sanitization.",
    }
    artifacts = {
        "diagnostics.json": json_bytes(diagnostics),
        "redaction-report.json": json_bytes(report),
    }
    manifest = {
        "schema_version": 1,
        "kind": "redacted_diagnostic_bundle_manifest",
        "captured_at": diagnostics["captured_at"],
        "files": [
            {
                "name": name,
                "sha256": sha256_bytes(payload),
                "bytes": len(payload),
            }
            for name, payload in sorted(artifacts.items())
        ],
        "policy": {
            "local_payload_review_required": True,
            "sharing_authorized": False,
            "contains_private_payload_content": False,
            "contains_credentials": False,
            "contains_raw_tcc_database": False,
        },
    }
    return artifacts, manifest


def build_zip(artifacts: dict[str, bytes], manifest: dict[str, Any]) -> bytes:
    stream = io.BytesIO()
    members = {**artifacts, "manifest.json": json_bytes(manifest)}
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, payload)
    return stream.getvalue()


def verify_zip(payload: bytes) -> dict[str, Any]:
    try:
        with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
            names = sorted(archive.namelist())
            if names != ["diagnostics.json", "manifest.json", "redaction-report.json"]:
                raise DiagnosticBundleError("diagnostic ZIP has unexpected members")
            manifest = json.loads(archive.read("manifest.json"))
            manifest_names = sorted(
                row.get("name")
                for row in manifest.get("files", [])
                if isinstance(row, dict)
            )
            if manifest_names != ["diagnostics.json", "redaction-report.json"]:
                raise DiagnosticBundleError(
                    "diagnostic manifest has unexpected file rows"
                )
            for row in manifest.get("files", []):
                content = archive.read(row["name"])
                if len(content) != row["bytes"] or sha256_bytes(content) != row["sha256"]:
                    raise DiagnosticBundleError(
                        f"diagnostic ZIP hash mismatch: {row['name']}"
                    )
            diagnostics = json.loads(archive.read("diagnostics.json"))
            findings = sensitive_findings(diagnostics)
            if findings:
                raise DiagnosticBundleError(
                    "exported diagnostics failed redaction read-back"
                )
    except (KeyError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
        raise DiagnosticBundleError(f"invalid diagnostic ZIP: {exc}") from exc
    return {
        "members": names,
        "manifest_files": len(manifest["files"]),
        "verified": True,
    }


def preview(
    diagnostics: dict[str, Any],
    *,
    output: Path | None = None,
) -> dict[str, Any]:
    artifacts, manifest = build_artifacts(diagnostics)
    redaction_report = json.loads(artifacts["redaction-report.json"])
    payload = build_zip(artifacts, manifest)
    verification = verify_zip(payload)
    return {
        "schema_version": 1,
        "status": "preview",
        "output": (
            redact_text(str(output.expanduser().resolve()))
            if output
            else None
        ),
        "check_summary": {
            "passed": sum(row["status"] == "passed" for row in diagnostics["checks"]),
            "failed": sum(row["status"] == "failed" for row in diagnostics["checks"]),
        },
        "failure_classes": diagnostics["failure_classes"],
        "policy_hashes": len(diagnostics["policy_hashes"]),
        "redaction_preview": diagnostics["redaction"],
        "manifest": manifest,
        "payload_preview": {
            "diagnostics": diagnostics,
            "redaction_report": redaction_report,
        },
        "predicted_zip": {
            "bytes": len(payload),
            "sha256": sha256_bytes(payload),
            **verification,
        },
        "export_authorized": False,
    }


def export(
    diagnostics: dict[str, Any],
    output: Path,
    *,
    confirmation: str,
) -> dict[str, Any]:
    if confirmation != EXPORT_CONFIRMATION:
        raise DiagnosticBundleError(
            f"confirmation must be exactly {EXPORT_CONFIRMATION!r}"
        )
    output = output.expanduser().resolve()
    if output.suffix.casefold() != ".zip":
        raise DiagnosticBundleError("diagnostic export output must end in .zip")
    if not output.parent.is_dir():
        raise DiagnosticBundleError(
            f"diagnostic export directory does not exist: {output.parent}"
        )
    artifacts, manifest = build_artifacts(diagnostics)
    payload = build_zip(artifacts, manifest)
    verify_zip(payload)
    temporary = output.with_name(f".{output.name}.tmp-{os.getpid()}")
    try:
        with temporary.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, output)
        except FileExistsError as exc:
            raise DiagnosticBundleError(
                f"refusing to overwrite existing output: {output}"
            ) from exc
    finally:
        if temporary.exists():
            temporary.unlink()
    readback = output.read_bytes()
    if readback != payload:
        raise DiagnosticBundleError("diagnostic ZIP read-back differs from export plan")
    verification = verify_zip(readback)
    return {
        "schema_version": 1,
        "action_id": ACTION_ID,
        "status": "exported",
        "output": redact_text(str(output)),
        "bytes": len(readback),
        "sha256": sha256_bytes(readback),
        **verification,
        "publication_authorized": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")
    preview_parser = subparsers.add_parser("preview")
    preview_parser.add_argument("--output", type=Path)
    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--output", type=Path, required=True)
    export_parser.add_argument("--apply", action="store_true")
    export_parser.add_argument("--confirm")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "validate":
            result = validate_definition()
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["status"] == "passed" else 1
        diagnostics = collect()
        if args.command == "preview":
            print(
                json.dumps(
                    preview(diagnostics, output=args.output),
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if not args.apply:
            raise DiagnosticBundleError(
                "export is preview-only without --apply; run the preview command first"
            )
        result = export(
            diagnostics,
            args.output,
            confirmation=args.confirm or "",
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except DiagnosticBundleError as exc:
        print(f"diagnostic bundle error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
