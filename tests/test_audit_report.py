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


def sample_browser_plan() -> dict:
    return {
        "schema_version": 1,
        "kind": "browser_transaction_redacted_summary",
        "status": "preview",
        "operation_count": 2,
        "operation_counts": {"delete": 1, "move": 1},
        "backup_verified": True,
        "exact_rollback_supported": False,
        "apply_interface": "unavailable",
        "private_content_emitted": False,
        "writes_performed": False,
        "execution_authorized": False,
        "url": "https://private.example.invalid",
        "path": "/Users/private/Safari Export.zip",
        "item_id": "bri_private",
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

    def test_browser_summary_accepts_only_allowlisted_aggregate_fields(self) -> None:
        summary = audit_report.summarize(sample_browser_plan())
        self.assertEqual(summary["kind"], "browser_audit_report_summary")
        self.assertEqual(summary["stage"], "plan")
        self.assertEqual(summary["metrics"]["operation_count"], 2)
        self.assertEqual(summary["metrics"]["backup_verified"], True)
        self.assertEqual(summary["metrics"]["apply_interface"], "unavailable")
        serialized = str(summary)
        self.assertNotIn("private.example.invalid", serialized)
        self.assertNotIn("/Users/private", serialized)
        self.assertNotIn("bri_private", serialized)

    def test_browser_summary_maps_all_six_workflow_stages(self) -> None:
        cases = {
            "safari_export_redacted_summary": "scan",
            "browser_lifecycle_redacted_summary": "review",
            "browser_transaction_redacted_summary": "plan",
            "browser_transaction_apply_summary": "apply",
            "browser_transaction_verification_summary": "verify",
            "browser_history_redacted_summary": "history",
            "browser_live_acceptance_summary": "verify",
        }
        for kind, stage in cases.items():
            with self.subTest(kind=kind):
                source = {
                    "schema_version": 1,
                    "kind": kind,
                    "status": "passed",
                    "execution_authorized": False,
                    "private_content_emitted": False,
                }
                if kind == "safari_export_redacted_summary":
                    source.pop("private_content_emitted")
                    source["item_content_emitted"] = False
                    source["input_path_emitted"] = False
                    source["artifact_ref_emitted"] = False
                summary = audit_report.summarize(source)
                self.assertEqual(summary["stage"], stage)

    def test_live_acceptance_summary_renders_partial_gate_counts_only(self) -> None:
        source = {
            "schema_version": 1,
            "kind": "browser_live_acceptance_summary",
            "status": "partial",
            "counts": {
                "bookmark_count": 4,
                "reading_list_count": 1,
                "queued_count": 3,
                "suppressed_count": 2,
                "planned_operation_count": 1,
                "verified_operation_count": 0,
                "failed_operation_count": 1,
            },
            "private_content_emitted": False,
            "execution_authorized": False,
            "gates": [{"id": "BA-01", "reason": "private-value"}],
        }
        summary = audit_report.summarize(source)
        self.assertEqual(summary["source_status"], "partial")
        self.assertEqual(summary["metrics"]["bookmark_count"], 4)
        self.assertEqual(summary["metrics"]["planned_operation_count"], 1)
        self.assertNotIn("gates", summary)
        self.assertNotIn("private-value", str(summary))
        text = audit_report.render_tui(summary, "zh-Hans")
        self.assertIn("部分完成", text)
        self.assertIn("计划操作", text)

    def test_browser_tui_and_html_are_localized_semantic_and_private(self) -> None:
        summary = audit_report.summarize(sample_browser_plan())
        text = audit_report.render_tui(summary, "zh-Hans")
        self.assertIn("浏览器审计报告", text)
        self.assertIn("计划", text)
        self.assertIn("操作数量", text)
        self.assertNotIn("private.example.invalid", text)
        self.assertNotIn("\x1b[", text)

        rendered = audit_report.render_html(summary, "ja")
        self.assertIn('<main id="browser-audit-report">', rendered)
        self.assertIn('<th scope="row">', rendered)
        self.assertIn('aria-label="Status:', rendered)
        self.assertNotIn("private.example.invalid", rendered)
        self.assertNotIn("<script", rendered.lower())

    def test_browser_report_rejects_raw_or_private_browser_documents(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported browser report kind"):
            audit_report.summarize(
                {
                    "schema_version": 1,
                    "kind": "safari_export_private_parse",
                    "items": [{"url": "https://private.example.invalid"}],
                }
            )
        private_summary = sample_browser_plan()
        private_summary["private_content_emitted"] = True
        with self.assertRaisesRegex(ValueError, "not explicitly redacted"):
            audit_report.summarize(private_summary)

        scan_summary = {
            "schema_version": 1,
            "kind": "safari_export_redacted_summary",
            "status": "passed",
            "item_content_emitted": False,
            "input_path_emitted": True,
            "artifact_ref_emitted": False,
            "execution_authorized": False,
        }
        with self.assertRaisesRegex(ValueError, "not explicitly redacted"):
            audit_report.summarize(scan_summary)

        wrong_version = sample_browser_plan()
        wrong_version["schema_version"] = 2
        with self.assertRaisesRegex(ValueError, "schema_version"):
            audit_report.summarize(wrong_version)


if __name__ == "__main__":
    unittest.main()
