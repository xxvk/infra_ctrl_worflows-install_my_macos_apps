#!/usr/bin/env python3
# Mutation action ID: icloud.materialize
"""Protect Git operations when a checkout or its gitdir lives in iCloud.

The guard never treats an evicted File Provider item as a missing/corrupt Git
object. Inspection is read-only and avoids opening files flagged as dataless.
Materialization is plan-only unless --apply is explicitly supplied.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Iterable


SCHEMA_VERSION = 1
DEFAULT_REQUIRED_WORKTREE_PATHS = (
    "SKILL.md",
    "README.md",
    "VERSION",
    "references/mac-app-catalog.json",
)
UNAVAILABLE_FLAGS = {"dataless", "offline", "archived"}

FlagReader = Callable[[Path], set[str]]


def is_icloud_path(path: Path) -> bool:
    """Return whether a path is under a common iCloud/File Provider root."""
    normalized = str(path.expanduser().resolve(strict=False))
    markers = (
        f"{os.sep}Library{os.sep}Mobile Documents{os.sep}",
        f"{os.sep}Library{os.sep}CloudStorage{os.sep}",
        f"{os.sep}com~apple~CloudDocs{os.sep}",
    )
    return any(marker in normalized for marker in markers)


def resolve_git_dir(repo: Path) -> Path:
    """Resolve either a normal .git directory or a submodule/worktree pointer."""
    repo = repo.expanduser().resolve()
    dot_git = repo / ".git"
    if dot_git.is_dir():
        return dot_git.resolve()
    if dot_git.is_file():
        first_line = dot_git.read_text(encoding="utf-8", errors="replace").splitlines()
        if not first_line or not first_line[0].startswith("gitdir:"):
            raise ValueError(f"unsupported .git pointer: {dot_git}")
        raw = first_line[0].split(":", 1)[1].strip()
        target = Path(raw).expanduser()
        if not target.is_absolute():
            target = dot_git.parent / target
        return target.resolve()
    raise FileNotFoundError(f"no .git directory or pointer at {repo}")


def read_macos_flags(path: Path) -> set[str]:
    """Read BSD file flags without opening the item payload."""
    completed = subprocess.run(
        ["stat", "-f", "%Sf", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return set()
    return {value.strip().lower() for value in completed.stdout.strip().split(",") if value.strip()}


def unavailable_flags(flags: Iterable[str]) -> set[str]:
    return {flag.lower() for flag in flags} & UNAVAILABLE_FLAGS


def _finding(
    code: str,
    severity: str,
    path: Path,
    detail: str,
    *,
    flags: Iterable[str] = (),
) -> dict[str, object]:
    return {
        "code": code,
        "severity": severity,
        "path": str(path),
        "flags": sorted(set(flags)),
        "detail": detail,
    }


def _critical_git_paths(git_dir: Path) -> list[tuple[Path, bool]]:
    paths: list[tuple[Path, bool]] = [
        (git_dir, True),
        (git_dir / "HEAD", True),
        (git_dir / "config", True),
        (git_dir / "objects", True),
        (git_dir / "objects" / "pack", False),
    ]
    for optional in ("index", "packed-refs", "commondir"):
        candidate = git_dir / optional
        if candidate.exists():
            paths.append((candidate, False))
    for folder_name in ("refs", "objects"):
        folder = git_dir / folder_name
        if folder.exists():
            for candidate in sorted(folder.rglob("*")):
                if candidate.is_file():
                    paths.append((candidate, False))
    deduplicated: dict[str, tuple[Path, bool]] = {}
    for path, required in paths:
        key = str(path.resolve(strict=False))
        previous = deduplicated.get(key)
        deduplicated[key] = (path, required or bool(previous and previous[1]))
    return list(deduplicated.values())


def _validate_git_payload(path: Path) -> dict[str, object] | None:
    """Validate small structural headers after File Provider says data is local."""
    if not path.is_file():
        return None
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            prefix = handle.read(12)
    except OSError as exc:
        return _finding("unreadable_git_data", "blocker", path, str(exc))

    suffix = path.suffix.lower()
    if suffix == ".pack" and (size < 12 or not prefix.startswith(b"PACK")):
        return _finding(
            "invalid_pack_header",
            "blocker",
            path,
            f"expected a local Git PACK header and at least 12 bytes; observed {size} bytes",
        )
    if suffix == ".idx":
        modern = prefix.startswith(b"\xfftOc")
        plausible_legacy = size >= 1024
        if not modern and not plausible_legacy:
            return _finding(
                "invalid_index_header",
                "blocker",
                path,
                f"expected a modern Git index header or plausible legacy index; observed {size} bytes",
            )
    if suffix == ".rev" and size >= 4 and not prefix.startswith(b"RIDX"):
        return _finding(
            "invalid_reverse_index_header",
            "blocker",
            path,
            "expected a Git reverse-index RIDX header",
        )
    if path.name in {"HEAD", "config"} and size == 0:
        return _finding("empty_required_git_file", "blocker", path, "required Git metadata is empty")
    return None


def inspect_repository(
    repo: Path,
    *,
    flag_reader: FlagReader = read_macos_flags,
    required_worktree_paths: Iterable[str] = DEFAULT_REQUIRED_WORKTREE_PATHS,
) -> dict[str, object]:
    """Inspect File Provider availability before any Git command is allowed."""
    repo = repo.expanduser().resolve()
    findings: list[dict[str, object]] = []
    try:
        git_dir = resolve_git_dir(repo)
    except (FileNotFoundError, OSError, ValueError) as exc:
        return {
            "schema_version": SCHEMA_VERSION,
            "mode": "read_only_preflight",
            "repo": str(repo),
            "git_dir": None,
            "icloud_backed": is_icloud_path(repo),
            "status": "not_git_repository",
            "git_commands_safe": False,
            "findings": [
                _finding("git_dir_unavailable", "blocker", repo / ".git", str(exc))
            ],
        }

    targets: list[tuple[Path, bool, str]] = [(repo / ".git", True, "git_pointer")]
    targets.extend((path, required, "git_data") for path, required in _critical_git_paths(git_dir))
    targets.extend((repo / relative, True, "required_worktree") for relative in required_worktree_paths)

    seen: set[str] = set()
    checked_paths = 0
    for path, required, kind in targets:
        key = str(path.resolve(strict=False))
        if key in seen:
            continue
        seen.add(key)
        checked_paths += 1
        if not path.exists():
            if required:
                findings.append(
                    _finding(
                        "missing_required_path",
                        "blocker",
                        path,
                        f"required {kind} path is missing",
                    )
                )
            continue
        flags = flag_reader(path)
        unavailable = unavailable_flags(flags)
        if unavailable:
            findings.append(
                _finding(
                    "icloud_item_not_materialized",
                    "blocker",
                    path,
                    "File Provider reports that this required item is not fully local",
                    flags=flags,
                )
            )
            continue
        if kind == "git_data":
            invalid = _validate_git_payload(path)
            if invalid:
                findings.append(invalid)

    codes = {str(row["code"]) for row in findings}
    if "icloud_item_not_materialized" in codes:
        status = "materialization_required"
    elif findings:
        status = "invalid_git_data"
    else:
        status = "ready"
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "read_only_preflight",
        "repo": str(repo),
        "git_dir": str(git_dir),
        "icloud_backed": is_icloud_path(repo) or is_icloud_path(git_dir),
        "checked_paths": checked_paths,
        "status": status,
        "git_commands_safe": status == "ready",
        "findings": findings,
        "next_action": (
            "Run materialize in plan mode, then explicitly apply and re-inspect."
            if status == "materialization_required"
            else "Repair or recover Git data before running Git commands."
            if status == "invalid_git_data"
            else "Git read-only verification may proceed."
        ),
    }


def materialization_paths(report: dict[str, object], *, exact: bool = False) -> list[Path]:
    paths = {
        Path(str(row["path"]))
        for row in report.get("findings", [])
        if isinstance(row, dict) and row.get("code") == "icloud_item_not_materialized"
    }
    if not exact and report.get("git_dir"):
        objects = Path(str(report["git_dir"])) / "objects"
        collapsed: set[Path] = set()
        for path in paths:
            try:
                path.relative_to(objects)
                collapsed.add(objects)
            except ValueError:
                collapsed.add(path)
        paths = collapsed
    return sorted(paths)


def _default_help_runner(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False)


def fileprovider_supports_materialize(
    tool: str,
    *,
    runner: Callable[[list[str]], object] = _default_help_runner,
) -> bool:
    """Detect the command because recent macOS removed it while old manpages remain."""
    completed = runner([tool, "help"])
    output = f"{getattr(completed, 'stdout', '')}\n{getattr(completed, 'stderr', '')}"
    return bool(re.search(r"(?m)^\s*materialize(?:\s|$)", output))


def choose_materializer() -> str | None:
    fileproviderctl = shutil.which("fileproviderctl")
    if fileproviderctl and fileprovider_supports_materialize(fileproviderctl):
        return fileproviderctl
    return shutil.which("brctl")


def _materialize_command(tool: str, path: Path) -> list[str]:
    verb = "materialize" if Path(tool).name == "fileproviderctl" else "download"
    return [tool, verb, str(path)]


def _default_materialize_runner(command: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, capture_output=True, text=True, check=False, timeout=timeout)


def materialize_paths(
    paths: Iterable[Path],
    *,
    tool: str,
    apply: bool,
    timeout: int = 300,
    runner: Callable[[list[str], int], object] = _default_materialize_runner,
) -> list[dict[str, object]]:
    """Plan or execute local downloads; never evict or delete any item."""
    results: list[dict[str, object]] = []
    for path in paths:
        command = _materialize_command(tool, path)
        row: dict[str, object] = {
            "path": str(path),
            "command": command,
            "status": "planned",
        }
        if apply:
            try:
                completed = runner(command, timeout)
                returncode = int(getattr(completed, "returncode", 0))
                row.update(
                    {
                        "returncode": returncode,
                        "status": "requested" if returncode == 0 else "failed",
                        "stdout_tail": str(getattr(completed, "stdout", ""))[-2000:],
                        "stderr_tail": str(getattr(completed, "stderr", ""))[-2000:],
                    }
                )
            except subprocess.TimeoutExpired:
                row.update({"returncode": 124, "status": "timed_out"})
        results.append(row)
    return results


def _default_git_runner(
    command: list[str], cwd: Path, timeout: int
) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    return subprocess.run(
        command,
        cwd=cwd,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def verify_repository(
    preflight: dict[str, object],
    *,
    timeout: int,
    runner: Callable[[list[str], Path, int], object] = _default_git_runner,
) -> dict[str, object]:
    """Run read-only Git checks only after the iCloud preflight is ready."""
    if not preflight.get("git_commands_safe"):
        return {
            "schema_version": SCHEMA_VERSION,
            "mode": "git_read_only_verification",
            "status": "preflight_blocked",
            "preflight_status": preflight.get("status"),
            "checks": [],
        }
    repo = Path(str(preflight["repo"]))
    commands = (
        ["git", "status", "--short"],
        ["git", "diff", "--check"],
        ["git", "fsck", "--full"],
    )
    checks: list[dict[str, object]] = []
    for command in commands:
        row: dict[str, object] = {"command": command}
        try:
            completed = runner(command, repo, timeout)
            returncode = int(getattr(completed, "returncode", 0))
            row.update(
                {
                    "returncode": returncode,
                    "status": "passed" if returncode == 0 else "failed",
                    "stdout_tail": str(getattr(completed, "stdout", ""))[-4000:],
                    "stderr_tail": str(getattr(completed, "stderr", ""))[-4000:],
                }
            )
        except subprocess.TimeoutExpired:
            row.update({"returncode": 124, "status": "timed_out", "stdout_tail": "", "stderr_tail": ""})
        checks.append(row)
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "git_read_only_verification",
        "status": "passed" if all(row["status"] == "passed" for row in checks) else "failed",
        "preflight_status": preflight.get("status"),
        "checks": checks,
    }


def _print(payload: dict[str, object], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    print(f"status: {payload.get('status')}")
    if payload.get("repo"):
        print(f"repo: {payload['repo']}")
    if payload.get("git_dir"):
        print(f"git_dir: {payload['git_dir']}")
    findings = list(payload.get("findings", []))
    if findings:
        counts: dict[str, int] = {}
        for finding in findings:
            if isinstance(finding, dict):
                code = str(finding.get("code"))
                counts[code] = counts.get(code, 0) + 1
        print(f"findings: {len(findings)} {json.dumps(counts, sort_keys=True)}")
    for finding in findings[:10]:
        if isinstance(finding, dict):
            print(f"- {finding.get('code')}: {finding.get('path')}")
    if len(findings) > 10:
        print(f"- ... {len(findings) - 10} additional findings; use --json for full detail")
    actions = list(payload.get("actions", []))
    if actions:
        print(f"actions: {len(actions)}")
    for action in actions[:10]:
        if isinstance(action, dict):
            command = " ".join(str(part) for part in action.get("command", []))
            print(f"- {action.get('status')}: {command}")
            if action.get("stderr_tail"):
                print(f"  error: {str(action['stderr_tail']).strip()}")
    if len(actions) > 10:
        print(f"- ... {len(actions) - 10} additional actions; use --json for full detail")
    if payload.get("next_action"):
        print(f"next: {payload['next_action']}")


def _common_parser(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument("--repo", type=Path, default=Path.cwd())
    subparser.add_argument("--json", action="store_true")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect", help="read-only iCloud/Git preflight")
    _common_parser(inspect_parser)

    materialize_parser = subparsers.add_parser(
        "materialize", help="plan or request local downloads for unavailable Git data"
    )
    _common_parser(materialize_parser)
    materialize_parser.add_argument("--apply", action="store_true")
    materialize_parser.add_argument(
        "--exact",
        action="store_true",
        help="request every unavailable item individually after a grouped retry",
    )
    materialize_parser.add_argument("--timeout", type=int, default=300)

    verify_parser = subparsers.add_parser(
        "verify", help="preflight, then run git status/diff-check/fsck"
    )
    _common_parser(verify_parser)
    verify_parser.add_argument("--timeout", type=int, default=120)

    args = parser.parse_args(argv)
    preflight = inspect_repository(args.repo)
    if args.command == "inspect":
        _print(preflight, args.json)
        return 0 if preflight["status"] == "ready" else 2

    if args.command == "materialize":
        paths = materialization_paths(preflight, exact=args.exact)
        tool = choose_materializer()
        if not paths:
            payload = {
                "schema_version": SCHEMA_VERSION,
                "action_id": "icloud.materialize",
                "mode": "materialize",
                "status": "nothing_to_materialize",
                "preflight": preflight,
                "actions": [],
            }
            _print(payload, args.json)
            return 0 if preflight["status"] == "ready" else 3
        if tool is None:
            payload = {
                "schema_version": SCHEMA_VERSION,
                "action_id": "icloud.materialize",
                "mode": "materialize",
                "status": "materializer_unavailable",
                "preflight": preflight,
                "actions": [],
            }
            _print(payload, args.json)
            return 3
        if args.apply and os.geteuid() == 0:
            parser.error("materialization must run as the signed-in user, not root")
        actions = materialize_paths(
            paths,
            tool=tool,
            apply=args.apply,
            timeout=args.timeout,
        )
        payload = {
            "schema_version": SCHEMA_VERSION,
            "action_id": "icloud.materialize",
            "mode": "materialize_apply" if args.apply else "materialize_plan",
            "status": (
                "materialization_requested"
                if args.apply and all(row["status"] == "requested" for row in actions)
                else "materialization_failed"
                if args.apply
                else "planned"
            ),
            "preflight": preflight,
            "actions": actions,
            "next_action": "Re-run inspect, then verify after every item is local.",
        }
        _print(payload, args.json)
        return 0 if payload["status"] in {"planned", "materialization_requested"} else 3

    verification = verify_repository(preflight, timeout=args.timeout)
    payload = {"preflight": preflight, "verification": verification}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        _print(preflight, False)
        print(f"verification: {verification['status']}")
        for row in verification["checks"]:
            print(f"- {' '.join(row['command'])}: {row['status']}")
    return 0 if verification["status"] == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
