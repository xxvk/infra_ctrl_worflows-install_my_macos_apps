from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ONBOARDING = ROOT / "references" / "public-onboarding.md"
README = ROOT / "README.md"


class PublicOnboardingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(ONBOARDING.is_file(), "public onboarding guide is missing")
        self.text = ONBOARDING.read_text(encoding="utf-8")

    def section(self, heading: str) -> str:
        match = re.search(
            rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)",
            self.text,
            flags=re.MULTILINE | re.DOTALL,
        )
        self.assertIsNotNone(match, f"missing onboarding section: {heading}")
        return match.group(1)

    def test_required_public_sections_exist(self) -> None:
        for heading in (
            "Audience and support scope",
            "Platform support matrix",
            "Prerequisites",
            "Ten-minute read-only quick start",
            "Private overlay setup",
            "Permissions and secrets",
            "Known limitations",
            "Uninstall and rollback",
            "Troubleshooting",
        ):
            with self.subTest(heading=heading):
                self.section(heading)

    def test_quick_start_is_non_mutating_and_uses_temporary_state(self) -> None:
        quick_start = self.section("Ten-minute read-only quick start")
        for required in (
            "MACOMRADE_PUBLIC_ONLY",
            "MACOMRADE_STATE_DIR",
            "./bin/macomrade validate",
            "./bin/macomrade verify schemas",
            "./bin/macomrade scan apps",
            "./bin/macomrade plan apps --profile auto",
        ):
            self.assertIn(required, quick_start)
        for forbidden in ("--apply", "sudo ", "brew install", "mas install"):
            self.assertNotIn(forbidden, quick_start)

    def test_readme_links_to_onboarding_without_tracked_private_links(self) -> None:
        readme = README.read_text(encoding="utf-8")
        self.assertIn("references/public-onboarding.md", readme)
        self.assertNotRegex(readme, r"\]\(Private/")


if __name__ == "__main__":
    unittest.main()
