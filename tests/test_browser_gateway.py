#!/usr/bin/env python3
"""TDD contracts for the BR-10 personal knowledge gateway."""

from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import browser_gateway  # noqa: E402


class BrowserGatewayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = json.loads(
            (ROOT / "settings" / "browser-gateway-policy.json").read_text(encoding="utf-8")
        )

    def _organization(self) -> dict:
        organization = json.loads(
            (ROOT / "tests/fixtures/schema_contract/browser-organization-v1.json").read_text(
                encoding="utf-8"
            )
        )
        decisions = []
        for index, code in enumerate(["11", "11", "11", "21"], start=1):
            decisions.append(
                {
                    "item_id": f"bri_fixture_gateway_{index:04d}",
                    "item_fingerprint": f"{index:064x}",
                    "item_type": "bookmark",
                    "original_title": "PRIVATE TITLE MUST NOT LEAK",
                    "suggested_title": None,
                    "title_suggestion_rule_ids": [],
                    "original_url": f"https://private.invalid/{index}",
                    "source_collection": ["Bookmarks", "Private"],
                    "assignment_basis": "item_override",
                    "rule_id": None,
                    "duplicate_group_id": None,
                    "disposition": "move",
                    "target_collection": ["Favorites", "01 | Fictional", f"{code} | Fictional"],
                    "note": None,
                    "execution_authorized": False,
                }
            )
        organization["decisions"] = decisions
        organization["source"].update(bookmark_count=4, item_count=4)
        organization["summary"].update(
            active_move_count=4,
            bookmark_operation_count=4,
            item_count=4,
        )
        return organization

    def test_default_policy_targets_100_with_70_core_and_30_trial_slots(self) -> None:
        self.assertEqual(browser_gateway.policy_errors(self.policy), [])
        self.assertEqual(sum(row["core_slots"] for row in self.policy["subdomains"]), 70)
        self.assertEqual(sum(row["trial_slots"] for row in self.policy["subdomains"]), 30)
        self.assertEqual(sum(row["total_slots"] for row in self.policy["subdomains"]), 100)
        self.assertEqual(sum(1 for row in self.policy["subdomains"] if row["priority"]), 5)
        self.assertEqual(self.policy["renewal"]["above_target_retirements_per_new"], 2)

    def test_policy_rejects_duplicate_codes_and_broken_capacity_sums(self) -> None:
        invalid = copy.deepcopy(self.policy)
        invalid["subdomains"][1]["code"] = "11"
        invalid["capacity"]["trial_slots"] = 31
        errors = browser_gateway.policy_errors(invalid)
        self.assertTrue(any("unique" in error for error in errors))
        self.assertTrue(any("core_slots plus trial_slots" in error for error in errors))

    def test_audit_is_aggregate_only_and_counts_domain_pressure(self) -> None:
        result = browser_gateway.audit_organization(self._organization(), self.policy)
        rows = {row["code"]: row for row in result["subdomains"]}
        self.assertEqual(result["current_active_bookmarks"], 4)
        self.assertEqual(rows["11"]["current_active"], 3)
        self.assertEqual(rows["21"]["current_active"], 1)
        self.assertFalse(result["private_content_emitted"])
        rendered = json.dumps(result)
        self.assertNotIn("PRIVATE TITLE", rendered)
        self.assertNotIn("private.invalid", rendered)
        self.assertNotIn("source_collection", rendered)

    def test_cli_validation_and_audit_never_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            organization_path = Path(tmp) / "organization.json"
            organization_path.write_text(json.dumps(self._organization()), encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                returncode = browser_gateway.main(["audit-organization", str(organization_path)])
            self.assertEqual(returncode, 0)
            result = json.loads(stdout.getvalue())
            self.assertFalse(result["writes"])
            self.assertFalse(result["execution_authorized"])

    def test_wave_compiler_binds_private_retirement_without_leaking_summary(self) -> None:
        organization = self._organization()
        source = organization["decisions"][0]
        spec = {
            "wave_id": "bgw_fixture_compile_01",
            "created_at": "2026-08-15",
            "proposals": [
                {
                    "proposal_id": "bgp_fixture_compile_01",
                    "subdomain_code": "42",
                    "new_source": {
                        "title": "Fictional market data",
                        "url": "https://market-data.invalid/updates",
                        "operator": "Fictional operator",
                        "source_type": "data_tool",
                        "evidence_url": "https://market-data.invalid/evidence",
                        "evidence_checked_on": "2026-08-15",
                    },
                    "retirements": [
                        {"item_id": source["item_id"], "decision": "archive"}
                    ],
                }
            ],
        }
        wave = browser_gateway.build_wave(organization, spec, self.policy)
        self.assertEqual(wave["summary"]["new_source_count"], 1)
        self.assertEqual(wave["summary"]["retirement_count"], 1)
        self.assertFalse(wave["execution_authorized"])
        summary = browser_gateway._wave_summary(wave, status="preview", writes=False)
        rendered = json.dumps(summary)
        self.assertNotIn("PRIVATE TITLE", rendered)
        self.assertNotIn("private.invalid", rendered)
        self.assertNotIn(source["item_id"], rendered)
        plan = browser_gateway.plan_wave(wave)
        self.assertEqual(plan["status"], "blocked")
        self.assertEqual(plan["reason"], "supported_item_write_interface_unavailable")
        self.assertFalse(plan["browser_writes_performed"])

    def test_wave_requires_two_retirements_when_active_count_exceeds_100(self) -> None:
        organization = self._organization()
        template = organization["decisions"][0]
        for index in range(5, 102):
            row = copy.deepcopy(template)
            row["item_id"] = f"bri_fixture_gateway_{index:04d}"
            row["item_fingerprint"] = f"{index:064x}"
            row["original_url"] = f"https://private-{index}.invalid/source"
            organization["decisions"].append(row)
        organization["source"].update(bookmark_count=101, item_count=101)
        organization["summary"].update(
            active_move_count=101,
            bookmark_operation_count=101,
            item_count=101,
        )
        source = organization["decisions"][0]
        spec = {
            "wave_id": "bgw_fixture_ratio_01",
            "created_at": "2026-08-15",
            "proposals": [
                {
                    "proposal_id": "bgp_fixture_ratio_01",
                    "subdomain_code": "42",
                    "new_source": {
                        "title": "Fictional market data",
                        "url": "https://market-ratio.invalid/updates",
                        "operator": "Fictional operator",
                        "source_type": "data_tool",
                        "evidence_url": "https://market-ratio.invalid/evidence",
                        "evidence_checked_on": "2026-08-15",
                    },
                    "retirements": [
                        {"item_id": source["item_id"], "decision": "archive"}
                    ],
                }
            ],
        }
        with self.assertRaisesRegex(browser_gateway.BrowserGatewayError, "retirement ratio"):
            browser_gateway.build_wave(organization, spec, self.policy)
        organization["decisions"].pop()
        organization["source"].update(bookmark_count=100, item_count=100)
        organization["summary"].update(
            active_move_count=100,
            bookmark_operation_count=100,
            item_count=100,
        )
        wave = browser_gateway.build_wave(organization, spec, self.policy)
        self.assertEqual(wave["summary"]["minimum_retirements_per_new"], 1)


if __name__ == "__main__":
    unittest.main()
