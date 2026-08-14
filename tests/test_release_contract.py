#!/usr/bin/env python3
"""Hermetic tests for the release-candidate contract validator."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_release_contract import validate_contract  # noqa: E402


class ReleaseContractTests(unittest.TestCase):
    def _fixture(self, root: Path) -> Path:
        (root / "references").mkdir()
        (root / "VERSION").write_text("0.2.0\n", encoding="utf-8")
        (root / "evidence.txt").write_text("fixture\n", encoding="utf-8")
        (root / "references" / "release-roadmap.md").write_text(
            "## 0.1.0 — historical\n\nStatus: **release_candidate**\n\n"
            "## 0.2.0 — fixture\n\nStatus: **release_candidate**\n",
            encoding="utf-8",
        )
        matrix = root / "references" / "release-acceptance-matrix.json"
        matrix.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "version": "0.2.0",
                    "release_status": "release_candidate",
                    "classifications": {
                        "supported": "implemented",
                        "interface_limited": "limited",
                        "deferred": "later",
                        "excluded": "never",
                    },
                    "items": [
                        {
                            "id": "SUP-01",
                            "classification": "supported",
                            "capability": "fixture",
                            "evidence": ["evidence.txt"],
                        },
                        {
                            "id": "LIM-01",
                            "classification": "interface_limited",
                            "capability": "fixture",
                        },
                        {
                            "id": "DEF-01",
                            "classification": "deferred",
                            "capability": "fixture",
                        },
                        {
                            "id": "EXC-01",
                            "classification": "excluded",
                            "capability": "fixture",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        return matrix

    def test_valid_contract_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matrix = self._fixture(root)
            result = validate_contract(root, matrix)
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["supported_items"], 1)

    def test_supported_capability_requires_existing_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matrix = self._fixture(root)
            data = json.loads(matrix.read_text())
            data["items"][0]["evidence"] = ["missing.txt"]
            matrix.write_text(json.dumps(data), encoding="utf-8")
            result = validate_contract(root, matrix)
            self.assertEqual(result["status"], "failed")
            self.assertTrue(any("evidence not found" in error for error in result["errors"]))

    def test_version_matrix_and_current_roadmap_status_must_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matrix = self._fixture(root)
            (root / "VERSION").write_text("0.2.1\n", encoding="utf-8")
            (root / "references" / "release-roadmap.md").write_text(
                "## 0.2.1 — fixture\n\nStatus: **shipped**\n",
                encoding="utf-8",
            )
            result = validate_contract(root, matrix)
            self.assertEqual(result["status"], "failed")
            self.assertTrue(any("matrix version must match VERSION" in error for error in result["errors"]))
            self.assertTrue(any("matrix release_status must match" in error for error in result["errors"]))

    def test_version_must_be_semver(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            matrix = self._fixture(root)
            (root / "VERSION").write_text("next\n", encoding="utf-8")
            result = validate_contract(root, matrix)
            self.assertEqual(result["status"], "failed")
            self.assertTrue(any("Semantic Version" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
