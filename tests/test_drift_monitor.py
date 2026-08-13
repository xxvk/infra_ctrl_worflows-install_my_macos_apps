#!/usr/bin/env python3
"""Hermetic contracts for the low-noise, read-only drift monitor."""

from __future__ import annotations

import datetime as dt
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import drift_monitor  # noqa: E402


def drift_report() -> dict:
    return {
        "app_drift": {
            "missing_core": ["Fixture Core"],
            "source_mismatches": [{"app": "Fixture Source", "source": {"expected": "homebrew", "detected": "manual"}}],
        },
        "preference_drift": {"status": "mismatch", "mismatches": [{"key": "fixture.preference"}]},
        "step_returncodes": {"preferences": 1},
    }


class DriftMonitorTests(unittest.TestCase):
    def test_policy_is_valid_and_has_battery_and_cooldown_guards(self) -> None:
        result = drift_monitor.validate()
        self.assertEqual(result["status"], "passed", result["errors"])
        self.assertGreaterEqual(result["policy"]["min_battery_percent"], 1)

    def test_finding_extraction_is_safe_and_stable(self) -> None:
        findings = drift_monitor.extract_findings(drift_report())
        ids = [item["id"] for item in findings]
        self.assertIn("missing-core:Fixture Core", ids)
        self.assertIn("source-mismatch:Fixture Source", ids)
        self.assertNotIn("path", str(findings))

    def test_unchanged_finding_is_suppressed_within_cooldown(self) -> None:
        finding = drift_monitor.extract_findings(drift_report())[0]
        now = dt.datetime(2026, 8, 14, tzinfo=dt.timezone.utc)
        previous = {"findings": [{**finding, "first_seen_at": "2026-08-13T00:00:00+00:00", "last_notified_at": "2026-08-13T23:00:00+00:00"}]}
        result = drift_monitor.deduplicate(
            [finding], previous, {"low": 168, "medium": 72, "high": 24}, now=now
        )
        self.assertEqual(result["new_or_due"], [])
        self.assertEqual(result["suppressed_count"], 1)

    def test_low_battery_defers_without_running_audit(self) -> None:
        self.assertTrue(drift_monitor.should_defer_for_power({"available": True, "percentage": 15, "charging": False}, 20))
        self.assertFalse(drift_monitor.should_defer_for_power({"available": True, "percentage": 15, "charging": True}, 20))


if __name__ == "__main__":
    unittest.main()
