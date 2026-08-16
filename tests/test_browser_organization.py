#!/usr/bin/env python3
"""TDD contracts for Private Safari organization decisions."""

from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import browser_organization  # noqa: E402
import browser_review  # noqa: E402
import browser_transactions  # noqa: E402
import safari_export  # noqa: E402
import schema_contract  # noqa: E402


class BrowserOrganizationTests(unittest.TestCase):
    def archive(self, root: Path) -> Path:
        archive = root / "private-export.zip"
        bookmarks = b"""<!DOCTYPE NETSCAPE-Bookmark-file-1>
<DL><p><DT><H3>Favorites</H3><DL><p>
<DT><H3>Old Direct</H3><DL><p>
<DT><A HREF=\"https://example.invalid/article\">Article - Example</A>
</DL><p>
<DT><H3>Old Ambiguous</H3><DL><p>
<DT><A HREF=\"https://delete.example.invalid/\">Delete Me</A>
</DL><p></DL><p></DL><p>"""
        reading = b"""<!DOCTYPE NETSCAPE-Bookmark-file-1>
<DL><p><DT><H3>com.apple.ReadingList</H3><DL><p>
<DT><A HREF=\"https://example.invalid/article\">Article duplicate</A>
<DT><A HREF=\"https://later.example.invalid/\">Read Later</A>
</DL><p></DL><p>"""
        with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
            output.writestr("Bookmarks.html", bookmarks)
            output.writestr("ReadingList.html", reading)
        return archive

    def taxonomy(self) -> dict:
        active = [
            ("01", "Work", "W", "11", "Build", "B"),
            ("02", "Content", "C", "21", "Video", "V"),
            ("03", "Research", "R", "31", "Sources", "S"),
            ("04", "Finance", "F", "41", "Markets", "M"),
            ("05", "Life", "L", "51", "Personal", "P"),
        ]
        top_levels = [
            {
                "code": top_code,
                "label": top_label,
                "emoji": top_emoji,
                "folder_name": f"{top_code} | {top_label} {top_emoji}",
                "role": "active",
                "children": [
                    {
                        "code": child_code,
                        "label": child_label,
                        "emoji": child_emoji,
                        "folder_name": f"{child_code} | {child_label} {child_emoji}",
                    }
                ],
            }
            for top_code, top_label, top_emoji, child_code, child_label, child_emoji in active
        ]
        top_levels.append(
            {
                "code": "99",
                "label": "Archive",
                "emoji": "A",
                "folder_name": "99 | Archive A",
                "role": "archive",
                "children": [
                    {
                        "code": code,
                        "label": f"Archive {code}",
                        "emoji": "A",
                        "folder_name": f"{code} | Archive A",
                    }
                    for code in ("91", "92", "93", "94", "95")
                ],
            }
        )
        return {
            "primary_axis": "long_term_domains",
            "max_semantic_depth": 2,
            "project_context_owner": "obsidian",
            "reading_list_role": "temporary_inbox",
            "top_levels": top_levels,
        }

    def spec(self, archive: Path) -> tuple[dict, dict]:
        parsed = safari_export.parse_export(archive)
        reviewed = browser_review.review_items(parsed["items"])
        items = reviewed["items"]
        bookmark_article = next(
            item
            for item in items
            if item["item_type"] == "bookmark"
            and item["url"]["original"] == "https://example.invalid/article"
        )
        delete_item = next(
            item
            for item in items
            if item["url"]["original"] == "https://delete.example.invalid/"
        )
        duplicate = next(
            group
            for group in reviewed["duplicate_groups"]
            if group["canonical_url"] == "https://example.invalid/article"
        )
        spec = {
            "organization_id": "borg_fixture_00000001",
            "created_at": "2026-08-15T00:00:00+00:00",
            "taxonomy": self.taxonomy(),
            "path_rules": [
                {
                    "rule_id": "borm_fixture_direct",
                    "source_path": ["Favorites", "Old Direct"],
                    "target_path": ["Favorites", "03 | Research R", "31 | Sources S"],
                }
            ],
            "item_overrides": [
                {
                    "item_id": delete_item["item_id"],
                    "disposition": "delete",
                    "target_collection": None,
                    "note": "Fictional reviewed deletion.",
                }
            ],
            "duplicate_resolutions": [
                {
                    "group_id": duplicate["group_id"],
                    "members": [
                        {
                            "item_id": item_id,
                            "resolution": (
                                "keep"
                                if item_id == bookmark_article["item_id"]
                                else "delete_later"
                            ),
                        }
                        for item_id in duplicate["member_item_ids"]
                    ],
                }
            ],
            "expected": {
                "directory_rule_item_count": 1,
                "ambiguous_item_count": 1,
                "duplicate_group_count": 1,
                "active_move_count": 1,
                "archive_count": 0,
                "bookmark_delete_count": 1,
                "reading_list_delete_later_count": 1,
                "reading_list_deferred_count": 1,
                "bookmark_operation_count": 2,
                "item_count": 4,
            },
            "privacy": {
                "provenance": "private_user_data",
                "storage_layer": "private_icloud",
                "contains_private_content": True,
                "git_allowed": False,
                "redaction_required": True,
            },
            "execution_authorized": False,
        }
        return parsed, spec

    def test_build_is_complete_private_and_schema_valid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = self.archive(Path(tmp))
            parsed, spec = self.spec(archive)
            organization = browser_organization.build_organization(parsed, spec)

        self.assertEqual(len(organization["decisions"]), 4)
        self.assertEqual(len({row["item_id"] for row in organization["decisions"]}), 4)
        self.assertEqual(organization["summary"], spec["expected"])
        self.assertFalse(organization["privacy"]["git_allowed"])
        self.assertFalse(organization["execution_authorized"])
        self.assertEqual(
            schema_contract.validate_document(organization, "browser-organization"),
            [],
        )

    def test_title_suggestion_is_conservative_and_repeatable(self) -> None:
        for _ in range(2):
            result = browser_organization.suggest_title(
                "  Article   -   Example  ",
                "https://example.invalid/article",
            )
            self.assertEqual(result["suggested_title"], "Article")
            self.assertEqual(
                result["rule_ids"],
                ["normalize_whitespace", "remove_matching_site_suffix"],
            )
        unchanged = browser_organization.suggest_title(
            "Meaningful title", "https://example.invalid/"
        )
        self.assertIsNone(unchanged["suggested_title"])
        self.assertEqual(unchanged["rule_ids"], [])

    def test_organization_plan_rechecks_source_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = self.archive(Path(tmp))
            parsed, spec = self.spec(archive)
            organization = browser_organization.build_organization(parsed, spec)
            plan = browser_transactions.build_plan_from_organization(
                archive,
                organization,
                created_at="2026-08-15T00:00:00+00:00",
            )
            self.assertEqual(len(plan["operations"]), 2)
            stale = copy.deepcopy(organization)
            stale["source"]["artifact_sha256"] = "f" * 64
            with self.assertRaisesRegex(
                browser_transactions.BrowserTransactionError,
                "source export has drifted",
            ):
                browser_transactions.build_plan_from_organization(
                    archive,
                    stale,
                    created_at="2026-08-15T00:00:00+00:00",
                )

    def test_missing_or_duplicate_assignment_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = self.archive(Path(tmp))
            parsed, spec = self.spec(archive)
            spec["item_overrides"] = []
            with self.assertRaisesRegex(
                browser_organization.BrowserOrganizationError,
                "exactly one base assignment",
            ):
                browser_organization.build_organization(parsed, spec)

            parsed, spec = self.spec(archive)
            duplicate_rule = dict(spec["path_rules"][0])
            duplicate_rule["rule_id"] = "borm_fixture_overlap"
            spec["path_rules"].append(duplicate_rule)
            with self.assertRaisesRegex(
                browser_organization.BrowserOrganizationError,
                "exactly one base assignment",
            ):
                browser_organization.build_organization(parsed, spec)

    def test_private_spec_cannot_authorize_execution_or_git(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = self.archive(Path(tmp))
            parsed, spec = self.spec(archive)
            spec["execution_authorized"] = True
            with self.assertRaises(browser_organization.BrowserOrganizationError):
                browser_organization.build_organization(parsed, spec)

            parsed, spec = self.spec(archive)
            spec["privacy"]["git_allowed"] = True
            with self.assertRaises(browser_organization.BrowserOrganizationError):
                browser_organization.build_organization(parsed, spec)

    def test_preview_is_redacted_and_apply_requires_exact_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private_root = root / "Private"
            archive = self.archive(root)
            _parsed, spec = self.spec(archive)
            spec_path = root / "private-spec.json"
            spec_path.write_text(json.dumps(spec), encoding="utf-8")
            output = private_root / "browser" / "organization.json"

            stdout = io.StringIO()
            with mock.patch.object(browser_organization, "ROOT", root), mock.patch.object(
                browser_organization, "PRIVATE_ROOT", private_root
            ), redirect_stdout(stdout):
                code = browser_organization.main(
                    [
                        "compile-safari-export",
                        str(archive),
                        "--spec",
                        str(spec_path),
                        "--output",
                        str(output),
                    ]
                )
            self.assertEqual(code, 0)
            self.assertFalse(output.exists())
            preview = json.loads(stdout.getvalue())
            self.assertEqual(preview["status"], "preview")
            self.assertEqual(preview["item_count"], 4)
            for secret in ("example.invalid", "Article", "bri_", str(output)):
                self.assertNotIn(secret, stdout.getvalue())

            stderr = io.StringIO()
            with mock.patch.object(browser_organization, "ROOT", root), mock.patch.object(
                browser_organization, "PRIVATE_ROOT", private_root
            ), redirect_stderr(stderr):
                code = browser_organization.main(
                    [
                        "compile-safari-export",
                        str(archive),
                        "--spec",
                        str(spec_path),
                        "--output",
                        str(output),
                        "--apply",
                        "--confirm",
                        "wrong",
                    ]
                )
            self.assertEqual(code, 1)
            self.assertFalse(output.exists())

            stdout = io.StringIO()
            with mock.patch.object(browser_organization, "ROOT", root), mock.patch.object(
                browser_organization, "PRIVATE_ROOT", private_root
            ), redirect_stdout(stdout):
                code = browser_organization.main(
                    [
                        "compile-safari-export",
                        str(archive),
                        "--spec",
                        str(spec_path),
                        "--output",
                        str(output),
                        "--apply",
                        "--confirm",
                        "SYNC PRIVATE BROWSER ORGANIZATION",
                    ]
                )
            self.assertEqual(code, 0)
            self.assertEqual(output.stat().st_mode & 0o777, 0o600)
            applied = json.loads(stdout.getvalue())
            self.assertEqual(applied["status"], "written")
            self.assertFalse(applied["private_content_emitted"])


if __name__ == "__main__":
    unittest.main()
