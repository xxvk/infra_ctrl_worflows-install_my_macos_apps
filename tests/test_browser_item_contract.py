#!/usr/bin/env python3
"""Contracts for the private browser-item model introduced by BR-02."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "schema_contract" / "browser-item-v1.json"
sys.path.insert(0, str(ROOT / "scripts"))

import schema_contract  # noqa: E402


class BrowserItemContractTests(unittest.TestCase):
    def load_fixture(self) -> dict:
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_registered_synthetic_browser_item_validates(self) -> None:
        item = schema_contract.load_and_validate(FIXTURE, "browser-item")
        self.assertEqual(item["kind"], "browser_item")
        self.assertEqual(item["privacy"]["provenance"], "synthetic_fixture")
        self.assertTrue(item["privacy"]["git_allowed"])

    def test_private_item_cannot_claim_git_is_allowed(self) -> None:
        item = self.load_fixture()
        item["privacy"] = {
            "provenance": "private_export",
            "storage_layer": "private_icloud",
            "contains_private_content": True,
            "git_allowed": True,
            "redaction_required": True,
        }
        errors = schema_contract.validate_document(item, "browser-item")
        self.assertTrue(any("privacy" in error for error in errors), errors)

        item["privacy"]["git_allowed"] = False
        self.assertEqual(schema_contract.validate_document(item, "browser-item"), [])

    def test_required_identity_lifecycle_and_conflict_fields_fail_closed(self) -> None:
        for field in (
            "item_id",
            "identity",
            "source",
            "collection",
            "url",
            "title",
            "tags",
            "intended_lifecycle",
            "confidence",
            "decision_expiry",
            "conflict_evidence",
            "privacy",
            "execution_authorized",
        ):
            with self.subTest(field=field):
                item = self.load_fixture()
                item.pop(field)
                errors = schema_contract.validate_document(item, "browser-item")
                self.assertTrue(any(field in error for error in errors), errors)

    def test_item_identity_is_opaque_and_not_a_bare_url_hash(self) -> None:
        item = self.load_fixture()
        item["item_id"] = "a" * 64
        errors = schema_contract.validate_document(item, "browser-item")
        self.assertTrue(any("item_id" in error and "pattern" in error for error in errors), errors)

    def test_profile_and_account_boundaries_are_explicit(self) -> None:
        item = self.load_fixture()
        source = item["source"]
        self.assertIn("profile_scope", source)
        self.assertIn("profile_ref", source)
        self.assertIn("account_ref", source)
        self.assertEqual(source["profile_scope"], "shared_across_profiles")
        self.assertIsNone(source["profile_ref"])
        self.assertIsNone(source["account_ref"])


if __name__ == "__main__":
    unittest.main()
