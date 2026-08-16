#!/usr/bin/env python3
"""TDD contracts for Safari-only BR-08 live acceptance."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML_FIXTURE = ROOT / "tests" / "fixtures" / "browser" / "safari-bookmarks-only" / "Bookmarks.html"
sys.path.insert(0, str(ROOT / "scripts"))

import browser_acceptance  # noqa: E402
import safari_export  # noqa: E402
import schema_contract  # noqa: E402


class BrowserAcceptanceTests(unittest.TestCase):
    def archive(self, root: Path, html: bytes | None = None) -> Path:
        path = root / "private-safari-export.zip"
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as output:
            output.writestr("Bookmarks.html", html or HTML_FIXTURE.read_bytes())
        return path

    def capability(self) -> dict:
        return {
            "schema_version": 1,
            "kind": "safari_source_capability_inspection",
            "privacy_boundary": "capability_metadata_only",
            "safari": {
                "present": True,
                "version": "27.0",
                "build": "22625.fixture",
            },
            "official_export": {
                "support": "supported_user_mediated",
                "content_read": False,
            },
            "private_item_content": "not_read",
        }

    def empty_ledger(self) -> dict:
        return {
            "schema_version": 1,
            "kind": "browser_decision_ledger",
            "ledger_id": "bdl_fixture_acceptance",
            "updated_at": "2026-08-14T00:00:00+00:00",
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

    def test_repository_acceptance_contract_is_valid(self) -> None:
        result = browser_acceptance.validate_contract()
        self.assertEqual(result["status"], "passed", result["errors"])
        self.assertEqual(result["gate_count"], 10)
        self.assertEqual(result["chrome_status"], "deferred_by_user")
        contract = browser_acceptance._load_contract()
        self.assertEqual(
            next(gate["name"] for gate in contract["gates"] if gate["id"] == "BA-02"),
            "explicit Bookmarks and Reading List export",
        )

    def test_export_only_acceptance_is_deterministic_and_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export = self.archive(Path(tmp))
            result = browser_acceptance.inspect_live(
                export,
                capability=self.capability(),
                captured_at="2026-08-14T00:00:00+00:00",
            )
        gates = {row["id"]: row for row in result["gates"]}
        self.assertEqual(result["status"], "partial")
        self.assertEqual(gates["BA-02"]["status"], "passed")
        self.assertEqual(gates["BA-03"]["status"], "passed")
        self.assertEqual(gates["BA-04"]["status"], "passed")
        self.assertEqual(gates["BA-08"]["status"], "interface_limited")
        self.assertEqual(gates["BA-10"]["status"], "deferred")
        self.assertGreater(result["counts"]["bookmark_count"], 0)
        self.assertFalse(result["private_content_emitted"])
        self.assertFalse(result["writes_performed"])
        self.assertFalse(result["execution_authorized"])
        serialized = json.dumps(result)
        self.assertNotIn("private-safari-export.zip", serialized)
        self.assertNotIn("http", serialized)
        self.assertNotIn("bri_", serialized)
        self.assertEqual(
            schema_contract.validate_document(result, "browser-acceptance"), []
        )

    def test_ledger_and_plan_gates_are_repeatable_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            export = self.archive(root)
            item_id = safari_export.parse_export(export)["items"][0]["item_id"]
            result = browser_acceptance.inspect_live(
                export,
                capability=self.capability(),
                ledger=self.empty_ledger(),
                operations=[{"action": "delete", "item_id": item_id}],
                as_of="2026-08-14",
                captured_at="2026-08-14T00:00:00+00:00",
            )
        gates = {row["id"]: row for row in result["gates"]}
        self.assertEqual(gates["BA-06"]["status"], "passed")
        self.assertEqual(gates["BA-07"]["status"], "passed")
        self.assertEqual(gates["BA-08"]["reason"], "supported_item_write_interface_unavailable")
        self.assertEqual(result["counts"]["planned_operation_count"], 1)
        self.assertFalse(result["browser_writes_performed"])

    def test_post_export_mismatch_fails_acceptance_without_private_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            export = self.archive(root)
            item_id = safari_export.parse_export(export)["items"][0]["item_id"]
            result = browser_acceptance.inspect_live(
                export,
                capability=self.capability(),
                operations=[{"action": "delete", "item_id": item_id}],
                post_export=export,
                captured_at="2026-08-14T00:00:00+00:00",
            )
        gates = {row["id"]: row for row in result["gates"]}
        self.assertEqual(result["status"], "failed")
        self.assertEqual(gates["BA-09"]["status"], "failed")
        self.assertEqual(gates["BA-09"]["reason"], "post_export_mismatch")
        self.assertFalse(result["private_content_emitted"])

    def test_invalid_export_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            invalid = Path(tmp) / "private-name.zip"
            invalid.write_bytes(b"not a zip")
            result = browser_acceptance.inspect_live(
                invalid,
                capability=self.capability(),
                captured_at="2026-08-14T00:00:00+00:00",
            )
        self.assertEqual(result["status"], "failed")
        self.assertEqual(
            {row["id"]: row["status"] for row in result["gates"]}["BA-02"],
            "failed",
        )
        self.assertNotIn("private-name.zip", json.dumps(result))

    def test_cli_emits_summary_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            export = self.archive(Path(tmp))
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                returncode = browser_acceptance.main(
                    ["inspect-live", str(export), "--captured-at", "2026-08-14T00:00:00+00:00"],
                    capability_provider=self.capability,
                )
        self.assertEqual(returncode, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["kind"], "browser_live_acceptance_summary")
        for secret in ("private-safari-export.zip", "bri_", "http", "Bookmarks.html"):
            self.assertNotIn(secret, stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
