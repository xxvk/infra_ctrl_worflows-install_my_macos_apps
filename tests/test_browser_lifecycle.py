#!/usr/bin/env python3
"""TDD contracts for browser taxonomy and private decision memory."""

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
ITEM_FIXTURE = ROOT / "tests" / "fixtures" / "schema_contract" / "browser-item-v1.json"
LEDGER_FIXTURE = ROOT / "examples" / "private" / "browser-decision-ledger.json"
sys.path.insert(0, str(ROOT / "scripts"))

import browser_lifecycle  # noqa: E402
import browser_review  # noqa: E402
import schema_contract  # noqa: E402


class BrowserLifecycleTests(unittest.TestCase):
    def item(
        self,
        item_id: str,
        *,
        title: str = "Fictional item",
        account_ref: str | None = None,
    ) -> dict:
        item = json.loads(ITEM_FIXTURE.read_text(encoding="utf-8"))
        item["item_id"] = item_id
        item["title"] = title
        item["source"]["artifact_ref"] = "private-export-a"
        item["source"]["account_ref"] = account_ref
        item["privacy"] = {
            "provenance": "private_export",
            "storage_layer": "private_icloud",
            "contains_private_content": True,
            "git_allowed": False,
            "redaction_required": True,
        }
        reviewed = browser_review.review_items([item])
        return reviewed["items"][0]

    def empty_ledger(self) -> dict:
        return {
            "schema_version": 1,
            "kind": "browser_decision_ledger",
            "ledger_id": "bdl_fixture_private_0001",
            "updated_at": "2026-08-01T00:00:00+00:00",
            "custom_classifications": [],
            "decisions": [],
            "privacy": {
                "provenance": "private_user_data",
                "storage_layer": "private_icloud",
                "contains_private_content": True,
                "git_allowed": False,
                "redaction_required": True,
            },
            "execution_authorized": False,
        }

    def test_policy_and_private_example_are_registered_and_non_authorizing(self) -> None:
        result = browser_lifecycle.validate_policy()
        self.assertEqual(result["status"], "passed", result["errors"])
        self.assertEqual(
            result["builtin_classifications"],
            ["inbox", "project", "reference", "read_later", "archive"],
        )
        self.assertFalse(result["execution_authorized"])
        schema_contract.load_and_validate(
            ROOT / "settings" / "browser-lifecycle-policy.json",
            "browser-lifecycle-policy",
        )
        schema_contract.load_and_validate(LEDGER_FIXTURE, "browser-decision-ledger")

    def test_builtin_and_custom_decisions_receive_review_dates(self) -> None:
        item = self.item("bri_fixture_lifecycle_01")
        ledger = self.empty_ledger()
        built_in = browser_lifecycle.build_decision(
            item,
            "read_later",
            ledger=ledger,
            decided_at="2026-08-01T00:00:00+00:00",
        )
        self.assertEqual(built_in["review_after"], "2026-08-31")

        ledger["custom_classifications"] = [
            {
                "classification_id": "bcx_fixture_learning",
                "label": "Fictional learning",
                "review_days": 45,
                "status": "active",
            }
        ]
        custom = browser_lifecycle.build_decision(
            item,
            "bcx_fixture_learning",
            ledger=ledger,
            decided_at="2026-08-01T00:00:00+00:00",
        )
        self.assertEqual(custom["review_after"], "2026-09-15")
        self.assertFalse(custom["execution_authorized"])

    def test_private_fingerprint_survives_export_and_item_id_change(self) -> None:
        first = self.item("bri_fixture_lifecycle_11")
        second = copy.deepcopy(first)
        second["item_id"] = "bri_fixture_lifecycle_12"
        second["source"]["artifact_ref"] = "private-export-b"
        second["identity"]["namespace_ref"] = "different-private-export"
        self.assertEqual(
            browser_lifecycle.item_fingerprint(first),
            browser_lifecycle.item_fingerprint(second),
        )
        second["title"] = "Changed title"
        self.assertNotEqual(
            browser_lifecycle.item_fingerprint(first),
            browser_lifecycle.item_fingerprint(second),
        )

    def test_unchanged_item_is_suppressed_until_review_date(self) -> None:
        first = self.item("bri_fixture_lifecycle_21")
        ledger = self.empty_ledger()
        decision = browser_lifecycle.build_decision(
            first,
            "reference",
            ledger=ledger,
            decided_at="2026-08-01T00:00:00+00:00",
        )
        ledger = browser_lifecycle.record_decision(ledger, decision)

        reexported = copy.deepcopy(first)
        reexported["item_id"] = "bri_fixture_lifecycle_22"
        reexported["source"]["artifact_ref"] = "new-export"
        queue = browser_lifecycle.build_review_queue(
            [reexported], ledger, as_of="2026-08-14"
        )
        self.assertEqual(queue["queued"], [])
        self.assertEqual(queue["suppressed"][0]["reason"], "review_not_due")

        expired = browser_lifecycle.build_review_queue(
            [reexported], ledger, as_of="2027-02-01"
        )
        self.assertEqual(expired["queued"][0]["reason"], "review_due")

    def test_changed_or_cross_identity_item_reenters_queue(self) -> None:
        original = self.item("bri_fixture_lifecycle_31", account_ref="account-a")
        ledger = self.empty_ledger()
        ledger = browser_lifecycle.record_decision(
            ledger,
            browser_lifecycle.build_decision(
                original,
                "project",
                ledger=ledger,
                decided_at="2026-08-01T00:00:00+00:00",
            ),
        )

        changed = copy.deepcopy(original)
        changed["title"] = "Changed title"
        changed_result = browser_lifecycle.build_review_queue(
            [changed], ledger, as_of="2026-08-14"
        )
        self.assertEqual(changed_result["queued"][0]["reason"], "item_changed")

        other_account = copy.deepcopy(original)
        other_account["item_id"] = "bri_fixture_lifecycle_32"
        other_account["source"]["account_ref"] = "account-b"
        cross_result = browser_lifecycle.build_review_queue(
            [other_account], ledger, as_of="2026-08-14"
        )
        self.assertEqual(cross_result["queued"][0]["reason"], "unreviewed")

    def test_ambiguous_fingerprint_does_not_suppress_a_new_item(self) -> None:
        one = self.item("bri_fixture_lifecycle_41")
        two = copy.deepcopy(one)
        two["item_id"] = "bri_fixture_lifecycle_42"
        ledger = self.empty_ledger()
        for item in (one, two):
            ledger = browser_lifecycle.record_decision(
                ledger,
                browser_lifecycle.build_decision(
                    item,
                    "archive",
                    ledger=ledger,
                    decided_at="2026-08-01T00:00:00+00:00",
                ),
            )
        incoming = copy.deepcopy(one)
        incoming["item_id"] = "bri_fixture_lifecycle_43"
        result = browser_lifecycle.build_review_queue(
            [incoming], ledger, as_of="2026-08-14"
        )
        self.assertEqual(result["queued"][0]["reason"], "ambiguous_memory")

    def test_recording_a_new_decision_preserves_superseded_history(self) -> None:
        item = self.item("bri_fixture_lifecycle_51")
        ledger = self.empty_ledger()
        first = browser_lifecycle.build_decision(
            item,
            "inbox",
            ledger=ledger,
            decided_at="2026-08-01T00:00:00+00:00",
        )
        ledger = browser_lifecycle.record_decision(ledger, first)
        second = browser_lifecycle.build_decision(
            item,
            "project",
            ledger=ledger,
            decided_at="2026-08-02T00:00:00+00:00",
        )
        ledger = browser_lifecycle.record_decision(ledger, second)
        self.assertEqual([row["status"] for row in ledger["decisions"]], ["superseded", "active"])
        self.assertEqual(schema_contract.validate_document(ledger, "browser-decision-ledger"), [])

    def test_unknown_or_retired_custom_classification_is_rejected(self) -> None:
        item = self.item("bri_fixture_lifecycle_61")
        ledger = self.empty_ledger()
        ledger["custom_classifications"] = [
            {
                "classification_id": "bcx_fixture_retired",
                "label": "Retired",
                "review_days": 90,
                "status": "retired",
            }
        ]
        for classification in ("bcx_missing", "bcx_fixture_retired"):
            with self.subTest(classification=classification):
                with self.assertRaises(browser_lifecycle.BrowserLifecycleError):
                    browser_lifecycle.build_decision(
                        item,
                        classification,
                        ledger=ledger,
                        decided_at="2026-08-01T00:00:00+00:00",
                    )

    def test_private_ledger_cannot_claim_git_authority(self) -> None:
        ledger = self.empty_ledger()
        ledger["privacy"]["git_allowed"] = True
        self.assertTrue(
            schema_contract.validate_document(ledger, "browser-decision-ledger")
        )
        result = browser_lifecycle.validate_ledger(ledger)
        self.assertEqual(result["status"], "failed")
        self.assertFalse(result["private_content_emitted"])

    def test_review_date_must_follow_decision_date(self) -> None:
        with self.assertRaisesRegex(browser_lifecycle.BrowserLifecycleError, "after"):
            browser_lifecycle.build_decision(
                self.item("bri_fixture_lifecycle_71"),
                "inbox",
                ledger=self.empty_ledger(),
                decided_at="2026-08-01T00:00:00+00:00",
                review_after="2026-08-01",
            )

    def test_cli_summary_does_not_emit_private_content_or_ids(self) -> None:
        html = b"""<!DOCTYPE NETSCAPE-Bookmark-file-1>
<DL><p><DT><A HREF=\"https://private.example.invalid/a\">PRIVATE TITLE</A></DL><p>"""
        ledger = self.empty_ledger()
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "private-export.zip"
            ledger_path = Path(tmp) / "private-ledger.json"
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as output:
                output.writestr("Bookmarks.html", html)
            ledger_path.write_text(json.dumps(ledger), encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                returncode = browser_lifecycle.main(
                    [
                        "review-safari-export",
                        str(archive),
                        "--ledger",
                        str(ledger_path),
                        "--as-of",
                        "2026-08-14",
                    ]
                )
        self.assertEqual(returncode, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["queued_count"], 1)
        self.assertFalse(payload["private_content_emitted"])
        self.assertFalse(payload["writes_performed"])
        for secret in (
            "private.example.invalid",
            "PRIVATE TITLE",
            "bri_",
            "private-export.zip",
            "private-ledger.json",
        ):
            self.assertNotIn(secret, stdout.getvalue())

    def test_history_cli_failure_retains_history_summary_kind(self) -> None:
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            returncode = browser_lifecycle.main(
                ["inspect-ledger", "/tmp/missing-private-ledger.json"]
            )
        self.assertEqual(returncode, 1)
        payload = json.loads(stderr.getvalue())
        self.assertEqual(payload["kind"], "browser_history_redacted_summary")
        self.assertFalse(payload["private_content_emitted"])


if __name__ == "__main__":
    unittest.main()
