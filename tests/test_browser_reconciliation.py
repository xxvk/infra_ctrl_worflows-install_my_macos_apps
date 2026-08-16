#!/usr/bin/env python3
"""TDD contracts for source-drift browser organization reconciliation."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import browser_organization  # noqa: E402
import browser_reconciliation  # noqa: E402
import browser_review  # noqa: E402
import safari_export  # noqa: E402


class BrowserReconciliationTests(unittest.TestCase):
    BOOKMARKS = b"""<!DOCTYPE NETSCAPE-Bookmark-file-1>
<DL><p><DT><H3>Favorites</H3><DL><p>
<DT><H3>Old Direct</H3><DL><p>
<DT><A HREF=\"https://example.invalid/article\">Article</A>
</DL><p><DT><H3>Old Ambiguous</H3><DL><p>
<DT><A HREF=\"https://delete.example.invalid/\">Delete Me</A>
</DL><p></DL><p></DL><p>"""
    READING = b"""<!DOCTYPE NETSCAPE-Bookmark-file-1>
<DL><p><DT><H3>com.apple.ReadingList</H3><DL><p>
<DT><A HREF=\"https://example.invalid/article\">Article duplicate</A>
<DT><A HREF=\"https://later.example.invalid/\">Read Later</A>
</DL><p></DL><p>"""

    def archive(self, root: Path, name: str, *, changed: bool = False, apple_double: bool = False) -> Path:
        path = root / name
        bookmarks = self.BOOKMARKS.replace(b"Delete Me", b"Changed title") if changed else self.BOOKMARKS
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as output:
            output.writestr("Bookmarks.html", bookmarks)
            output.writestr("ReadingList.html", self.READING)
            if apple_double:
                output.writestr("__MACOSX/._Bookmarks.html", b"fictional metadata")
        return path

    def taxonomy(self) -> dict:
        tops = []
        for top, top_name, child, child_name in (
            ("01", "Work", "11", "Build"),
            ("02", "Content", "21", "Video"),
            ("03", "Research", "31", "Sources"),
            ("04", "Finance", "41", "Markets"),
            ("05", "Life", "51", "Personal"),
        ):
            tops.append(
                {
                    "code": top,
                    "label": top_name,
                    "emoji": top_name[0],
                    "folder_name": f"{top} | {top_name}",
                    "role": "active",
                    "children": [
                        {
                            "code": child,
                            "label": child_name,
                            "emoji": child_name[0],
                            "folder_name": f"{child} | {child_name}",
                        }
                    ],
                }
            )
        tops.append(
            {
                "code": "99",
                "label": "Archive",
                "emoji": "A",
                "folder_name": "99 | Archive",
                "role": "archive",
                "children": [
                    {"code": code, "label": code, "emoji": "A", "folder_name": f"{code} | Archive"}
                    for code in ("91", "92", "93", "94", "95")
                ],
            }
        )
        return {
            "primary_axis": "long_term_domains",
            "max_semantic_depth": 2,
            "project_context_owner": "obsidian",
            "reading_list_role": "temporary_inbox",
            "top_levels": tops,
        }

    def old_organization(self, archive: Path) -> dict:
        parsed = safari_export.parse_export(archive)
        reviewed = browser_review.review_items(parsed["items"])
        delete = next(item for item in reviewed["items"] if item["url"]["original"].startswith("https://delete"))
        bookmark = next(
            item
            for item in reviewed["items"]
            if item["item_type"] == "bookmark" and item["url"]["original"].startswith("https://example")
        )
        group = reviewed["duplicate_groups"][0]
        spec = {
            "organization_id": "borg_reconcile_fixture_old",
            "created_at": "2026-08-15T00:00:00+00:00",
            "taxonomy": self.taxonomy(),
            "path_rules": [
                {
                    "rule_id": "borm_reconcile_direct",
                    "source_path": ["Favorites", "Old Direct"],
                    "target_path": ["Favorites", "03 | Research", "31 | Sources"],
                }
            ],
            "item_overrides": [
                {
                    "item_id": delete["item_id"],
                    "disposition": "delete",
                    "target_collection": None,
                    "note": "Fictional reviewed deletion.",
                }
            ],
            "duplicate_resolutions": [
                {
                    "group_id": group["group_id"],
                    "members": [
                        {
                            "item_id": item_id,
                            "resolution": "keep" if item_id == bookmark["item_id"] else "delete_later",
                        }
                        for item_id in group["member_item_ids"]
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
        return browser_organization.build_organization(parsed, spec)

    def test_semantically_identical_new_export_builds_versioned_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old_export = self.archive(root, "old.zip")
            new_export = self.archive(root, "new.zip", apple_double=True)
            old = self.old_organization(old_export)
            result = browser_reconciliation.reconcile_organization(
                old,
                new_export,
                reconciled_on="2026-08-16",
            )
        self.assertTrue(result["summary"]["source_hash_changed"])
        self.assertEqual(result["summary"]["fingerprint_inherited_count"], 4)
        self.assertEqual(result["summary"]["stable_duplicate_group_count"], 1)
        self.assertEqual(result["summary"]["review_required_count"], 0)
        self.assertTrue(result["summary"]["candidate_ready"])
        self.assertIsNotNone(result["candidate"])
        self.assertEqual(result["candidate"]["summary"], old["summary"])
        self.assertNotEqual(result["candidate"]["source"]["artifact_sha256"], old["source"]["artifact_sha256"])

    def test_changed_item_requires_review_and_blocks_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old_export = self.archive(root, "old.zip")
            changed_export = self.archive(root, "changed.zip", changed=True, apple_double=True)
            result = browser_reconciliation.reconcile_organization(
                self.old_organization(old_export),
                changed_export,
                reconciled_on="2026-08-16",
            )
        self.assertGreater(result["summary"]["review_required_count"], 0)
        self.assertGreater(result["summary"]["removed_item_count"], 0)
        self.assertFalse(result["summary"]["candidate_ready"])
        self.assertIsNone(result["candidate"])

    def test_candidate_write_requires_exact_confirmation_and_never_switches_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private = root / "Private"
            old_export = self.archive(root, "old.zip")
            new_export = self.archive(root, "new.zip", apple_double=True)
            result = browser_reconciliation.reconcile_organization(
                self.old_organization(old_export),
                new_export,
                reconciled_on="2026-08-16",
            )
            with self.assertRaisesRegex(ValueError, "WRITE PRIVATE BROWSER RECONCILIATION CANDIDATE"):
                browser_reconciliation.write_candidate(
                    result["candidate"],
                    reconciled_on="2026-08-16",
                    apply=True,
                    confirmation="wrong",
                    root=root,
                    private_root=private,
                )
            record = browser_reconciliation.write_candidate(
                result["candidate"],
                reconciled_on="2026-08-16",
                apply=True,
                confirmation="WRITE PRIVATE BROWSER RECONCILIATION CANDIDATE",
                root=root,
                private_root=private,
            )
            versions = list((private / "browser" / "versions").glob("*.json"))
            self.assertEqual(record["status"], "written")
            self.assertEqual(len(versions), 1)
            self.assertEqual(versions[0].stat().st_mode & 0o777, 0o600)
            self.assertFalse((private / "browser" / "organization.json").exists())


if __name__ == "__main__":
    unittest.main()
