#!/usr/bin/env python3
"""Hermetic tests for mutation transaction contracts."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import transaction_contract  # noqa: E402
import validate_mutation_contracts  # noqa: E402


class MutationContractTests(unittest.TestCase):
    def test_repository_registry_covers_all_mutations(self) -> None:
        result = validate_mutation_contracts.validate(ROOT)
        self.assertEqual(result["status"], "passed", result["errors"])
        self.assertEqual(result["action_count"], 43)

    def test_transaction_metadata_has_stable_contract_hash(self) -> None:
        first = transaction_contract.transaction_metadata(
            "apps.install",
            phase="plan",
            status="planned",
            targets=["Fixture Brew"],
        )
        second = transaction_contract.transaction_metadata(
            "apps.install",
            phase="verify",
            status="passed",
            targets=["Fixture Brew"],
        )
        self.assertEqual(first["action_id"], "apps.install")
        self.assertEqual(first["contract_sha256"], second["contract_sha256"])
        self.assertNotEqual(first["recorded_at"], "")

    def test_invalid_phase_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid transaction phase"):
            transaction_contract.transaction_metadata(
                "apps.install",
                phase="pretend",
                status="unknown",
                targets=[],
            )

    def test_exact_confirmation_is_enforced(self) -> None:
        with self.assertRaisesRegex(ValueError, "must be exactly"):
            transaction_contract.require_confirmation(
                "state.cleanup",
                "wrong",
            )
        transaction_contract.require_confirmation(
            "state.cleanup",
            "REMOVE VERIFIED LEGACY STATE",
        )

    def test_every_high_risk_contract_uses_exact_confirmation(self) -> None:
        registry = transaction_contract.load_registry()
        for action in registry["actions"]:
            if action["risk"] not in {"high", "destructive"}:
                continue
            with self.subTest(action=action["id"]):
                self.assertIn(
                    action["confirmation"]["mode"],
                    {"exact", "interactive_exact"},
                )
                self.assertTrue(action["confirmation"]["value"])

    def test_wrong_capacities_confirmation_stops_before_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/capacities_cleanup.py"),
                    "--state-dir",
                    tmp,
                    "--apply",
                    "--confirm",
                    "wrong",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("REMOVE CAPACITIES APP", completed.stderr)

    def test_wrong_skill_uninstall_confirmation_stops_before_mutation(self) -> None:
        completed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/skill_uninstall.py"),
                "--apply",
                "--confirm",
                "wrong",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("UNINSTALL SKILL RUNTIME", completed.stderr)


if __name__ == "__main__":
    unittest.main()
