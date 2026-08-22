#!/usr/bin/env python3
# Mutation action ID: supply-chain.capture
"""Validate installation sources and optionally capture current supply state."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any, Callable

from config_layers import load_app_catalog, load_json
import pnpm_global
from state_paths import add_state_dir_argument, resolve_state_dir


ROOT = Path(__file__).resolve().parents[1]
BASE_CATALOG = ROOT / "references/mac-app-catalog.json"
PRIVATE_OVERLAY = ROOT / "Private/app-catalog-overlay.json"
POLICY_PATH = ROOT / "references/source-policy.json"
CONFIRM_CAPTURE = "CAPTURE SUPPLY CHAIN STATE"
FULL_REVISION = re.compile(r"^[0-9a-f]{40}$")
EXACT_VERSION = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
ACTIVE_EXECUTION_PATTERNS = (
    ("curl_pipe_shell", re.compile(r"curl[^\n]*(?:\|\s*(?:bash|sh)\b|bash\s*<\()", re.IGNORECASE)),
    ("curl_process_substitution", re.compile(r"bash\s*<\(curl", re.IGNORECASE)),
    ("github_mutable_branch", re.compile(r"raw\.githubusercontent\.com/[^\s)]+/refs/heads/", re.IGNORECASE)),
    ("homebrew_head_bootstrap", re.compile(r"Homebrew/install/HEAD/install\.sh", re.IGNORECASE)),
)


def classify(app: dict[str, Any]) -> str:
    if app.get("runtime_manager"):
        return "version_manager_runtime"
    if app.get("delivery_method") == "playcover-ipa":
        return "decrypted_ipa"
    if app.get("system_app"):
        return "system_app"
    if app.get("app_store_url"):
        return "app_store"
    if app.get("brew_cask") or app.get("brew_formula"):
        token = str(app.get("brew_cask") or app.get("brew_formula"))
        return "third_party_homebrew" if app.get("brew_tap") or token.count("/") >= 2 else "official_homebrew"
    if app.get("npm_package"):
        return "npm_global"
    if app.get("source") == "github" or app.get("delivery_method") == "github-source":
        return "github_source"
    if app.get("delivery_method") in {"webcatalog-wrapper", "web-app-shortcut"}:
        return "web_wrapper"
    if app.get("delivery_method") == "browser-extension":
        return "browser_extension"
    return "official_web"


def tap_for(app: dict[str, Any]) -> str | None:
    if app.get("brew_tap"):
        return str(app["brew_tap"]).casefold()
    token = str(app.get("brew_cask") or app.get("brew_formula") or "")
    parts = token.split("/")
    return "/".join(parts[:2]).casefold() if len(parts) >= 3 else None


def package_for(app: dict[str, Any]) -> str | None:
    return app.get("brew_cask") or app.get("brew_formula") or app.get("npm_package")


def provenance_for(app: dict[str, Any]) -> dict[str, Any]:
    result = {
        "source_class": classify(app),
        "package": package_for(app),
        "official_url": app.get("official_url"),
    }
    for key in (
        "brew_tap",
        "brew_tap_revision",
        "brew_tap_repository",
        "brew_trust_cask",
        "npm_version",
        "github_revision",
        "artifact_sha256",
        "ios_app_store_url",
        "bundle_identifiers",
        "runtime_manager",
        "runtime_version",
        "npm_runtime_manager",
        "npm_runtime_version",
        "npm_install_client",
        "npm_lifecycle_policy",
        "npm_allowed_builds",
    ):
        if app.get(key) is not None:
            result[key] = app[key]
    return result


def _execution_findings(root: Path) -> list[dict[str, Any]]:
    findings = []
    paths = [
        *sorted((root / "scripts").glob("*.py")),
        *sorted((root / "scripts").glob("*.sh")),
        *sorted((root / "components").glob("*.md")),
        *sorted((root / "references").glob("*.md")),
        *(path for path in (root / "README.md", root / "SKILL.md") if path.is_file()),
    ]
    for path in paths:
        if path.resolve() == Path(__file__).resolve():
            continue
        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            for code, pattern in ACTIVE_EXECUTION_PATTERNS:
                if pattern.search(line):
                    findings.append(
                        {
                            "code": code,
                            "path": str(path.relative_to(root)),
                            "line": line_number,
                            "text": line.strip(),
                        }
                    )
    return findings


def validate(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    policy = load_json(root / "references/source-policy.json")
    base = load_json(root / "references/mac-app-catalog.json")
    overlay_path = root / "Private/app-catalog-overlay.json"
    merged = load_app_catalog(
        root / "references/mac-app-catalog.json",
        overlay_path,
    )
    overlay = load_json(overlay_path) if overlay_path.is_file() else {"apps": {}}
    errors: list[str] = []
    warnings: list[str] = []
    classes = Counter()
    if policy.get("schema_version") != 1:
        errors.append("source policy schema_version must be 1")
    known_classes = set(policy.get("source_classes", {}))
    managed_taps = set(policy.get("third_party_homebrew", {}))
    observed_taps = policy.get("observed_unmanaged_homebrew", {})
    allowed_review_statuses = {
        "catalog_or_remove",
        "retirement_cleanup_candidate",
        "managed_by_mpia_project",
    }
    for tap, entry in observed_taps.items():
        if tap in managed_taps:
            errors.append(f"{tap}: tap cannot be both managed and observed-unmanaged")
        if not str(entry.get("repository", "")).startswith("https://"):
            errors.append(f"{tap}: observed tap repository must use HTTPS")
        if not FULL_REVISION.fullmatch(str(entry.get("observed_revision", ""))):
            errors.append(f"{tap}: observed tap revision must be a full commit")
        if entry.get("review_status") not in allowed_review_statuses:
            errors.append(f"{tap}: observed tap review_status is invalid")
    for app in merged.get("apps", []):
        name = str(app.get("name"))
        source_class = classify(app)
        classes[source_class] += 1
        if source_class not in known_classes:
            errors.append(f"{name}: unknown source class {source_class}")
        for key in ("official_url", "ios_app_store_url"):
            value = app.get(key)
            if value and not str(value).startswith("https://"):
                errors.append(f"{name}: {key} must use HTTPS")
        if source_class == "app_store":
            value = str(app.get("app_store_url", ""))
            if not re.match(r"^macappstore://itunes\.apple\.com/app/id\d+$", value):
                errors.append(f"{name}: app_store_url must be a numeric macappstore URL")
        elif source_class == "third_party_homebrew":
            tap = tap_for(app)
            entry = policy.get("third_party_homebrew", {}).get(tap or "")
            if not entry:
                errors.append(f"{name}: third-party tap is not allowlisted: {tap}")
                continue
            if app.get("brew_tap_revision") != entry.get("reviewed_revision"):
                errors.append(f"{name}: catalog tap revision does not match policy")
            if app.get("brew_tap_repository") != entry.get("repository"):
                errors.append(f"{name}: catalog tap repository does not match policy")
            package = str(app.get("brew_cask") or app.get("brew_formula"))
            if package not in entry.get("packages", []):
                errors.append(f"{name}: package is not allowlisted for {tap}")
            trust_scope = entry.get("trust", {}).get("scope")
            if trust_scope == "tap":
                # Tap-wide trust is allowed only when the policy entry declares it
                # deliberately. It auto-loads any future cask the tap gains, so it
                # is reserved for first-party taps and must be recorded as such.
                if not entry.get("first_party"):
                    errors.append(f"{name}: tap-scoped trust requires first_party in policy")
                if app.get("brew_trust_tap") != tap:
                    errors.append(f"{name}: brew_trust_tap must name the trusted tap")
            elif app.get("brew_trust_cask") != package:
                errors.append(f"{name}: trust must be scoped to the exact cask")
        elif source_class == "npm_global":
            package = str(app.get("npm_package"))
            npm_policy = policy.get("npm_globals", {}).get(package, {})
            expected = npm_policy.get("version")
            if not EXACT_VERSION.fullmatch(str(app.get("npm_version", ""))):
                errors.append(f"{name}: npm_version must be exact")
            elif app.get("npm_version") != expected:
                errors.append(f"{name}: npm_version does not match source policy")
            for key in ("install_client", "lifecycle_policy", "allowed_builds"):
                catalog_key = f"npm_{key}"
                if app.get(catalog_key) != npm_policy.get(key):
                    errors.append(f"{name}: {catalog_key} does not match source policy")
        elif source_class == "github_source":
            entry = policy.get("github_sources", {}).get(name)
            if not entry:
                errors.append(f"{name}: GitHub source is not allowlisted")
                continue
            if app.get("github_revision") != entry.get("revision"):
                errors.append(f"{name}: GitHub revision does not match source policy")
            if app.get("artifact_sha256") != entry.get("sha256"):
                errors.append(f"{name}: GitHub artifact SHA-256 does not match policy")
        elif source_class == "decrypted_ipa":
            public = next((row for row in base.get("apps", []) if row.get("name") == name), {})
            private = overlay.get("apps", {}).get(name, {})
            if public.get("preferred_source") or public.get("download_url"):
                errors.append(f"{name}: personal IPA source must not be in public catalog")
            if overlay_path.is_file() and (
                private.get("source_type") != "decrypted_ipa"
                or not private.get("approved_source_label")
            ):
                errors.append(f"{name}: Private approved decrypted-IPA source is missing")
            elif not overlay_path.is_file():
                warnings.append(
                    f"{name}: personal IPA source is unavailable in public-only mode"
                )
            if private.get("download_url"):
                errors.append(f"{name}: direct IPA URL must not be tracked")
        if source_class == "official_web" and app.get("tier") == "core":
            warnings.append(f"{name}: capture final URL, SHA-256, codesign, and spctl at install time")
    execution_findings = _execution_findings(root)
    errors.extend(
        f"{row['path']}:{row['line']}: prohibited {row['code']}"
        for row in execution_findings
    )
    return {
        "status": "passed" if not errors else "failed",
        "apps": len(merged.get("apps", [])),
        "source_classes": dict(sorted(classes.items())),
        "errors": errors,
        "warnings": warnings,
        "execution_findings": execution_findings,
    }


def _run_json(
    command: list[str],
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> Any:
    completed = runner(command, capture_output=True, text=True, check=False)
    if completed.returncode:
        return {"unavailable": True, "command": command, "error": completed.stderr.strip()}
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {"unavailable": True, "command": command, "error": "invalid JSON"}


def inspect_live(
    *,
    policy_path: Path = POLICY_PATH,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    policy = load_json(policy_path)
    taps_raw = _run_json(["brew", "tap-info", "--json=v1", "--installed"], runner=runner)
    trust = _run_json(["brew", "trust", "--json=v1"], runner=runner)
    npm = _run_json(
        ["fnm", "exec", "--using=24", "npm", "list", "--global", "--depth=0", "--json"],
        runner=runner,
    )
    taps = []
    if isinstance(taps_raw, list):
        for row in taps_raw:
            if not row.get("installed") or row.get("official"):
                continue
            taps.append(
                {
                    "name": str(row.get("name", "")).casefold(),
                    "remote": row.get("remote"),
                    "head": row.get("HEAD"),
                    "trusted": row.get("trusted"),
                }
            )
    expected_taps = policy.get("third_party_homebrew", {})
    by_tap = {row["name"]: row for row in taps}
    tap_results = []
    for name, expected in expected_taps.items():
        observed = by_tap.get(name)
        tap_results.append(
            {
                "name": name,
                "status": (
                    "missing"
                    if not observed
                    else "match"
                    if observed.get("remote") == expected.get("repository")
                    and observed.get("head") == expected.get("reviewed_revision")
                    else "drift"
                ),
                "expected_remote": expected.get("repository"),
                "expected_revision": expected.get("reviewed_revision"),
                "observed": observed,
            }
        )
    dependencies = npm.get("dependencies", {}) if isinstance(npm, dict) else {}
    needs_pnpm = any(
        row.get("install_client") == "pnpm"
        for row in policy.get("npm_globals", {}).values()
    )
    try:
        pnpm_dependencies = pnpm_global.global_packages("24", runner=runner) if needs_pnpm else {}
    except (RuntimeError, ValueError):
        pnpm_dependencies = {}
    npm_results = []
    for package, expected in policy.get("npm_globals", {}).items():
        client = expected.get("install_client", "npm")
        observed = (
            pnpm_dependencies.get(package)
            if client == "pnpm"
            else dependencies.get(package, {}).get("version")
        )
        npm_results.append(
            {
                "package": package,
                "install_client": client,
                "expected_version": expected.get("version"),
                "observed_version": observed,
                "status": "match" if observed == expected.get("version") else "missing" if not observed else "drift",
            }
        )
    expected_names = set(expected_taps)
    observed_unmanaged = policy.get("observed_unmanaged_homebrew", {})
    unmanaged_results = []
    for name, expected in observed_unmanaged.items():
        observed = by_tap.get(name)
        unmanaged_results.append(
            {
                "name": name,
                "status": (
                    "missing"
                    if not observed
                    else "observed_match"
                    if observed.get("remote") == expected.get("repository")
                    and observed.get("head") == expected.get("observed_revision")
                    else "observed_drift"
                ),
                "review_status": expected.get("review_status"),
                "installed_package": expected.get("installed_package"),
                "observed": observed,
            }
        )
    known_names = expected_names | set(observed_unmanaged)
    return {
        "schema_version": 1,
        "mode": "read_only_supply_chain_observation",
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "expected_taps": tap_results,
        "observed_unmanaged_taps": unmanaged_results,
        "unknown_installed_taps": [row for row in taps if row["name"] not in known_names],
        "trust": trust,
        "npm_globals": npm_results,
        "status": (
            "passed"
            if all(row["status"] == "match" for row in tap_results + npm_results)
            else "drift"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_state_dir_argument(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate tracked source policy")
    subparsers.add_parser("inspect", help="read current tap/trust/npm state")
    capture = subparsers.add_parser("capture", help="write current observation to machine-local state")
    capture.add_argument("--apply", action="store_true")
    capture.add_argument("--confirm", default="")
    args = parser.parse_args()
    if args.command == "validate":
        result = validate()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "passed" else 1
    if args.command == "capture" and args.apply and args.confirm != CONFIRM_CAPTURE:
        parser.error(f'--apply requires --confirm "{CONFIRM_CAPTURE}"')
    result = inspect_live()
    if args.command == "inspect":
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "passed" else 2
    preview = {"action_id": "supply-chain.capture", **result}
    if not args.apply:
        print(json.dumps({**preview, "record_status": "planned"}, ensure_ascii=False, indent=2))
        return 0
    state_dir = resolve_state_dir(args.state_dir)
    state_dir.mkdir(parents=True, exist_ok=True)
    output = state_dir / f"supply-chain-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps({**preview, "record_status": "recorded"}, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"output": str(output), **preview, "record_status": "recorded"}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
