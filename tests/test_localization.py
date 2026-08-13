#!/usr/bin/env python3
"""Hermetic locale and accessibility catalog contracts."""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import localization  # noqa: E402


class LocalizationTests(unittest.TestCase):
    def test_repository_catalogs_have_complete_translations(self) -> None:
        result = localization.validate()
        self.assertEqual(result["status"], "passed", result["errors"])
        self.assertEqual(result["locales"], ["en", "ja", "zh-Hans"])

    def test_missing_key_and_placeholder_drift_are_rejected(self) -> None:
        catalogs = localization.load_catalogs()
        missing = copy.deepcopy(catalogs)
        del missing["ja"]["messages"]["role.base.description"]
        with self.assertRaisesRegex(localization.LocalizationError, "message keys differ"):
            localization.validate_catalogs(missing)

        drift = copy.deepcopy(catalogs)
        drift["zh-Hans"]["messages"]["adapter.inspect.summary"] = "已检查 {different}"
        with self.assertRaisesRegex(localization.LocalizationError, "placeholder set differs"):
            localization.validate_catalogs(drift)

    def test_message_lookup_uses_declared_locale_and_parameters(self) -> None:
        self.assertIn(
            "developer",
            localization.message("role.selected", "en", roles="developer"),
        )
        self.assertIn(
            "developer",
            localization.message("role.selected", "ja", roles="developer"),
        )


if __name__ == "__main__":
    unittest.main()
