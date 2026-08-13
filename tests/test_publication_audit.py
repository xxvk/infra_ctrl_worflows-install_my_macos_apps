#!/usr/bin/env python3
"""Hermetic contracts for public-release inventory and classification."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import publication_audit  # noqa: E402


class PublicationAuditTests(unittest.TestCase):
    def test_repository_policy_is_valid(self) -> None:
        result = publication_audit.validate()
        self.assertEqual(result["status"], "passed", result["errors"])
        self.assertGreaterEqual(result["pattern_count"], 5)

    def test_public_governance_surface_is_complete(self) -> None:
        policy = publication_audit.load_policy()
        self.assertEqual(
            set(policy["governance_files"]),
            {
                "LICENSE",
                "SECURITY.md",
                "CONTRIBUTING.md",
                "CODE_OF_CONDUCT.md",
                "CHANGELOG.md",
                "THIRD_PARTY_NOTICES.md",
            },
        )
        result = publication_audit.scan_current_tree(ROOT, [], policy)
        self.assertEqual(result["missing_governance_files"], [])

    def test_current_tree_findings_never_copy_sensitive_values(self) -> None:
        secret_email = "private-person@example.invalid"
        secret_token = "ghp_abcdefghijklmnopqrstuvwxyz123456"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private = root / "Private/profile.json"
            private.parent.mkdir()
            private.write_text(json.dumps({"email": secret_email, "token": secret_token}))
            test_file = root / "tests/fixture.txt"
            test_file.parent.mkdir()
            test_file.write_text("fixture@example.invalid")
            result = publication_audit.scan_current_tree(
                root,
                ["Private/profile.json", "tests/fixture.txt"],
                publication_audit.load_policy(),
            )
        serialized = json.dumps(result)
        self.assertNotIn(secret_email, serialized)
        self.assertNotIn(secret_token, serialized)
        self.assertIn("Private/profile.json", serialized)
        self.assertTrue(any(item["id"] == "email-address" for item in result["sensitive_findings"]))

    def test_classification_requires_review_without_authorizing_changes(self) -> None:
        result = publication_audit.classify(
            current={
                "private_files": ["Private/example.json"],
                "sensitive_findings": [{"id": "email-address", "paths": ["Private/example.json"]}],
                "missing_governance_files": ["LICENSE"],
                "large_files": [],
                "binary_files": [],
                "generated_artifacts": [],
                "third_party_assets": [],
                "submodules": [],
            },
            history={"commit_count": 3, "private_commit_count": 2, "sensitive_findings": []},
        )
        self.assertEqual(result["status"], "review_required")
        self.assertFalse(result["visibility_change_authorized"])
        self.assertFalse(result["history_rewrite_authorized"])


if __name__ == "__main__":
    unittest.main()
