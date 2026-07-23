#!/usr/bin/env python3
# Mutation action IDs: state.materialize, state.migrate, state.cleanup
"""Copy, verify, and explicitly clean up legacy repository-local state."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Iterable

from icloud_git_guard import choose_materializer, materialize_paths
from state_paths import add_state_dir_argument, resolve_state_dir


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "state"
STUB_NAMES = {"README.md", "locator.json"}
CLEANUP_CONFIRMATION = "REMOVE VERIFIED LEGACY STATE"
UNAVAILABLE_FLAGS = {"dataless", "offline", "archived"}


class StateMigrationError(RuntimeError):
    pass


class SourceUnavailableError(StateMigrationError):
    pass


class MigrationConflictError(StateMigrationError):
    pass


class VerificationError(StateMigrationError):
    pass


class ConfirmationError(StateMigrationError):
    pass


def read_macos_flags(path: Path) -> set[str]:
    result = subprocess.run(
        ["stat", "-f", "%Sf", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return set()
    return {part.strip().lower() for part in result.stdout.strip().split(",") if part.strip()}


def source_files(source: Path) -> list[Path]:
    if not source.exists():
        return []
    files: list[Path] = []
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise MigrationConflictError(f"legacy state contains unsupported symlink: {path}")
        if path.is_file() and not (path.parent == source and path.name in STUB_NAMES):
            files.append(path)
    return files


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_source(
    source: Path,
    *,
    flag_reader: Callable[[Path], set[str]] = read_macos_flags,
) -> dict[str, object]:
    files = source_files(source)
    unavailable = []
    logical_bytes = 0
    for path in files:
        flags = flag_reader(path)
        blocked = sorted(flags & UNAVAILABLE_FLAGS)
        if blocked:
            unavailable.append({"path": str(path), "flags": blocked})
        try:
            logical_bytes += path.stat().st_size
        except OSError:
            pass
    return {
        "schema_version": 1,
        "source": str(source),
        "source_file_count": len(files),
        "source_logical_bytes": logical_bytes,
        "unavailable_count": len(unavailable),
        "unavailable": unavailable,
        "ready_to_copy": not unavailable,
    }


def build_manifest(
    source: Path,
    destination: Path,
    *,
    flag_reader: Callable[[Path], set[str]] = read_macos_flags,
) -> dict[str, object]:
    rows = []
    for path in source_files(source):
        flags = flag_reader(path)
        blocked = sorted(flags & UNAVAILABLE_FLAGS)
        if blocked:
            raise SourceUnavailableError(
                f"source is not fully local: {path} ({','.join(blocked)})"
            )
        rows.append(
            {
                "relative_path": path.relative_to(source).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return {
        "schema_version": 1,
        "kind": "state_migration_manifest",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source": str(source),
        "destination": str(destination),
        "file_count": len(rows),
        "logical_bytes": sum(int(row["bytes"]) for row in rows),
        "files": rows,
    }


def _verify_destination(destination: Path, manifest: dict[str, object]) -> None:
    for row in manifest["files"]:
        path = destination / str(row["relative_path"])
        if not path.is_file():
            raise VerificationError(f"destination file missing: {path}")
        if path.stat().st_size != row["bytes"] or sha256_file(path) != row["sha256"]:
            raise VerificationError(f"destination hash mismatch: {path}")


def copy_and_verify(
    source: Path,
    destination: Path,
    *,
    flag_reader: Callable[[Path], set[str]] = read_macos_flags,
) -> dict[str, object]:
    """Copy first, then hash every destination file; never remove source data."""
    source = source.expanduser().resolve()
    destination = destination.expanduser().resolve()
    manifest = build_manifest(source, destination, flag_reader=flag_reader)

    conflicts = []
    for row in manifest["files"]:
        target = destination / str(row["relative_path"])
        if target.exists() and (
            not target.is_file()
            or target.stat().st_size != row["bytes"]
            or sha256_file(target) != row["sha256"]
        ):
            conflicts.append(str(target))
    if conflicts:
        raise MigrationConflictError(
            "destination contains different data: " + ", ".join(conflicts[:10])
        )

    destination.mkdir(parents=True, exist_ok=True)
    for row in manifest["files"]:
        relative = Path(str(row["relative_path"]))
        source_path = source / relative
        target = destination / relative
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_name(f".{target.name}.migrating-{os.getpid()}")
        shutil.copy2(source_path, temporary)
        if temporary.stat().st_size != row["bytes"] or sha256_file(temporary) != row["sha256"]:
            temporary.unlink(missing_ok=True)
            raise VerificationError(f"temporary copy hash mismatch: {source_path}")
        os.replace(temporary, target)

    _verify_destination(destination, manifest)
    completed = {
        **manifest,
        "status": "verified",
        "verified_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    manifest_path = destination / f"migration-manifest-{stamp}.json"
    temporary_manifest = manifest_path.with_suffix(".json.tmp")
    temporary_manifest.write_text(
        json.dumps(completed, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary_manifest, manifest_path)
    return {
        "status": "verified",
        "source": str(source),
        "destination": str(destination),
        "source_file_count": manifest["file_count"],
        "verified_file_count": manifest["file_count"],
        "logical_bytes": manifest["logical_bytes"],
        "manifest_path": str(manifest_path),
    }


def cleanup_verified_source(
    source: Path,
    destination: Path,
    manifest: dict[str, object],
    *,
    confirmation: str,
    flag_reader: Callable[[Path], set[str]] = read_macos_flags,
) -> dict[str, object]:
    """Delete only manifest-bound source files after fresh source/dest read-back."""
    if confirmation != CLEANUP_CONFIRMATION:
        raise ConfirmationError(f'confirmation must be exactly "{CLEANUP_CONFIRMATION}"')
    _verify_destination(destination, manifest)
    removable: list[Path] = []
    for row in manifest["files"]:
        source_path = source / str(row["relative_path"])
        if not source_path.exists():
            continue
        flags = flag_reader(source_path)
        blocked = sorted(flags & UNAVAILABLE_FLAGS)
        if blocked:
            raise SourceUnavailableError(
                f"source became unavailable before cleanup: {source_path}"
            )
        if (
            source_path.stat().st_size != row["bytes"]
            or sha256_file(source_path) != row["sha256"]
        ):
            raise VerificationError(f"source changed after migration: {source_path}")
        removable.append(source_path)

    for path in removable:
        path.unlink()
    for directory in sorted(
        (path for path in source.rglob("*") if path.is_dir()),
        key=lambda path: len(path.parts),
        reverse=True,
    ):
        try:
            directory.rmdir()
        except OSError:
            pass
    remaining = [path.relative_to(source).as_posix() for path in source_files(source)]
    return {
        "status": "cleaned",
        "removed_file_count": len(removable),
        "remaining_untracked_file_count": len(remaining),
        "remaining_untracked_files": remaining,
    }


def plan_verified_source_cleanup(
    source: Path,
    destination: Path,
    manifest: dict[str, object],
    *,
    flag_reader: Callable[[Path], set[str]] = read_macos_flags,
) -> dict[str, object]:
    """Verify both copies and report exactly what an approved cleanup removes."""
    _verify_destination(destination, manifest)
    removable_count = 0
    removable_bytes = 0
    manifest_paths = {str(row["relative_path"]) for row in manifest["files"]}
    for row in manifest["files"]:
        source_path = source / str(row["relative_path"])
        if not source_path.exists():
            continue
        flags = flag_reader(source_path)
        blocked = sorted(flags & UNAVAILABLE_FLAGS)
        if blocked:
            raise SourceUnavailableError(
                f"source became unavailable before cleanup: {source_path}"
            )
        if (
            source_path.stat().st_size != row["bytes"]
            or sha256_file(source_path) != row["sha256"]
        ):
            raise VerificationError(f"source changed after migration: {source_path}")
        removable_count += 1
        removable_bytes += int(row["bytes"])

    preserved = [
        path.relative_to(source).as_posix()
        for path in source_files(source)
        if path.relative_to(source).as_posix() not in manifest_paths
    ]
    return {
        "status": "planned",
        "removable_file_count": removable_count,
        "removable_logical_bytes": removable_bytes,
        "preserved_untracked_file_count": len(preserved),
        "preserved_untracked_files": preserved,
        "required_confirmation": CLEANUP_CONFIRMATION,
        "policy": "Preview only; no source files deleted.",
    }


def _latest_manifest(destination: Path) -> Path | None:
    paths = sorted(destination.glob("migration-manifest-*.json"))
    return paths[-1] if paths else None


def _print(payload: dict[str, object], *, full: bool = False) -> None:
    if full:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    compact = json.loads(json.dumps(payload))
    containers = [compact]
    if isinstance(compact.get("inspection"), dict):
        containers.append(compact["inspection"])
    for container in containers:
        unavailable = container.get("unavailable")
        if isinstance(unavailable, list) and len(unavailable) > 10:
            container["unavailable"] = unavailable[:10]
            container["unavailable_omitted"] = len(unavailable) - 10
    actions = compact.get("actions")
    if isinstance(actions, list) and len(actions) > 10:
        compact["actions"] = actions[:10]
        compact["actions_omitted"] = len(actions) - 10
    print(json.dumps(compact, ensure_ascii=False, indent=2))


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    add_state_dir_argument(parser)
    parser.add_argument("--json", action="store_true", help="print every path and action")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect")
    _add_common(inspect_parser)
    materialize_parser = subparsers.add_parser("materialize")
    _add_common(materialize_parser)
    materialize_parser.add_argument("--apply", action="store_true")
    materialize_parser.add_argument("--exact", action="store_true")
    materialize_parser.add_argument("--timeout", type=int, default=300)
    migrate_parser = subparsers.add_parser("migrate")
    _add_common(migrate_parser)
    migrate_parser.add_argument("--apply", action="store_true")
    cleanup_parser = subparsers.add_parser("cleanup-source")
    _add_common(cleanup_parser)
    cleanup_parser.add_argument("--manifest", type=Path)
    cleanup_parser.add_argument("--confirm", default="")
    args = parser.parse_args()

    source = args.source.expanduser().resolve()
    destination = resolve_state_dir(args.state_dir)
    if args.command == "inspect":
        _print({**inspect_source(source), "destination": str(destination)}, full=args.json)
        return 0

    if args.command == "materialize":
        inspection = inspect_source(source)
        unavailable = [Path(row["path"]) for row in inspection["unavailable"]]
        paths: Iterable[Path] = unavailable if args.exact else ([source] if unavailable else [])
        tool = choose_materializer()
        if unavailable and not tool:
            _print({"status": "materializer_unavailable", "inspection": inspection}, full=args.json)
            return 3
        actions = materialize_paths(
            paths,
            tool=str(tool),
            apply=args.apply,
            timeout=args.timeout,
        ) if paths else []
        status = (
            "nothing_to_materialize"
            if not unavailable
            else "requested"
            if args.apply and all(row["status"] == "requested" for row in actions)
            else "failed"
            if args.apply
            else "planned"
        )
        _print(
            {
                "action_id": "state.materialize",
                "status": status,
                "inspection": inspection,
                "actions": actions,
            },
            full=args.json,
        )
        return 0 if status in {"nothing_to_materialize", "requested", "planned"} else 3

    if args.command == "migrate":
        inspection = inspect_source(source)
        if not args.apply:
            _print(
                {
                    "action_id": "state.migrate",
                    "status": "planned" if inspection["ready_to_copy"] else "materialization_required",
                    "source": str(source),
                    "destination": str(destination),
                    "source_file_count": inspection["source_file_count"],
                    "unavailable_count": inspection["unavailable_count"],
                    "policy": "Plan only; no files copied or deleted.",
                },
                full=args.json,
            )
            return 0 if inspection["ready_to_copy"] else 2
        try:
            _print(
                {"action_id": "state.migrate", **copy_and_verify(source, destination)},
                full=args.json,
            )
            return 0
        except StateMigrationError as exc:
            _print(
                {"action_id": "state.migrate", "status": "failed", "error": str(exc)},
                full=args.json,
            )
            return 3

    manifest_path = args.manifest or _latest_manifest(destination)
    if manifest_path is None or not manifest_path.is_file():
        _print({"status": "failed", "error": "verified migration manifest not found"}, full=args.json)
        return 3
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    try:
        if not args.confirm:
            result = plan_verified_source_cleanup(source, destination, manifest)
            _print(
                {"action_id": "state.cleanup", "manifest": str(manifest_path), **result},
                full=args.json,
            )
            return 0
        result = cleanup_verified_source(
            source,
            destination,
            manifest,
            confirmation=args.confirm,
        )
    except StateMigrationError as exc:
        _print({"status": "failed", "error": str(exc)}, full=args.json)
        return 3
        _print(
            {"action_id": "state.cleanup", "manifest": str(manifest_path), **result},
            full=args.json,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
