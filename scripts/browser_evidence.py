#!/usr/bin/env python3
"""Import one immutable Safari export into Git-ignored Private evidence."""

# Mutation action ID: browser.evidence-import

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from safari_export import SafariExportError, parse_export
from transaction_contract import require_confirmation, transaction_metadata


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_ROOT = ROOT / "Private"
ACTION_ID = "browser.evidence-import"
CONFIRMATION = "IMPORT PRIVATE BROWSER EVIDENCE"
EVIDENCE_NAME = re.compile(
    r"^safari-export-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9a-f]{12}\.zip$"
)


class BrowserEvidenceError(RuntimeError):
    """A privacy-safe browser evidence import failure."""


def _export_date(value: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        raise BrowserEvidenceError("exported-on must be an ISO calendar date")
    try:
        parsed = dt.date.fromisoformat(value)
    except ValueError as exc:
        raise BrowserEvidenceError("exported-on must be an ISO calendar date") from exc
    if parsed.isoformat() != value:
        raise BrowserEvidenceError("exported-on must be an ISO calendar date")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise BrowserEvidenceError("Safari export is unavailable") from exc
    return digest.hexdigest()


def _source_stat(source: Path) -> os.stat_result:
    try:
        stat = source.lstat()
    except OSError as exc:
        raise BrowserEvidenceError("Safari export is unavailable") from exc
    if source.is_symlink() or not source.is_file():
        raise BrowserEvidenceError("Safari export must be a regular file")
    return stat


def evidence_destination(
    source: Path,
    *,
    exported_on: str,
    private_root: Path = PRIVATE_ROOT,
) -> Path:
    date = _export_date(exported_on)
    digest = _sha256(source)
    return private_root / "browser" / "evidence" / f"safari-export-{date}-{digest[:12]}.zip"


def _assert_private_destination(destination: Path, *, root: Path, private_root: Path) -> None:
    evidence_root = (private_root / "browser" / "evidence").resolve(strict=False)
    candidate = destination.resolve(strict=False)
    try:
        candidate.relative_to(evidence_root)
    except ValueError as exc:
        raise BrowserEvidenceError("browser evidence destination escapes Private") from exc
    if candidate.parent != evidence_root or EVIDENCE_NAME.fullmatch(candidate.name) is None:
        raise BrowserEvidenceError("browser evidence destination name is invalid")
    probe = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        return
    ignored = subprocess.run(
        ["git", "-C", str(root), "check-ignore", "-q", "--", str(candidate)],
        capture_output=True,
        text=True,
        check=False,
    )
    if ignored.returncode != 0:
        raise BrowserEvidenceError("browser evidence destination must be ignored by Git")


def _validated_export(source: Path) -> tuple[dict[str, Any], str, os.stat_result]:
    before = _source_stat(source)
    digest = _sha256(source)
    try:
        parsed = parse_export(source)
    except SafariExportError as exc:
        raise BrowserEvidenceError("Safari export is invalid") from exc
    if parsed.get("artifact_ref") != f"safari-export:{digest}":
        raise BrowserEvidenceError("Safari export hash binding is invalid")
    after = _source_stat(source)
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise BrowserEvidenceError("Safari export changed during validation")
    return parsed, digest, after


def _summary(
    parsed: dict[str, Any],
    *,
    status: str,
    size_bytes: int,
    writes: bool,
    would_write: bool,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "browser_evidence_import_summary",
        "action_id": ACTION_ID,
        "status": status,
        "bookmark_count": parsed["bookmark_count"],
        "reading_list_count": parsed["reading_list_count"],
        "item_count": len(parsed["items"]),
        "size_bytes": size_bytes,
        "output_layer": "private_icloud",
        "immutable_evidence": True,
        "would_write": would_write,
        "private_content_emitted": False,
        "writes_performed": writes,
        "browser_writes_performed": False,
        "execution_authorized": False,
    }


def import_evidence(
    source: Path,
    *,
    exported_on: str,
    apply: bool,
    confirmation: str,
    root: Path = ROOT,
    private_root: Path = PRIVATE_ROOT,
) -> dict[str, Any]:
    source = source.expanduser().resolve(strict=False)
    parsed, digest, source_stat = _validated_export(source)
    destination = evidence_destination(
        source,
        exported_on=exported_on,
        private_root=private_root,
    )
    _assert_private_destination(destination, root=root, private_root=private_root)
    if not apply:
        return _summary(
            parsed,
            status="preview",
            size_bytes=source_stat.st_size,
            writes=False,
            would_write=True,
        )
    require_confirmation(ACTION_ID, confirmation)

    writes = False
    if destination.exists() or destination.is_symlink():
        if destination.is_symlink() or not destination.is_file():
            raise BrowserEvidenceError("browser evidence destination is not a regular file")
        if destination.stat().st_size != source_stat.st_size or _sha256(destination) != digest:
            raise BrowserEvidenceError("refusing to overwrite different browser evidence")
        status = "unchanged"
        if destination.stat().st_mode & 0o777 != 0o600:
            os.chmod(destination, 0o600)
            status = "permissions_corrected"
            writes = True
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary: Path | None = None
        try:
            with source.open("rb") as input_file, tempfile.NamedTemporaryFile(
                mode="wb",
                dir=destination.parent,
                prefix=".safari-evidence-",
                delete=False,
            ) as output_file:
                temporary = Path(output_file.name)
                shutil.copyfileobj(input_file, output_file, length=1024 * 1024)
                output_file.flush()
                os.fsync(output_file.fileno())
            current = _source_stat(source)
            if (source_stat.st_dev, source_stat.st_ino, source_stat.st_size, source_stat.st_mtime_ns) != (
                current.st_dev,
                current.st_ino,
                current.st_size,
                current.st_mtime_ns,
            ):
                raise BrowserEvidenceError("Safari export changed during copy")
            if temporary.stat().st_size != source_stat.st_size or _sha256(temporary) != digest:
                raise BrowserEvidenceError("browser evidence copy failed hash verification")
            try:
                copied = parse_export(temporary)
            except SafariExportError as exc:
                raise BrowserEvidenceError("browser evidence copy failed export validation") from exc
            if copied.get("artifact_ref") != parsed.get("artifact_ref"):
                raise BrowserEvidenceError("browser evidence copy failed export validation")
            os.chmod(temporary, 0o600)
            os.replace(temporary, destination)
            directory = os.open(destination.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        except (OSError, BrowserEvidenceError) as exc:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
            if isinstance(exc, BrowserEvidenceError):
                raise
            raise BrowserEvidenceError("failed to import browser evidence") from exc
        status = "written"
        writes = True

    try:
        verified, verified_digest, verified_stat = _validated_export(destination)
    except BrowserEvidenceError as exc:
        raise BrowserEvidenceError("browser evidence failed read-back") from exc
    if (
        verified_digest != digest
        or verified.get("artifact_ref") != parsed.get("artifact_ref")
        or verified_stat.st_mode & 0o777 != 0o600
    ):
        raise BrowserEvidenceError("browser evidence failed read-back")
    transaction_metadata(
        ACTION_ID,
        phase="record",
        status=status,
        targets=[destination.name],
    )
    return _summary(
        verified,
        status=status,
        size_bytes=verified_stat.st_size,
        writes=writes,
        would_write=False,
    )


def validate_policy() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "browser_evidence_policy_summary",
        "status": "passed",
        "action_id": ACTION_ID,
        "destination_layer": "private_icloud",
        "source_bytes_preserved": True,
        "mode": "0600",
        "private_content_emitted": False,
        "writes_performed": False,
        "browser_writes_performed": False,
        "execution_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate-policy")
    import_parser = subparsers.add_parser("import-safari-export")
    import_parser.add_argument("export", type=Path)
    import_parser.add_argument("--exported-on", required=True)
    import_parser.add_argument("--apply", action="store_true")
    import_parser.add_argument("--confirm", default="")
    args = parser.parse_args(argv)

    try:
        if args.command == "validate-policy":
            result = validate_policy()
        else:
            result = import_evidence(
                args.export,
                exported_on=args.exported_on,
                apply=args.apply,
                confirmation=args.confirm,
            )
    except (BrowserEvidenceError, ValueError, KeyError) as exc:
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": "browser_evidence_import_summary",
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
