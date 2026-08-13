#!/usr/bin/env python3
"""Rehearse a credential-free public-only clone of the exact clean commit."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable, Mapping

from state_paths import add_state_dir_argument, resolve_state_dir


ROOT = Path(__file__).resolve().parents[1]
EMAIL_RE = re.compile(r"(?i)\b[a-z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-z0-9.-]+\.[a-z]{2,}\b")
USER_HOME_RE = re.compile(r"/Users/[^/\s]+")
REQUIRED_REFERENCES = (
    "references/public-onboarding.md",
    "references/public-release-readiness.md",
    "scripts/release_check.py",
    "scripts/config_layers.py",
    "bin/macomrade",
)


class PublicCloneRehearsalError(RuntimeError):
    pass


def rehearsal_steps(*, python: str = sys.executable) -> list[tuple[str, list[str]]]:
    """Return the hermetic gate followed by the documented read-only quick start."""
    return [
        ("bootstrap-definition", [python, "scripts/bootstrap_validate.py"]),
        ("cli-contract", ["./bin/macomrade", "validate", "--json"]),
        ("schema-contract", ["./bin/macomrade", "verify", "schemas"]),
        ("release-check", [python, "scripts/release_check.py"]),
        ("app-inventory", ["./bin/macomrade", "scan", "apps"]),
        ("app-plan", ["./bin/macomrade", "plan", "apps", "--profile", "auto"]),
    ]


def credential_free_environment(
    *,
    home: Path,
    state_dir: Path,
    temp_dir: Path,
    environ: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Build a narrow environment without inherited credential channels."""
    source = os.environ if environ is None else environ
    environment = {
        "PATH": source.get("PATH", "/usr/bin:/bin:/usr/sbin:/sbin"),
        "HOME": str(home),
        "TMPDIR": str(temp_dir),
        "MACOMRADE_PUBLIC_ONLY": "1",
        "INSTALL_MY_MACOS_APPS_STATE_DIR": str(state_dir),
        "PYTHONPYCACHEPREFIX": str(temp_dir / "pycache"),
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_ASKPASS": "/usr/bin/false",
        "SSH_ASKPASS": "/usr/bin/false",
        "GIT_CONFIG_GLOBAL": "/dev/null",
        "GIT_CONFIG_NOSYSTEM": "1",
        "HOMEBREW_NO_AUTO_UPDATE": "1",
        "NO_COLOR": "1",
    }
    for name in ("LANG", "LC_ALL", "LC_CTYPE"):
        if source.get(name):
            environment[name] = source[name]
    return environment


def personal_markers(output: str) -> list[str]:
    markers = []
    if EMAIL_RE.search(output):
        markers.append("email_address")
    if USER_HOME_RE.search(output):
        markers.append("absolute_user_home")
    return markers


def _run(
    command: list[str],
    *,
    cwd: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]],
    env: Mapping[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return runner(
        command,
        cwd=cwd,
        env=None if env is None else dict(env),
        capture_output=True,
        text=True,
        check=False,
    )


def _source_commit(
    *,
    root: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]],
) -> tuple[str, bool]:
    guard = _run(
        [sys.executable, "scripts/icloud_git_guard.py", "inspect", "--repo", "."],
        cwd=root,
        runner=runner,
    )
    if guard.returncode != 0:
        raise PublicCloneRehearsalError("iCloud Git preflight failed")
    revision = _run(["git", "rev-parse", "HEAD"], cwd=root, runner=runner)
    commit = revision.stdout.strip().lower()
    if revision.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise PublicCloneRehearsalError("cannot resolve the exact source commit")
    status = _run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root,
        runner=runner,
    )
    if status.returncode != 0:
        raise PublicCloneRehearsalError("cannot inspect the source worktree")
    return commit, not bool(status.stdout.strip())


def _result(step_id: str, command: list[str], completed: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return {
        "id": step_id,
        "command": command,
        "returncode": completed.returncode,
        "status": "passed" if completed.returncode == 0 else "failed",
    }


def build_record(
    *,
    commit: str,
    results: list[dict[str, Any]],
    source_clean: bool,
    clone_clean: bool,
    private_overlay_present: bool,
    markers: list[str],
) -> dict[str, Any]:
    assertions = {
        "source_worktree_clean": source_clean,
        "clone_worktree_clean": clone_clean,
        "private_overlay_absent": not private_overlay_present,
        "personal_output_markers": sorted(set(markers)),
        "inherited_credentials": [],
        "public_only_mode": True,
    }
    passed = (
        bool(results)
        and all(row.get("status") == "passed" for row in results)
        and all(
            (
                assertions["source_worktree_clean"],
                assertions["clone_worktree_clean"],
                assertions["private_overlay_absent"],
                not assertions["personal_output_markers"],
                not assertions["inherited_credentials"],
                assertions["public_only_mode"],
            )
        )
    )
    return {
        "schema_version": 1,
        "kind": "public_clone_rehearsal",
        "status": "passed" if passed else "failed",
        "source_commit": commit,
        "transport": "credential_free_local_clone",
        "boundary": (
            "This proves an independent local clone without inherited credentials or Private overlays; "
            "it is not anonymous GitHub access while the remote repository remains private."
        ),
        "checks_run": len(results),
        "results": results,
        "assertions": assertions,
        "authority": {
            "publication_authorized": False,
            "visibility_change_authorized": False,
            "push_authorized": False,
        },
    }


def _write_record(state_dir: Path, record: dict[str, Any]) -> Path:
    destination_dir = state_dir / "public-clone-rehearsals"
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / f"public-clone-rehearsal-{record['source_commit'][:12]}.json"
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(destination)
    return destination


def run_rehearsal(
    *,
    root: Path = ROOT,
    state_dir: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> tuple[dict[str, Any], Path]:
    commit, source_clean = _source_commit(root=root, runner=runner)
    if not source_clean:
        raise PublicCloneRehearsalError("source worktree must be clean before rehearsing an exact candidate")

    results: list[dict[str, Any]] = []
    markers: list[str] = []
    clone_clean = False
    private_overlay_present = False
    with tempfile.TemporaryDirectory(prefix="macomrade-public-clone-") as raw_temp:
        temp = Path(raw_temp)
        home = temp / "home"
        runtime_state = temp / "state"
        scratch = temp / "tmp"
        clone = temp / "candidate"
        for path in (home, runtime_state, scratch):
            path.mkdir(parents=True, exist_ok=True)
        environment = credential_free_environment(
            home=home,
            state_dir=runtime_state,
            temp_dir=scratch,
        )

        clone_command = [
            "git",
            "-c",
            "credential.helper=",
            "clone",
            "--no-local",
            "--no-hardlinks",
            "--no-checkout",
            root.resolve().as_uri(),
            str(clone),
        ]
        completed = _run(clone_command, cwd=temp, runner=runner, env=environment)
        results.append(_result("independent-clone", ["git", "clone", "<local-source>", "<temporary-clone>"], completed))
        if completed.returncode == 0:
            checkout = _run(
                ["git", "checkout", "--detach", commit],
                cwd=clone,
                runner=runner,
                env=environment,
            )
            results.append(_result("exact-commit-checkout", ["git", "checkout", "--detach", commit], checkout))
        else:
            checkout = subprocess.CompletedProcess([], 1, "", "clone failed")

        if checkout.returncode == 0:
            for step_id, command in rehearsal_steps():
                completed = _run(command, cwd=clone, runner=runner, env=environment)
                results.append(_result(step_id, command, completed))
                markers.extend(personal_markers(completed.stdout + "\n" + completed.stderr))
                if completed.returncode != 0:
                    break

            private_overlay_present = (clone / "Private").exists()
            status = _run(
                ["git", "status", "--porcelain", "--untracked-files=all"],
                cwd=clone,
                runner=runner,
                env=environment,
            )
            clone_clean = status.returncode == 0 and not bool(status.stdout.strip())
            results.append(
                {
                    "id": "clone-boundary",
                    "command": ["assert", "no-Private-and-clean-worktree"],
                    "returncode": 0 if clone_clean and not private_overlay_present else 1,
                    "status": "passed" if clone_clean and not private_overlay_present else "failed",
                }
            )

    record = build_record(
        commit=commit,
        results=results,
        source_clean=source_clean,
        clone_clean=clone_clean,
        private_overlay_present=private_overlay_present,
        markers=markers,
    )
    return record, _write_record(state_dir, record)


def validate_definition(*, root: Path = ROOT) -> dict[str, Any]:
    errors = [relative for relative in REQUIRED_REFERENCES if not (root / relative).is_file()]
    commands = [command for _step_id, command in rehearsal_steps()]
    if any("--apply" in command or "sudo" in command for command in commands):
        errors.append("rehearsal steps must remain read-only")
    if not any(command[-1:] == ["scripts/release_check.py"] for command in commands):
        errors.append("rehearsal must run the complete hermetic release check")
    return {
        "schema_version": 1,
        "status": "passed" if not errors else "failed",
        "steps": len(commands),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")
    run_parser = subparsers.add_parser("run")
    add_state_dir_argument(run_parser)
    args = parser.parse_args()
    if args.command == "validate":
        result = validate_definition()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "passed" else 1
    try:
        record, path = run_rehearsal(
            state_dir=resolve_state_dir(args.state_dir),
        )
    except PublicCloneRehearsalError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 2
    print(json.dumps({"record": str(path), "summary": record}, ensure_ascii=False, indent=2))
    return 0 if record["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
