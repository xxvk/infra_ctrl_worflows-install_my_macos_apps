#!/usr/bin/env python3
"""TDD contracts for frozen browser plans and post-export verification."""

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


ROOT = Path(__file__).resolve().parents[1]
HTML_FIXTURE = ROOT / "tests" / "fixtures" / "browser" / "safari-bookmarks-only" / "Bookmarks.html"
PLAN_FIXTURE = ROOT / "tests" / "fixtures" / "schema_contract" / "browser-transaction-plan-v1.json"
sys.path.insert(0, str(ROOT / "scripts"))

import browser_lifecycle  # noqa: E402
import browser_transactions  # noqa: E402
import schema_contract  # noqa: E402


class BrowserTransactionTests(unittest.TestCase):
    def archive(self, root: Path, html: bytes | None = None, name: str = "export.zip") -> Path:
        path = root / name
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as output:
            output.writestr(
                "Bookmarks.html",
                html if html is not None else HTML_FIXTURE.read_bytes(),
            )
        return path

    def parsed_items(self, archive: Path) -> list[dict]:
        return browser_transactions.inspect_export(archive)["items"]

    def test_plan_schema_is_registered_and_fixture_is_non_authorizing(self) -> None:
        fixture = schema_contract.load_and_validate(
            PLAN_FIXTURE, "browser-transaction-plan"
        )
        self.assertFalse(fixture["apply_interface"]["supported"])
        self.assertFalse(fixture["execution_authorized"])
        self.assertEqual(browser_transactions.validate_plan(fixture), [])

    def test_plan_binds_verified_export_items_and_additive_recovery_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = self.archive(Path(tmp))
            items = self.parsed_items(archive)
            plan = browser_transactions.build_plan(
                archive,
                [
                    {
                        "action": "delete",
                        "item_id": items[0]["item_id"],
                    }
                ],
                created_at="2026-08-14T00:00:00+00:00",
            )
        self.assertEqual(plan["source"]["item_count"], 4)
        self.assertTrue(plan["backup"]["verified"])
        self.assertEqual(plan["backup"]["recovery_mode"], "manual_import_additive")
        self.assertFalse(plan["backup"]["exact_rollback_supported"])
        self.assertEqual(plan["operations"][0]["action"], "delete")
        self.assertFalse(plan["operations"][0]["executable"])
        self.assertEqual(browser_transactions.validate_plan(plan), [])

    def test_merge_cannot_cross_identity_or_target_itself(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = self.archive(Path(tmp))
            items = self.parsed_items(archive)
            other = copy.deepcopy(items[1])
            other["item_id"] = "bri_fixture_other_identity_0001"
            other["source"]["browser"] = "chrome"
            other["source"]["profile_scope"] = "profile_specific"
            other["source"]["profile_ref"] = "profile-b"
            other["source"]["account_ref"] = "account-b"
            with self.assertRaises(browser_transactions.BrowserTransactionError):
                browser_transactions.build_plan_for_items(
                    items + [other],
                    [
                        {
                            "action": "merge",
                            "item_id": items[0]["item_id"],
                            "target_item_id": other["item_id"],
                        }
                    ],
                    source_path=archive,
                    source_sha256="a" * 64,
                    source_size=1,
                    source_mtime_ns=1,
                    created_at="2026-08-14T00:00:00+00:00",
                )
            with self.assertRaises(browser_transactions.BrowserTransactionError):
                browser_transactions.build_plan_for_items(
                    items,
                    [
                        {
                            "action": "merge",
                            "item_id": items[0]["item_id"],
                            "target_item_id": items[0]["item_id"],
                        }
                    ],
                    source_path=archive,
                    source_sha256="a" * 64,
                    source_size=1,
                    source_mtime_ns=1,
                    created_at="2026-08-14T00:00:00+00:00",
                )

    def test_move_requires_target_and_delete_forbids_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = self.archive(Path(tmp))
            item_id = self.parsed_items(archive)[0]["item_id"]
            for operation in (
                {"action": "move", "item_id": item_id},
                {
                    "action": "delete",
                    "item_id": item_id,
                    "target_collection": ["Should not exist"],
                },
            ):
                with self.subTest(operation=operation):
                    with self.assertRaises(browser_transactions.BrowserTransactionError):
                        browser_transactions.build_plan(
                            archive,
                            [operation],
                            created_at="2026-08-14T00:00:00+00:00",
                        )

    def test_freeze_requires_exact_confirmation_and_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = self.archive(root)
            item_id = self.parsed_items(archive)[0]["item_id"]
            plan = browser_transactions.build_plan(
                archive,
                [{"action": "delete", "item_id": item_id}],
                created_at="2026-08-14T00:00:00+00:00",
            )
            state = root / "state"
            with self.assertRaisesRegex(ValueError, "FREEZE BROWSER PLAN"):
                browser_transactions.freeze_plan(plan, state, confirmation="wrong")
            self.assertFalse(state.exists())
            first = browser_transactions.freeze_plan(
                plan,
                state,
                confirmation="FREEZE BROWSER PLAN",
            )
            second = browser_transactions.freeze_plan(
                plan,
                state,
                confirmation="FREEZE BROWSER PLAN",
            )
            destination = state / "browser" / "plans" / f"{plan['plan_id']}.json"
            self.assertEqual(destination.stat().st_mode & 0o777, 0o600)
            destination.write_text("{}\n", encoding="utf-8")
            with self.assertRaisesRegex(
                browser_transactions.BrowserTransactionError, "overwrite"
            ):
                browser_transactions.freeze_plan(
                    plan,
                    state,
                    confirmation="FREEZE BROWSER PLAN",
                )
        self.assertEqual(first["status"], "written")
        self.assertEqual(second["status"], "unchanged")
        self.assertEqual(first["action_id"], "browser.plan-freeze")
        self.assertTrue(first["verified"])

    def test_tampered_plan_is_rejected_before_freeze_or_verification(self) -> None:
        fixture = json.loads(PLAN_FIXTURE.read_text(encoding="utf-8"))
        fixture["operations"][0]["action"] = "archive"
        self.assertIn("plan_sha256", " ".join(browser_transactions.validate_plan(fixture)))
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(browser_transactions.BrowserTransactionError):
                browser_transactions.freeze_plan(
                    fixture,
                    Path(tmp),
                    confirmation="FREEZE BROWSER PLAN",
                )

    def test_export_or_item_drift_stops_preapply(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = self.archive(root)
            item_id = self.parsed_items(archive)[0]["item_id"]
            plan = browser_transactions.build_plan(
                archive,
                [{"action": "delete", "item_id": item_id}],
                created_at="2026-08-14T00:00:00+00:00",
            )
            changed = self.archive(
                root,
                b"""<!DOCTYPE NETSCAPE-Bookmark-file-1><DL><p>
<DT><A HREF=\"https://changed.example.invalid\">Changed</A></DL><p>""",
                "changed.zip",
            )
            result = browser_transactions.verify_preapply(plan, changed)
        self.assertEqual(result["status"], "failed")
        self.assertIn("source_export_changed", result["reasons"])
        self.assertFalse(result["writes_performed"])

    def test_live_apply_is_explicitly_unavailable_even_after_fresh_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = self.archive(root)
            item_id = self.parsed_items(archive)[0]["item_id"]
            plan = browser_transactions.build_plan(
                archive,
                [{"action": "delete", "item_id": item_id}],
                created_at="2026-08-14T00:00:00+00:00",
            )
            result = browser_transactions.apply_live_safari(plan, archive)
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["reason"], "supported_item_write_interface_unavailable")
        self.assertFalse(result["writes_performed"])
        self.assertFalse(result["execution_authorized"])

    def test_post_export_verifies_delete_and_move_without_raw_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            pre = self.archive(
                root,
                b"""<!DOCTYPE NETSCAPE-Bookmark-file-1><DL><p>
<DT><H3>Old</H3><DL><p>
<DT><A HREF=\"https://delete.example.invalid\">Delete me</A>
<DT><A HREF=\"https://move.example.invalid\">Move me</A>
</DL><p></DL><p>""",
                "pre.zip",
            )
            items = self.parsed_items(pre)
            by_title = {item["title"]: item for item in items}
            plan = browser_transactions.build_plan(
                pre,
                [
                    {"action": "delete", "item_id": by_title["Delete me"]["item_id"]},
                    {
                        "action": "move",
                        "item_id": by_title["Move me"]["item_id"],
                        "target_collection": ["New"],
                    },
                ],
                created_at="2026-08-14T00:00:00+00:00",
            )
            post = self.archive(
                root,
                b"""<!DOCTYPE NETSCAPE-Bookmark-file-1><DL><p>
<DT><H3>New</H3><DL><p>
<DT><A HREF=\"https://move.example.invalid\">Move me</A>
</DL><p></DL><p>""",
                "post.zip",
            )
            result = browser_transactions.verify_post_export(plan, post)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["verified_operation_count"], 2)
        self.assertEqual(result["failed_operation_count"], 0)
        self.assertFalse(result["private_content_emitted"])

    def test_cli_preview_emits_no_url_title_or_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = self.archive(
                root,
                b"""<!DOCTYPE NETSCAPE-Bookmark-file-1><DL><p>
<DT><A HREF=\"https://private.example.invalid\">PRIVATE TITLE</A></DL><p>""",
            )
            item_id = self.parsed_items(archive)[0]["item_id"]
            operations = root / "private-operations.json"
            operations.write_text(
                json.dumps([{"action": "delete", "item_id": item_id}]),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                returncode = browser_transactions.main(
                    [
                        "plan-safari-export",
                        str(archive),
                        "--operations",
                        str(operations),
                        "--created-at",
                        "2026-08-14T00:00:00+00:00",
                    ]
                )
        self.assertEqual(returncode, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "preview")
        self.assertFalse(payload["writes_performed"])
        for secret in (
            "private.example.invalid",
            "PRIVATE TITLE",
            "bri_",
            "export.zip",
            "private-operations.json",
        ):
            self.assertNotIn(secret, stdout.getvalue())

    def test_organization_generates_bookmark_operations_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = self.archive(
                root,
                b"""<!DOCTYPE NETSCAPE-Bookmark-file-1><DL><p>
<DT><A HREF=\"https://move.example.invalid\">Move - Example</A>
<DT><A HREF=\"https://delete.example.invalid\">Delete</A></DL><p>""",
            )
            inspected = browser_transactions.inspect_export(archive)
            decisions = []
            for item in inspected["items"]:
                move = item["url"]["original"].startswith("https://move")
                decisions.append(
                    {
                        "item_id": item["item_id"],
                        "item_fingerprint": browser_lifecycle.item_fingerprint(item),
                        "item_type": "bookmark",
                        "original_title": item["title"],
                        "suggested_title": "Move" if move else None,
                        "title_suggestion_rule_ids": (
                            ["remove_matching_site_suffix"] if move else []
                        ),
                        "original_url": item["url"]["original"],
                        "source_collection": item["collection"]["path"],
                        "assignment_basis": "path_rule" if move else "item_override",
                        "rule_id": "borm_fixture" if move else None,
                        "duplicate_group_id": None,
                        "disposition": "move" if move else "delete",
                        "target_collection": (
                            ["Favorites", "03 | Research R", "31 | Sources S"]
                            if move
                            else None
                        ),
                        "note": None,
                        "execution_authorized": False,
                    }
                )
            organization = {
                "source": {"artifact_sha256": inspected["sha256"]},
                "decisions": decisions,
                "execution_authorized": False,
            }
            operations = browser_transactions.operations_from_organization(
                organization, inspected["items"]
            )
            plan = browser_transactions.build_plan(
                archive,
                operations,
                created_at="2026-08-15T00:00:00+00:00",
            )

        self.assertEqual([row["action"] for row in operations], ["move", "delete"])
        rendered = json.dumps(plan)
        self.assertNotIn("suggested_title", rendered)
        self.assertNotIn("Move - Example", rendered)
        self.assertTrue(all(not row["executable"] for row in plan["operations"]))

    def test_apply_cli_failure_retains_apply_summary_kind(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            returncode = browser_transactions.main(
                [
                    "apply-live-safari",
                    "/tmp/missing-private-plan.json",
                    "/tmp/missing-private-export.zip",
                ]
            )
        self.assertEqual(returncode, 1)
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["kind"], "browser_transaction_apply_summary")
        self.assertFalse(payload["private_content_emitted"])


if __name__ == "__main__":
    unittest.main()
