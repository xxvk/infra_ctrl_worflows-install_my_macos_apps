#!/usr/bin/env python3
"""Parse an explicit Safari Bookmarks-and-Reading-List export without writes."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
import zipfile
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath
from typing import Any

from schema_contract import validate_document


READING_LIST_ID = "com.apple.ReadingList"
MAX_ARCHIVE_BYTES = 100 * 1024 * 1024
MAX_MEMBER_BYTES = 64 * 1024 * 1024
MAX_TOTAL_BYTES = 64 * 1024 * 1024
MAX_MEMBERS = 32
MAX_COMPRESSION_RATIO = 1000

MACHINE_PRIVACY = {
    "provenance": "machine_observation",
    "storage_layer": "machine_local",
    "contains_private_content": True,
    "git_allowed": False,
    "redaction_required": True,
}


class SafariExportError(RuntimeError):
    """A privacy-safe Safari export validation or parsing failure."""


def validate_member(info: zipfile.ZipInfo) -> None:
    member = PurePosixPath(info.filename)
    if member.is_absolute() or ".." in member.parts:
        raise SafariExportError("unsafe member path")
    if info.flag_bits & 0x1:
        raise SafariExportError("encrypted ZIP members are unsupported")
    mode = (info.external_attr >> 16) & 0o170000
    if mode == stat.S_IFLNK:
        raise SafariExportError("symbolic-link ZIP members are unsupported")
    if info.file_size > MAX_MEMBER_BYTES:
        raise SafariExportError("ZIP member exceeds the size limit")
    if info.file_size and info.compress_size == 0:
        raise SafariExportError("ZIP member has an unsafe compression ratio")
    if info.compress_size and info.file_size / info.compress_size > MAX_COMPRESSION_RATIO:
        raise SafariExportError("ZIP member has an unsafe compression ratio")


class NetscapeBookmarkParser(HTMLParser):
    """Parse folder and anchor structure without interpreting or fetching URLs."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.folder_stack: list[dict[str, Any]] = []
        self.dl_pushes: list[bool] = []
        self.pending_folder: dict[str, Any] | None = None
        self.folder_capture: dict[str, Any] | None = None
        self.anchor_capture: dict[str, Any] | None = None
        self.entries: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {key.lower(): value for key, value in attrs}
        if tag == "h3":
            self.folder_capture = {"attrs": attributes, "text": []}
        elif tag == "dl":
            pushed = self.pending_folder is not None
            if self.pending_folder is not None:
                self.folder_stack.append(self.pending_folder)
                self.pending_folder = None
            self.dl_pushes.append(pushed)
        elif tag == "a":
            self.anchor_capture = {
                "href": attributes.get("href"),
                "text": [],
                "folders": [dict(folder) for folder in self.folder_stack],
            }

    def handle_endtag(self, tag: str) -> None:
        if tag == "h3" and self.folder_capture is not None:
            text = "".join(self.folder_capture["text"]).strip()
            values = {
                value.strip()
                for value in self.folder_capture["attrs"].values()
                if isinstance(value, str)
            }
            self.pending_folder = {
                "name": text or READING_LIST_ID,
                "is_reading_list": text == READING_LIST_ID or READING_LIST_ID in values,
            }
            self.folder_capture = None
        elif tag == "a" and self.anchor_capture is not None:
            href = self.anchor_capture.get("href")
            if isinstance(href, str) and href.strip():
                if any(ord(character) < 0x20 for character in href):
                    raise SafariExportError("bookmark URL contains control characters")
                folders = self.anchor_capture["folders"]
                self.entries.append(
                    {
                        "url": href.strip(),
                        "title": "".join(self.anchor_capture["text"]).strip() or None,
                        "folder_path": [folder["name"] for folder in folders] or ["Bookmarks"],
                        "reading_list": any(folder["is_reading_list"] for folder in folders),
                    }
                )
            self.anchor_capture = None
        elif tag == "dl" and self.dl_pushes:
            if self.dl_pushes.pop() and self.folder_stack:
                self.folder_stack.pop()

    def handle_data(self, data: str) -> None:
        if self.folder_capture is not None:
            self.folder_capture["text"].append(data)
        if self.anchor_capture is not None:
            self.anchor_capture["text"].append(data)


def _artifact_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_appledouble_metadata(info: zipfile.ZipInfo) -> bool:
    member = PurePosixPath(info.filename)
    return "__MACOSX" in member.parts or member.name.startswith("._")


def _parse_html_member(html_bytes: bytes) -> tuple[list[dict[str, Any]], bool]:
    try:
        html = html_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise SafariExportError("Safari bookmark HTML is not valid UTF-8") from exc
    if "NETSCAPE-BOOKMARK-FILE-1" not in html[:4096].upper():
        raise SafariExportError("Safari bookmark HTML lacks the Netscape signature")

    parser = NetscapeBookmarkParser()
    try:
        parser.feed(html)
        parser.close()
    except (ValueError, AssertionError) as exc:
        raise SafariExportError("Safari bookmark HTML could not be parsed") from exc
    return parser.entries, READING_LIST_ID in html


def _item_from_entry(
    entry: dict[str, Any],
    *,
    ordinal: int,
    artifact_ref: str,
    privacy: dict[str, Any],
) -> dict[str, Any]:
    identity_seed = f"{artifact_ref}:{ordinal}".encode("utf-8")
    item_id = "bri_" + hashlib.sha256(identity_seed).hexdigest()[:32]
    reading_list = bool(entry["reading_list"])
    return {
        "schema_version": 1,
        "kind": "browser_item",
        "item_id": item_id,
        "identity": {
            "method": "source_position_fallback",
            "stability": "unstable",
            "namespace_ref": artifact_ref,
            "cross_profile_merge_allowed": False,
        },
        "item_type": "reading_list" if reading_list else "bookmark",
        "source": {
            "browser": "safari",
            "source_id": "safari_export_zip",
            "profile_scope": "shared_across_profiles",
            "profile_ref": None,
            "account_ref": None,
            "artifact_ref": artifact_ref,
        },
        "collection": {
            "kind": "reading_list" if reading_list else "bookmarks",
            "path": entry["folder_path"],
        },
        "url": {
            "original": entry["url"],
            "canonical": None,
            "canonicalization_status": "not_evaluated",
            "canonicalization_version": None,
        },
        "title": entry["title"],
        "tags": [],
        "read_state": "unknown" if reading_list else "not_applicable",
        "intended_lifecycle": "read_later" if reading_list else "unknown",
        "confidence": "high" if reading_list else "low",
        "decision_expiry": None,
        "conflict_evidence": [],
        "privacy": dict(privacy),
        "execution_authorized": False,
    }


def parse_export(
    path: Path,
) -> dict[str, Any]:
    """Read one explicit ZIP into private in-memory items without writing output."""

    path = Path(path)
    if path.is_symlink() or not path.is_file():
        raise SafariExportError("explicit Safari export file is unavailable")
    if path.stat().st_size > MAX_ARCHIVE_BYTES:
        raise SafariExportError("Safari export exceeds the archive size limit")
    if not zipfile.is_zipfile(path):
        raise SafariExportError("Safari export must be a ZIP archive")

    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_MEMBERS:
                raise SafariExportError("Safari export contains too many members")
            for info in infos:
                validate_member(info)
            if sum(info.file_size for info in infos) > MAX_TOTAL_BYTES:
                raise SafariExportError("Safari export exceeds the total size limit")
            files = [
                info
                for info in infos
                if not info.is_dir() and not _is_appledouble_metadata(info)
            ]
            html_members = [
                info
                for info in files
                if PurePosixPath(info.filename).suffix.lower() in {".html", ".htm"}
            ]
            if len(files) not in {1, 2} or len(html_members) != len(files):
                raise SafariExportError(
                    "Safari export must be a Bookmarks and Reading List only ZIP with one or two HTML members"
                )
            parsed_members = [
                _parse_html_member(archive.read(member)) for member in html_members
            ]
    except zipfile.BadZipFile as exc:
        raise SafariExportError("Safari export ZIP is invalid") from exc

    if len(parsed_members) == 2:
        reading_documents = [row for row in parsed_members if row[1]]
        bookmark_documents = [row for row in parsed_members if not row[1]]
        if len(reading_documents) != 1 or len(bookmark_documents) != 1:
            raise SafariExportError(
                "Safari export must be a Bookmarks and Reading List only ZIP with one bookmarks document and one Reading List document"
            )
        if any(entry["reading_list"] for entry in bookmark_documents[0][0]) or any(
            not entry["reading_list"] for entry in reading_documents[0][0]
        ):
            raise SafariExportError(
                "Safari export must be a Bookmarks and Reading List only ZIP with separated document roles"
            )

    entries = [entry for member_entries, _ in parsed_members for entry in member_entries]

    artifact_ref = "safari-export:" + _artifact_digest(path)
    items = [
        _item_from_entry(
            entry,
            ordinal=index,
            artifact_ref=artifact_ref,
            privacy=MACHINE_PRIVACY,
        )
        for index, entry in enumerate(entries, start=1)
    ]
    for item in items:
        errors = validate_document(item, "browser-item")
        if errors:
            raise SafariExportError("parsed Safari item failed the browser-item contract")

    bookmark_count = sum(item["item_type"] == "bookmark" for item in items)
    reading_list_count = sum(item["item_type"] == "reading_list" for item in items)
    return {
        "schema_version": 1,
        "kind": "safari_export_private_parse",
        "source": "safari_export_zip",
        "artifact_ref": artifact_ref,
        "bookmark_count": bookmark_count,
        "reading_list_count": reading_list_count,
        "items": items,
        "execution_authorized": False,
    }


def redacted_summary(result: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "kind": "safari_export_redacted_summary",
        "status": "passed",
        "source": "safari_export_zip",
        "bookmark_count": result["bookmark_count"],
        "reading_list_count": result["reading_list_count"],
        "item_content_emitted": False,
        "input_path_emitted": False,
        "artifact_ref_emitted": False,
        "writes_performed": False,
        "execution_authorized": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect", help="emit redacted counts from one explicit private export")
    inspect_parser.add_argument("export", type=Path)
    args = parser.parse_args(argv)

    try:
        result = parse_export(args.export)
    except SafariExportError as exc:
        print(
            json.dumps(
                {
                    "schema_version": 1,
                    "kind": "safari_export_redacted_summary",
                    "status": "failed",
                    "error": str(exc),
                    "item_content_emitted": False,
                    "writes_performed": False,
                    "execution_authorized": False,
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(redacted_summary(result), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
