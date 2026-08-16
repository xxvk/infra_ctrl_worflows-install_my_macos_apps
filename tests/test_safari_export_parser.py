#!/usr/bin/env python3
"""Fixture-first read-only tests for the BR-03 Safari export adapter."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_HTML = ROOT / "tests" / "fixtures" / "browser" / "safari-bookmarks-only" / "Bookmarks.html"
sys.path.insert(0, str(ROOT / "scripts"))

import safari_export  # noqa: E402
import schema_contract  # noqa: E402


class SafariExportParserTests(unittest.TestCase):
    def make_zip(self, root: Path, *, extra: dict[str, bytes] | None = None) -> Path:
        archive = root / "Safari Export.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as output:
            output.writestr("Bookmarks.html", FIXTURE_HTML.read_bytes())
            for name, content in (extra or {}).items():
                output.writestr(name, content)
        return archive

    def test_fixture_splits_bookmarks_and_reading_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = safari_export.parse_export(self.make_zip(Path(tmp)))

        self.assertEqual(result["bookmark_count"], 2)
        self.assertEqual(result["reading_list_count"], 2)
        self.assertEqual(len(result["items"]), 4)
        for item in result["items"]:
            self.assertEqual(schema_contract.validate_document(item, "browser-item"), [])
            self.assertEqual(item["source"]["browser"], "safari")
            self.assertEqual(item["source"]["profile_scope"], "shared_across_profiles")
            self.assertIsNone(item["url"]["canonical"])
            self.assertEqual(item["url"]["canonicalization_status"], "not_evaluated")
            self.assertEqual(item["privacy"]["provenance"], "machine_observation")
            self.assertFalse(item["privacy"]["git_allowed"])
            self.assertFalse(item["execution_authorized"])

        reading = [item for item in result["items"] if item["item_type"] == "reading_list"]
        self.assertEqual(len(reading), 2)
        self.assertTrue(all(item["intended_lifecycle"] == "read_later" for item in reading))
        self.assertTrue(
            all("Reading List" in item["collection"]["path"] for item in reading)
        )

    def test_safari_27_separate_members_and_appledouble_metadata_are_supported(self) -> None:
        bookmarks = b'''<!DOCTYPE NETSCAPE-Bookmark-file-1>\n<DL><p>\n<DT><H3>Bookmarks</H3>\n<DL><p><DT><A HREF="https://bookmark.example.invalid">Bookmark</A></DL><p>\n</DL><p>'''
        reading_list = b'''<!DOCTYPE NETSCAPE-Bookmark-file-1>\n<DL><p>\n<DT><H3 IDENTIFIER="com.apple.ReadingList">Reading List</H3>\n<DL><p><DT><A HREF="https://reading.example.invalid">Reading</A></DL><p>\n</DL><p>'''
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "Safari Export.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
                output.writestr("Safari Export/", b"")
                output.writestr("Safari Export/Bookmarks.html", bookmarks)
                output.writestr("Safari Export/ReadingList.html", reading_list)
                output.writestr("__MACOSX/Safari Export/._Bookmarks.html", b"appledouble")
                output.writestr("__MACOSX/Safari Export/._ReadingList.html", b"appledouble")
            result = safari_export.parse_export(archive)

        self.assertEqual(result["bookmark_count"], 1)
        self.assertEqual(result["reading_list_count"], 1)
        self.assertEqual(
            [item["item_type"] for item in result["items"]],
            ["bookmark", "reading_list"],
        )

    def test_two_html_members_must_be_one_bookmarks_and_one_reading_list_document(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "duplicate-bookmarks.zip"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
                output.writestr("Bookmarks.html", FIXTURE_HTML.read_bytes())
                output.writestr("Bookmarks-copy.html", FIXTURE_HTML.read_bytes())
            with self.assertRaisesRegex(
                safari_export.SafariExportError,
                "Bookmarks and Reading List only",
            ):
                safari_export.parse_export(archive)

    def test_identity_is_repeatable_for_an_unchanged_export_but_marked_unstable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = self.make_zip(Path(tmp))
            first = safari_export.parse_export(archive)
            second = safari_export.parse_export(archive)

        self.assertEqual(
            [item["item_id"] for item in first["items"]],
            [item["item_id"] for item in second["items"]],
        )
        for item in first["items"]:
            self.assertEqual(item["identity"]["method"], "source_position_fallback")
            self.assertEqual(item["identity"]["stability"], "unstable")
            self.assertFalse(item["identity"]["cross_profile_merge_allowed"])

    def test_cli_emits_redacted_counts_not_private_item_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = self.make_zip(Path(tmp))
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                returncode = safari_export.main(["inspect", str(archive)])

        payload = json.loads(stdout.getvalue())
        self.assertEqual(returncode, 0)
        self.assertEqual(payload["bookmark_count"], 2)
        self.assertEqual(payload["reading_list_count"], 2)
        self.assertFalse(payload["item_content_emitted"])
        self.assertFalse(payload["execution_authorized"])
        rendered = stdout.getvalue()
        for private_value in (
            "docs.example.invalid",
            "research.example.invalid",
            "Example documentation",
            "Fictional paper",
            "Safari Export.zip",
        ):
            self.assertNotIn(private_value, rendered)

    def test_rejects_non_bookmark_members(self) -> None:
        for member, content in (
            ("Passwords.csv", b"Title,URL,Username,Password\n"),
            ("History.json", b'{"history": []}'),
            ("PaymentCards.json", b'{"payment_cards": []}'),
        ):
            with self.subTest(member=member), tempfile.TemporaryDirectory() as tmp:
                archive = self.make_zip(Path(tmp), extra={member: content})
                with self.assertRaisesRegex(safari_export.SafariExportError, "Bookmarks and Reading List only"):
                    safari_export.parse_export(archive)

    def test_rejects_path_traversal_encryption_and_oversized_members(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "traversal.zip"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("../Bookmarks.html", FIXTURE_HTML.read_bytes())
            with self.assertRaisesRegex(safari_export.SafariExportError, "unsafe member path"):
                safari_export.parse_export(archive)

        with tempfile.TemporaryDirectory() as tmp:
            archive = self.make_zip(Path(tmp))
            original = safari_export.MAX_MEMBER_BYTES
            safari_export.MAX_MEMBER_BYTES = 32
            try:
                with self.assertRaisesRegex(safari_export.SafariExportError, "size limit"):
                    safari_export.parse_export(archive)
            finally:
                safari_export.MAX_MEMBER_BYTES = original

        info = zipfile.ZipInfo("Bookmarks.html")
        info.flag_bits |= 0x1
        with self.assertRaisesRegex(safari_export.SafariExportError, "encrypted"):
            safari_export.validate_member(info)

        link = zipfile.ZipInfo("Bookmarks.html")
        link.create_system = 3
        link.external_attr = (0o120777 << 16)
        with self.assertRaisesRegex(safari_export.SafariExportError, "symbolic-link"):
            safari_export.validate_member(link)

    def test_rejects_input_symlink_and_multiple_html_members(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = self.make_zip(root)
            alias = root / "alias.zip"
            alias.symlink_to(archive)
            with self.assertRaisesRegex(safari_export.SafariExportError, "unavailable"):
                safari_export.parse_export(alias)

            with zipfile.ZipFile(archive, "a") as output:
                output.writestr("Bookmarks-duplicate.html", FIXTURE_HTML.read_bytes())
            with self.assertRaisesRegex(safari_export.SafariExportError, "Bookmarks and Reading List only"):
                safari_export.parse_export(archive)

    def test_rejects_non_zip_or_malformed_netscape_html_without_leaking_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plain = root / "Bookmarks.html"
            plain.write_text("PRIVATE https://secret.example.invalid", encoding="utf-8")
            with self.assertRaisesRegex(safari_export.SafariExportError, "ZIP"):
                safari_export.parse_export(plain)

            archive = root / "malformed.zip"
            with zipfile.ZipFile(archive, "w") as output:
                output.writestr("Bookmarks.html", b"PRIVATE malformed content")
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                returncode = safari_export.main(["inspect", str(archive)])
            self.assertEqual(returncode, 1)
            self.assertNotIn("PRIVATE", stderr.getvalue())
            self.assertNotIn("secret.example.invalid", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
