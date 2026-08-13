from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "references" / "public-support-safety.md"
BUG_FORM = ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml"
FEATURE_FORM = ROOT / ".github" / "ISSUE_TEMPLATE" / "feature_request.yml"
ISSUE_CONFIG = ROOT / ".github" / "ISSUE_TEMPLATE" / "config.yml"
PULL_REQUEST_TEMPLATE = ROOT / ".github" / "PULL_REQUEST_TEMPLATE.md"


class PublicSupportContractTests(unittest.TestCase):
    def test_required_public_support_files_exist(self) -> None:
        for path in (
            POLICY,
            BUG_FORM,
            FEATURE_FORM,
            ISSUE_CONFIG,
            PULL_REQUEST_TEMPLATE,
        ):
            with self.subTest(path=path):
                self.assertTrue(path.is_file(), f"missing public support file: {path}")

    def test_support_policy_preserves_preview_export_share_boundaries(self) -> None:
        text = POLICY.read_text(encoding="utf-8")
        for heading in (
            "Public issue or private security report",
            "Never share",
            "Safe diagnostic workflow",
            "Public mutation safety contract",
            "Maintainer response boundary",
        ):
            self.assertRegex(text, rf"(?m)^## {re.escape(heading)}$")
        for required in (
            "./bin/macomrade diagnostics bundle",
            "./bin/macomrade apply diagnostic-bundle",
            'EXPORT REDACTED DIAGNOSTICS',
            "sharing_authorized",
            "separate explicit",
            "SECURITY.md",
            "Private/",
            "raw TCC",
        ):
            self.assertIn(required, text)
        for forbidden in ("gh issue create", "curl -F", "automatically upload"):
            self.assertNotIn(forbidden, text)

    def test_issue_forms_require_redaction_acknowledgement(self) -> None:
        bug = BUG_FORM.read_text(encoding="utf-8")
        feature = FEATURE_FORM.read_text(encoding="utf-8")
        config = ISSUE_CONFIG.read_text(encoding="utf-8")
        self.assertIn("blank_issues_enabled: false", config)
        for required in (
            "SECURITY.md",
            "Private/",
            "credentials",
            "redacted",
            "validations:\n        required: true",
        ):
            self.assertIn(required, bug)
        self.assertIn("no secrets or private machine state", feature)
        pull_request = PULL_REQUEST_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("No secrets, Private files, or machine-local state", pull_request)
        self.assertIn("python3 scripts/release_check.py", pull_request)

    def test_public_entry_points_link_to_support_contract(self) -> None:
        for path in (ROOT / "README.md", ROOT / "CONTRIBUTING.md", ROOT / "SECURITY.md"):
            with self.subTest(path=path):
                self.assertIn(
                    "references/public-support-safety.md",
                    path.read_text(encoding="utf-8"),
                )


if __name__ == "__main__":
    unittest.main()
