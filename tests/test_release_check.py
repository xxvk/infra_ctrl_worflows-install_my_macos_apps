#!/usr/bin/env python3
"""Contract tests for the unified local release-check entry point."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import release_check  # noqa: E402


class ReleaseCheckTests(unittest.TestCase):
    def test_default_suite_is_hermetic_and_excludes_live_smoke(self) -> None:
        checks = release_check.build_checks(
            include_live_smoke=False,
            python="/fixture/python",
        )
        ids = [check_id for check_id, _ in checks]
        self.assertIn("hermetic-tests", ids)
        self.assertIn("unified-cli", ids)
        self.assertIn("schema-contract", ids)
        self.assertIn("machine-roles", ids)
        self.assertIn("localization", ids)
        self.assertIn("app-adapters", ids)
        self.assertIn("performance-budgets", ids)
        self.assertIn("drift-monitor", ids)
        self.assertIn("publication-audit-policy", ids)
        self.assertIn("diagnostic-bundle", ids)
        self.assertNotIn("live-macos-smoke", ids)

    def test_live_smoke_requires_explicit_flag(self) -> None:
        checks = release_check.build_checks(
            include_live_smoke=True,
            python="/fixture/python",
        )
        self.assertEqual(checks[-1], ("live-macos-smoke", ["/bin/bash", "tests/smoke.sh"]))

    def test_failure_stops_later_checks_and_preserves_diagnostics(self) -> None:
        runner = mock.Mock(
            side_effect=[
                subprocess.CompletedProcess([], 0, stdout="ok", stderr=""),
                subprocess.CompletedProcess([], 7, stdout="partial", stderr="failure"),
            ]
        )
        result = release_check.run_checks(
            [
                ("first", ["first"]),
                ("second", ["second"]),
                ("must-not-run", ["third"]),
            ],
            root=ROOT,
            runner=runner,
        )
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["schema_version"], 1)
        self.assertEqual(result["checks_run"], 2)
        self.assertEqual(result["results"][-1]["stderr"], "failure")
        self.assertEqual(runner.call_count, 2)


if __name__ == "__main__":
    unittest.main()
