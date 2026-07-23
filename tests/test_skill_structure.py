#!/usr/bin/env python3
"""Tests for the progressive-disclosure Skill structure."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import validate_skill_structure as validator  # noqa: E402


class SkillStructureTests(unittest.TestCase):
    def test_repository_structure_passes(self) -> None:
        result = validator.validate_skill_structure(ROOT)
        self.assertEqual(result["status"], "passed", result["errors"])
        self.assertLessEqual(result["skill_lines"], validator.MAX_SKILL_LINES)
        self.assertEqual(
            set(result["domain_references"]),
            set(validator.DOMAIN_REFERENCES),
        )

    def test_missing_domain_reference_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            links = "\n".join(
                f"[domain]({relative})"
                for relative in validator.DOMAIN_REFERENCES
            )
            headings = "\n".join(validator.CORE_HEADINGS)
            (root / "SKILL.md").write_text(
                f"---\nname: fixture\ndescription: fixture\n---\n{headings}\n{links}\n",
                encoding="utf-8",
            )
            result = validator.validate_skill_structure(root)
            self.assertEqual(result["status"], "failed")
            self.assertTrue(
                any("domain reference not found" in error for error in result["errors"])
            )


if __name__ == "__main__":
    unittest.main()
