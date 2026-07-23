#!/usr/bin/env python3
"""Hermetic compatibility tests for the tracked Chrome profile registry."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import chrome_profiles  # noqa: E402


class ChromeProfileConfigurationTests(unittest.TestCase):
    def test_legacy_locator_and_private_path_have_identical_policy(self) -> None:
        inventory = {
            "profiles": [
                {
                    "profile_directory": "Default",
                    "display_name": "Example Profile 12",
                    "account_email": "profile@example.com",
                }
            ]
        }
        legacy = chrome_profiles.compare(
            inventory,
            ROOT / "config" / "chrome-profiles.json",
        )
        private = chrome_profiles.compare(
            inventory,
            ROOT / "Private" / "chrome-profiles.json",
        )

        self.assertIsNotNone(legacy.pop("expected_locator"))
        self.assertIsNone(private.pop("expected_locator"))
        legacy.pop("expected")
        private.pop("expected")
        self.assertEqual(legacy, private)


if __name__ == "__main__":
    unittest.main()
