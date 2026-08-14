#!/usr/bin/env python3
"""Hermetic contracts for repeatable local performance benchmarking."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import performance_benchmark  # noqa: E402


class PerformanceBenchmarkTests(unittest.TestCase):
    def test_policy_is_valid_and_covers_required_operations(self) -> None:
        result = performance_benchmark.validate()
        self.assertEqual(result["status"], "passed", result["errors"])
        self.assertEqual(
            result["operations"],
            ["drift", "inventory", "migration", "plan", "storage_plan", "storage_scan", "validate"],
        )

    def test_suite_records_cold_warm_time_output_state_and_peak_memory(self) -> None:
        clock = iter([0.0, 0.25, 1.0, 1.5])

        def runner(command, **_kwargs):
            return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

        with tempfile.TemporaryDirectory() as tmp:
            result = performance_benchmark.run_suite(
                ["inventory"],
                iterations=2,
                state_dir=Path(tmp),
                runner=runner,
                clock=lambda: next(clock),
                peak_reader=lambda _pid: 4096,
            )
        samples = result["operations"]["inventory"]["samples"]
        self.assertEqual([sample["mode"] for sample in samples], ["cold", "warm"])
        self.assertEqual(samples[0]["elapsed_ms"], 250)
        self.assertEqual(samples[1]["output_bytes"], 2)
        self.assertEqual(samples[1]["peak_rss_bytes"], 4096)

    def test_comparison_uses_absolute_and_regression_budgets(self) -> None:
        policy = {
            "operations": {
                "inventory": {
                    "cold_max_ms": 500,
                    "warm_max_ms": 400,
                    "peak_rss_max_bytes": 5000,
                    "output_max_bytes": 100,
                    "state_growth_max_bytes": 100,
                }
            },
            "regression": {"max_percent": 25, "min_absolute_delta_ms": 20},
        }
        current = {"operations": {"inventory": {"summary": {"cold_elapsed_ms": 650, "warm_elapsed_ms": 450, "peak_rss_bytes": 6000, "output_bytes": 120, "state_growth_bytes": 120}}}}
        baseline = {"operations": {"inventory": {"summary": {"cold_elapsed_ms": 400, "warm_elapsed_ms": 300}}}}
        result = performance_benchmark.compare_budgets(current, policy, baseline)
        self.assertEqual(result["status"], "review_required")
        self.assertTrue(result["violations"])
        self.assertTrue(any(item["metric"] == "cold_elapsed_ms" for item in result["violations"]))

    def test_failed_sample_is_always_review_required(self) -> None:
        current = {"operations": {"inventory": {"samples": [{"returncode": 2}], "summary": {"cold_elapsed_ms": 1, "warm_elapsed_ms": 1, "peak_rss_bytes": 1, "output_bytes": 1, "state_growth_bytes": 0}}}}
        policy = {"operations": {"inventory": {"cold_max_ms": 2, "warm_max_ms": 2, "peak_rss_max_bytes": 2, "output_max_bytes": 2, "state_growth_max_bytes": 2}}, "regression": {"max_percent": 25, "min_absolute_delta_ms": 20}}
        result = performance_benchmark.compare_budgets(current, policy, None)
        self.assertTrue(any(item["reason"] == "command_failed" for item in result["violations"]))

    def test_drift_mismatch_exit_is_a_valid_measurement_outcome(self) -> None:
        current = {"operations": {"drift": {"samples": [{"returncode": 1}], "summary": {"cold_elapsed_ms": 1, "warm_elapsed_ms": 1, "peak_rss_bytes": 1, "output_bytes": 1, "state_growth_bytes": 0}}}}
        policy = {"operations": {"drift": {"cold_max_ms": 2, "warm_max_ms": 2, "peak_rss_max_bytes": 2, "output_max_bytes": 2, "state_growth_max_bytes": 2}}, "regression": {"max_percent": 25, "min_absolute_delta_ms": 20}}
        result = performance_benchmark.compare_budgets(current, policy, None)
        self.assertFalse(any(item["reason"] == "command_failed" for item in result["violations"]))


if __name__ == "__main__":
    unittest.main()
