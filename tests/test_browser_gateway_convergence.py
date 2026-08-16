#!/usr/bin/env python3
"""Hermetic contracts for the 100-source Safari gateway convergence."""

from __future__ import annotations

import copy
import json
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import browser_gateway_convergence as convergence  # noqa: E402
import browser_gateway_order  # noqa: E402
import browser_gateway_pilot  # noqa: E402


class BrowserGatewayConvergenceTests(unittest.TestCase):
    def inputs(self) -> tuple[dict, dict, dict, dict]:
        policy = json.loads((ROOT / "settings/browser-gateway-policy.json").read_text())
        organization = json.loads(
            (ROOT / "tests/fixtures/schema_contract/browser-organization-v1.json").read_text()
        )
        top_specs = [
            ("01", "Work", "W", ["11", "12", "13"]),
            ("02", "Content", "C", ["21", "22", "23"]),
            ("03", "Research", "R", ["31", "32", "33"]),
            ("04", "Finance", "F", ["41", "42", "43"]),
            ("05", "Life", "L", ["51", "52", "53"]),
        ]
        organization["taxonomy"]["top_levels"] = [
            {
                "code": top_code,
                "label": label,
                "emoji": emoji,
                "folder_name": f"{top_code}｜Fixture {label} {emoji}",
                "role": "active",
                "children": [
                    {
                        "code": code,
                        "label": f"Fixture {code}",
                        "emoji": emoji,
                        "folder_name": f"{code}｜Fixture {code} {emoji}",
                    }
                    for code in codes
                ],
            }
            for top_code, label, emoji, codes in top_specs
        ] + [
            {
                "code": "99",
                "label": "Archive",
                "emoji": "A",
                "folder_name": "99｜Fixture Archive A",
                "role": "archive",
                "children": [
                    {
                        "code": f"9{index}",
                        "label": f"Fixture archive {index}",
                        "emoji": "A",
                        "folder_name": f"9{index}｜Fixture archive {index} A",
                    }
                    for index in range(1, 6)
                ],
            }
        ]
        taxonomy: dict[str, list[str]] = {}
        for top in organization["taxonomy"]["top_levels"]:
            if top["role"] == "active":
                for child in top["children"]:
                    taxonomy[child["code"]] = ["Favorites", top["folder_name"], child["folder_name"]]

        pilot_codes = ["31", "13", "13", "31", "42", "42", "11", "22", "22", "11"]
        pilot_additions = Counter(pilot_codes)
        decisions = []
        legacy_urls: dict[str, list[str]] = {code: [] for code in convergence.EXPECTED_CODES}
        ordinal = 1
        for quota in policy["subdomains"]:
            keep_count = quota["total_slots"] - pilot_additions[quota["code"]]
            for _ in range(keep_count):
                url = f"https://legacy-{ordinal}.invalid/source"
                legacy_urls[quota["code"]].append(url)
                decisions.append(self._decision(ordinal, quota["code"], url, taxonomy[quota["code"]]))
                ordinal += 1
        retirement_rows = []
        for _ in range(20):
            url = f"https://retire-{ordinal}.invalid/source"
            row = self._decision(ordinal, "12", url, taxonomy["12"])
            decisions.append(row)
            retirement_rows.append(row)
            ordinal += 1
        for index in range(1, 90):
            decisions.append(
                {
                    "item_id": f"bri_fixture_reading_{index:04d}",
                    "item_fingerprint": f"{5000 + index:064x}",
                    "item_type": "reading_list",
                    "original_title": f"Fixture reading {index}",
                    "suggested_title": None,
                    "title_suggestion_rule_ids": [],
                    "original_url": f"https://reading-{index}.invalid/source",
                    "source_collection": ["Reading List"],
                    "assignment_basis": "reading_list_policy",
                    "rule_id": None,
                    "duplicate_group_id": None,
                    "disposition": "defer",
                    "target_collection": None,
                    "note": None,
                    "execution_authorized": False,
                }
            )
        organization["organization_id"] = "borg_fixture_convergence_01"
        organization["created_at"] = "2026-08-15"
        organization["source"].update(
            artifact_sha256="a" * 64,
            bookmark_count=110,
            reading_list_count=89,
            item_count=199,
        )
        organization["decisions"] = decisions
        organization["summary"].update(
            directory_rule_item_count=0,
            ambiguous_item_count=0,
            duplicate_group_count=0,
            active_move_count=110,
            archive_count=0,
            bookmark_delete_count=0,
            reading_list_delete_later_count=0,
            reading_list_deferred_count=89,
            bookmark_operation_count=110,
            item_count=199,
        )
        organization["item_overrides"] = []
        organization["duplicate_resolutions"] = []

        proposals = []
        pilot_groups = []
        required_directories = [browser_gateway_pilot.TEMPORARY_COLLECTION]
        for index, code in enumerate(pilot_codes):
            proposal_id = f"bgp_fixture_convergence_{index + 1:02d}"
            old_rows = retirement_rows[index * 2:index * 2 + 2]
            proposals.append(
                {
                    "proposal_id": proposal_id,
                    "subdomain_code": code,
                    "new_source": {
                        "title": f"Fixture trial {index + 1}",
                        "url": f"https://trial-{index + 1}.invalid/updates",
                        "operator": "Fixture operator",
                        "source_type": "official_primary",
                        "evidence_url": f"https://trial-{index + 1}.invalid/evidence",
                        "evidence_checked_on": "2026-08-15",
                        "decision": "trial_new",
                    },
                    "retirements": [
                        {
                            "item_id": row["item_id"],
                            "item_fingerprint": row["item_fingerprint"],
                            "original_title": row["original_title"],
                            "original_url": row["original_url"],
                            "original_subdomain_code": "12",
                            "decision": "delete",
                        }
                        for row in old_rows
                    ],
                    "review_status": "approved",
                    "execution_authorized": False,
                }
            )
            target = taxonomy[code][1:]
            if target not in required_directories:
                required_directories.append(target)
            pilot_groups.append(
                {
                    "group_id": ("A" if index < 5 else "B") + str(index % 5 + 1),
                    "batch": "batch-1" if index < 5 else "batch-2",
                    "proposal_id": proposal_id,
                    "title": f"Fixture trial {index + 1}",
                    "target_collection": target,
                    "retirements": [
                        {
                            "item_id": row["item_id"],
                            "action": (
                                "archive" if index < 4 and offset == 0
                                else "promote_then_stage" if index == 9 and offset == 0
                                else "stage_for_purge"
                            ),
                            "target_collection": (
                                ["99｜Fixture", "91｜Fixture"]
                                if index < 4 and offset == 0
                                else browser_gateway_pilot.TEMPORARY_COLLECTION
                            ),
                            "knowledge_note_required": index == 9 and offset == 0,
                        }
                        for offset, row in enumerate(old_rows)
                    ],
                }
            )
        required_directories.append(["99｜Fixture", "91｜Fixture"])
        wave = {
            "schema_version": 1,
            "kind": "browser_gateway_wave",
            "wave_id": "bgw_fixture_convergence_01",
            "created_at": "2026-08-15",
            "policy_version": "browser-gateway-v1",
            "source": {
                "organization_id": organization["organization_id"],
                "artifact_sha256": "a" * 64,
                "active_bookmark_count": 110,
            },
            "proposals": proposals,
            "summary": {
                "new_source_count": 10,
                "retirement_count": 20,
                "projected_active_count": 100,
                "minimum_retirements_per_new": 2,
                "private_content_emitted_to_stdout": False,
            },
            "privacy": organization["privacy"],
            "safari_execution_authorized": False,
            "execution_authorized": False,
        }
        pilot_spec = {
            "pilot_id": "bgpilot_fixture_convergence_01",
            "created_at": "2026-08-15",
            "groups": pilot_groups,
            "required_directories": required_directories,
        }
        organization_errors = convergence.validate_document(organization, "browser-organization")
        if organization_errors:
            raise AssertionError(organization_errors)
        pilot = browser_gateway_pilot.build_pilot(organization, wave, pilot_spec)
        spec = {
            "candidate_id": "bgconv_fixture_convergence_01",
            "created_at": "2026-08-15",
            "target_active": 100,
            "legacy_keep_urls": legacy_urls,
            "quota_fill_sources": [],
            "execution_authorized": False,
            "safari_execution_authorized": False,
        }
        return organization, pilot, spec, policy

    @staticmethod
    def _decision(index: int, code: str, url: str, target: list[str]) -> dict:
        return {
            "item_id": f"bri_fixture_convergence_{index:04d}",
            "item_fingerprint": f"{index:064x}",
            "item_type": "bookmark",
            "original_title": f"Fixture bookmark {index}",
            "suggested_title": None,
            "title_suggestion_rule_ids": [],
            "original_url": url,
            "source_collection": ["Bookmarks", "Legacy"],
            "assignment_basis": "item_override",
            "rule_id": None,
            "duplicate_group_id": None,
            "disposition": "move",
            "target_collection": target,
            "note": None,
            "execution_authorized": False,
        }

    def test_compile_reaches_exact_quota_without_reading_list_import(self) -> None:
        organization, pilot, spec, policy = self.inputs()
        document = convergence.compile_convergence(organization, pilot, spec, policy)
        self.assertEqual(document["summary"]["active_count"], 100)
        self.assertEqual(document["summary"]["legacy_keep_count"], 90)
        self.assertEqual(document["summary"]["trial_new_count"], 10)
        self.assertEqual(document["summary"]["excluded_old_bookmark_count"], 20)
        self.assertEqual(document["target"]["reading_list_count"], 89)
        self.assertFalse(document["execution_authorized"])
        self.assertEqual(validate := convergence.validate_document(document, "browser-gateway-convergence"), [])

    def test_pilot_retirement_and_duplicate_url_are_rejected(self) -> None:
        organization, pilot, spec, policy = self.inputs()
        invalid = copy.deepcopy(spec)
        retired_url = pilot["groups"][0]["retirements"][0]["original_url"]
        invalid["legacy_keep_urls"]["11"][0] = retired_url
        with self.assertRaisesRegex(convergence.BrowserGatewayConvergenceError, "pilot retirement"):
            convergence.compile_convergence(organization, pilot, invalid, policy)

    def test_import_html_is_deterministic_exact_and_reading_list_free(self) -> None:
        organization, pilot, spec, policy = self.inputs()
        document = convergence.compile_convergence(organization, pilot, spec, policy)
        order = self.ordering(document)
        first = convergence.render_import_html(document, order)
        second = convergence.render_import_html(document, order)
        self.assertEqual(first, second)
        result = convergence.validate_import_html(first, document, order)
        self.assertEqual(result["bookmark_count"], 100)
        self.assertEqual(result["reading_list_count"], 0)
        self.assertTrue(result["order_verified"])
        self.assertNotIn(b"com.apple.ReadingList", first)
        parser = convergence.NetscapeBookmarkParser()
        parser.feed(first.decode("utf-8"))
        parser.close()
        self.assertEqual(
            {tuple(row["folder_path"]) for row in parser.entries},
            {(row["target_collection"][-1],) for row in document["active_sources"]},
        )
        self.assertEqual(len({tuple(row["folder_path"]) for row in parser.entries}), 15)
        for top in organization["taxonomy"]["top_levels"]:
            if top["role"] == "active":
                self.assertNotIn(f"<H3>{top['folder_name']}</H3>".encode(), first)

    def test_import_preview_declares_one_level_system_favorites_projection(self) -> None:
        organization, pilot, spec, policy = self.inputs()
        document = convergence.compile_convergence(organization, pilot, spec, policy)
        order = self.ordering(document)
        with self.subTest("stable public projection metadata"):
            self.assertEqual(convergence.IMPORT_FOLDER_DEPTH, 1)
            self.assertEqual(convergence.SAFARI_PARENT_COLLECTION, "Favorites")
        payload = convergence.render_import_html(document, order)
        self.assertEqual(convergence.validate_import_html(payload, document, order)["bookmark_count"], 100)

    def ordering(self, document: dict) -> dict:
        folders = []
        by_code = {}
        for row in document["active_sources"]:
            code = row["target_collection"][-1][:2]
            by_code.setdefault(code, []).append(row)
        for code in sorted(by_code):
            rows = sorted(by_code[code], key=lambda row: row["source_id"])
            pinned = rows[:1]
            core = [row for row in rows[1:] if row["origin"] == "legacy"]
            trial = [row for row in rows[1:] if row["origin"] != "legacy"]
            folders.append({
                "code": code,
                "items": [
                    {"source_id": row["source_id"], "tier": "pinned", "reason": "manual_pin"}
                    for row in pinned
                ] + [
                    {"source_id": row["source_id"], "tier": "core", "reason": "recurring_value"}
                    for row in core
                ] + [
                    {"source_id": row["source_id"], "tier": "trial", "reason": "recency"}
                    for row in trial
                ],
            })
        return browser_gateway_order.compile_order(document, {
            "order_id": "bgo_fixture_convergence_01",
            "created_at": "2026-08-15",
            "folders": folders,
            "safari_execution_authorized": False,
            "execution_authorized": False,
        })

    def test_order_requires_complete_unique_coverage(self) -> None:
        organization, pilot, spec, policy = self.inputs()
        document = convergence.compile_convergence(organization, pilot, spec, policy)
        order = self.ordering(document)
        self.assertEqual(order["summary"]["folder_count"], 15)
        self.assertEqual(order["summary"]["item_count"], 100)
        self.assertEqual(convergence.validate_document(order, "browser-gateway-order"), [])
        invalid = copy.deepcopy(order)
        invalid["folders"][0]["items"].append(copy.deepcopy(invalid["folders"][0]["items"][0]))
        with self.assertRaisesRegex(browser_gateway_order.BrowserGatewayOrderError, "coverage|duplicated|contiguous"):
            browser_gateway_order.ordered_active_sources(invalid, document)

    def test_reviewed_99_source_target_is_valid_inside_operating_range(self) -> None:
        organization, pilot, spec, policy = self.inputs()
        spec["target_active"] = 99
        spec["legacy_keep_urls"]["12"].pop()
        document = convergence.compile_convergence(organization, pilot, spec, policy)
        self.assertEqual(document["summary"]["active_count"], 99)
        self.assertEqual(document["target"]["active_bookmark_count"], 99)

    def test_wrong_target_count_fails_closed(self) -> None:
        organization, pilot, spec, policy = self.inputs()
        invalid = copy.deepcopy(spec)
        invalid["legacy_keep_urls"]["12"].pop()
        with self.assertRaisesRegex(convergence.BrowserGatewayConvergenceError, "reviewed target"):
            convergence.compile_convergence(organization, pilot, invalid, policy)


if __name__ == "__main__":
    unittest.main()
