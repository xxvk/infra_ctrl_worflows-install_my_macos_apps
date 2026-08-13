#!/usr/bin/env python3
"""Hermetic accessibility and privacy contracts for audit reports."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_report  # noqa: E402


def sample_report() -> dict:
    return {
        "mode": "read_only_final_drift_check",
        "captured_at": "2026-08-14T00:00:00+00:00",
        "app_drift": {
            "missing_count": 1,
            "missing_core": ["Fixture Core"],
            "source_mismatches": [{"app": "Fixture App", "path": "/Users/example/Applications/Fixture.app"}],
        },
        "permission_drift": {"verified": 2, "blocked": 1},
        "preference_drift": {"status": "mismatch", "mismatches": [{"key": "fixture"}]},
        "step_returncodes": {"app_scan": 0, "app_plan": 0, "permissions": 0, "preferences": 1},
    }


class AuditReportTests(unittest.TestCase):
    def test_summary_is_path_safe_and_machine_readable(self) -> None:
        summary = audit_report.summarize(sample_report())
        self.assertEqual(summary["overall_status"], "review_required")
        self.assertEqual(summary["missing_core"], ["Fixture Core"])
        self.assertNotIn("/Users/example", str(summary))

    def test_html_is_semantic_and_not_color_only(self) -> None:
        html = audit_report.render_html(audit_report.summarize(sample_report()), "en")
        self.assertIn('<main id="audit-report">', html)
        self.assertIn('<th scope="col">', html)
        self.assertIn('aria-label="Status: review required"', html)
        self.assertNotIn("/Users/example", html)
        self.assertNotIn("<script", html.lower())

    def test_tui_uses_localized_textual_status(self) -> None:
        text = audit_report.render_tui(audit_report.summarize(sample_report()), "ja")
        self.assertIn("監査", text)
        self.assertIn("要確認", text)
        self.assertNotIn("\x1b[", text)


if __name__ == "__main__":
    unittest.main()
