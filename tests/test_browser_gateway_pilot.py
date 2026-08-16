#!/usr/bin/env python3
"""Hermetic contracts for the manual Safari Browser Gateway pilot."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import browser_gateway_pilot  # noqa: E402


class BrowserGatewayPilotTests(unittest.TestCase):
    def inputs(self) -> tuple[dict, dict, dict]:
        decisions = []
        for index in range(1, 312):
            decisions.append(
                {
                    "item_id": f"bri_fixture_pilot_{index:04d}",
                    "item_fingerprint": f"{index:064x}",
                    "item_type": "bookmark",
                    "original_title": f"Private fixture bookmark {index}",
                    "suggested_title": None,
                    "title_suggestion_rule_ids": [],
                    "original_url": f"https://private-{index}.invalid/source",
                    "source_collection": ["Bookmarks", "Legacy"],
                    "assignment_basis": "item_override",
                    "rule_id": None,
                    "duplicate_group_id": None,
                    "disposition": "move",
                    "target_collection": ["Favorites", "01｜Fixture", "11｜Fixture"],
                    "note": None,
                    "execution_authorized": False,
                }
            )
        for index in range(1, 90):
            decisions.append(
                {
                    "item_id": f"bri_fixture_reading_{index:04d}",
                    "item_fingerprint": f"{1000 + index:064x}",
                    "item_type": "reading_list",
                    "original_title": f"Private fixture reading {index}",
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
        organization = {
            "schema_version": 1,
            "kind": "browser_organization",
            "organization_id": "borg_fixture_pilot_000001",
            "created_at": "2026-08-15",
            "source": {
                "browser": "safari",
                "interface": "safari_export_zip",
                "artifact_sha256": "a" * 64,
                "bookmark_count": 311,
                "reading_list_count": 89,
                "item_count": 400,
            },
            "taxonomy": {
                "version": 1,
                "maximum_semantic_depth": 2,
                "project_system": "obsidian",
                "reading_list_role": "temporary_inbox",
                "domains": [
                    {
                        "code": f"0{domain}",
                        "label": f"Fixture domain {domain}",
                        "archive_code": f"9{domain}",
                        "archive_label": f"Fixture archive {domain}",
                        "subdomains": [
                            {"code": f"{domain}{sub}", "label": f"Fixture {domain}{sub}"}
                            for sub in range(1, 4)
                        ],
                    }
                    for domain in range(1, 6)
                ],
            },
            "directory_rules": [],
            "item_overrides": [],
            "duplicate_resolutions": [],
            "title_policy": {
                "mode": "suggest_only",
                "rules": ["collapse_whitespace", "remove_exact_host_suffix", "remove_obvious_template_noise"],
                "translate": False,
                "summarize": False,
                "execution_authorized": False,
            },
            "decisions": decisions,
            "summary": {
                "directory_rule_item_count": 0,
                "ambiguous_item_count": 0,
                "duplicate_group_count": 0,
                "active_move_count": 311,
                "archive_count": 0,
                "bookmark_delete_count": 0,
                "reading_list_delete_later_count": 0,
                "reading_list_deferred_count": 89,
                "bookmark_operation_count": 311,
                "item_count": 400,
            },
            "privacy": {
                "provenance": "private_user_data",
                "storage_layer": "private_icloud",
                "contains_private_content": True,
                "git_allowed": False,
                "redaction_required": True,
            },
            "execution_authorized": False,
        }
        organization = json.loads(
            (ROOT / "tests/fixtures/schema_contract/browser-organization-v1.json").read_text(
                encoding="utf-8"
            )
        )
        organization["organization_id"] = "borg_fixture_pilot_000001"
        organization["source"].update(
            artifact_sha256="a" * 64,
            bookmark_count=311,
            reading_list_count=89,
            item_count=400,
        )
        organization["decisions"] = decisions
        organization["summary"].update(
            active_move_count=311,
            reading_list_deferred_count=89,
            bookmark_operation_count=311,
            item_count=400,
        )
        proposals = []
        group_specs = []
        required = [browser_gateway_pilot.TEMPORARY_COLLECTION]
        codes = ["31", "13", "13", "31", "42", "42", "11", "22", "22", "11"]
        for offset, group_id in enumerate([f"A{i}" for i in range(1, 6)] + [f"B{i}" for i in range(1, 6)]):
            proposal_id = f"bgp_fixture_pilot_{offset + 1:02d}"
            retirement_rows = []
            action_rows = []
            for inner in range(2):
                decision = decisions[offset * 2 + inner]
                retirement_rows.append(
                    {
                        "item_id": decision["item_id"],
                        "item_fingerprint": decision["item_fingerprint"],
                        "original_title": decision["original_title"],
                        "original_url": decision["original_url"],
                        "original_subdomain_code": "11",
                        "decision": "promote_to_obsidian" if offset == 9 and inner == 0 else "delete",
                    }
                )
                archive = (group_id in {"A1", "A2", "B1", "B2"}) and inner == 0
                action = "archive" if archive else "stage_for_purge"
                if offset == 9 and inner == 0:
                    action = "promote_then_stage"
                target = ["99｜Fixture Archive", "91｜Fixture"] if archive else browser_gateway_pilot.TEMPORARY_COLLECTION
                action_rows.append(
                    {
                        "item_id": decision["item_id"],
                        "action": action,
                        "target_collection": target,
                        "knowledge_note_required": action == "promote_then_stage",
                    }
                )
                if archive and target not in required:
                    required.append(target)
            target = ["01｜Fixture", f"{codes[offset]}｜Fixture"]
            if target not in required:
                required.append(target)
            new_source = {
                "title": f"Fixture new source {offset + 1}",
                "url": f"https://new-{offset + 1}.invalid/updates",
                "operator": "Fixture operator",
                "source_type": "official_primary",
                "evidence_url": f"https://new-{offset + 1}.invalid/evidence",
                "evidence_checked_on": "2026-08-15",
                "decision": "trial_new",
            }
            proposals.append(
                {
                    "proposal_id": proposal_id,
                    "subdomain_code": codes[offset],
                    "new_source": new_source,
                    "retirements": retirement_rows,
                    "review_status": "approved",
                    "execution_authorized": False,
                }
            )
            group_specs.append(
                {
                    "group_id": group_id,
                    "batch": "batch-1" if group_id.startswith("A") else "batch-2",
                    "proposal_id": proposal_id,
                    "title": new_source["title"],
                    "target_collection": target,
                    "retirements": action_rows,
                }
            )
        wave = {
            "schema_version": 1,
            "kind": "browser_gateway_wave",
            "wave_id": "bgw_fixture_pilot_0001",
            "created_at": "2026-08-15",
            "policy_version": "browser-gateway-v1",
            "source": {
                "organization_id": organization["organization_id"],
                "artifact_sha256": "a" * 64,
                "active_bookmark_count": 311,
            },
            "proposals": proposals,
            "summary": {
                "new_source_count": 10,
                "retirement_count": 20,
                "projected_active_count": 301,
                "minimum_retirements_per_new": 2,
                "private_content_emitted_to_stdout": False,
            },
            "privacy": organization["privacy"],
            "safari_execution_authorized": False,
            "execution_authorized": False,
        }
        spec = {
            "pilot_id": "bgpilot_fixture_0001",
            "created_at": "2026-08-15",
            "groups": group_specs,
            "required_directories": required,
        }
        return organization, wave, spec

    def export(self, path: Path, items: list[tuple[str, str, tuple[str, ...], str]]) -> Path:
        tree: dict = {}
        for title, url, folders, item_type in items:
            node = tree
            path_parts = ("Reading List",) if item_type == "reading_list" else folders
            for folder in path_parts:
                node = node.setdefault(folder, {})
            node.setdefault("__items__", []).append((title, url))

        def render(node: dict) -> str:
            parts = ["<DL><p>"]
            for title, url in node.get("__items__", []):
                parts.append(f'<DT><A HREF="{url}">{title}</A>')
            for folder, child in node.items():
                if folder == "__items__":
                    continue
                identifier = ' IDENTIFIER="com.apple.ReadingList"' if folder == "Reading List" else ""
                parts.append(f"<DT><H3{identifier}>{folder}</H3>{render(child)}")
            parts.append("</DL><p>")
            return "".join(parts)

        html = "<!DOCTYPE NETSCAPE-Bookmark-file-1>" + render(tree)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as output:
            output.writestr("Bookmarks.html", html.encode())
        return path

    def baseline_items(self) -> list[tuple[str, str, tuple[str, ...], str]]:
        rows = [
            (f"Private fixture bookmark {index}", f"https://private-{index}.invalid/source", ("Bookmarks", "Legacy"), "bookmark")
            for index in range(1, 312)
        ]
        rows.extend(
            (f"Private fixture reading {index}", f"https://reading-{index}.invalid/source", ("Reading List",), "reading_list")
            for index in range(1, 90)
        )
        return rows

    def checkpoint_items(self, pilot: dict, checkpoint: str) -> list[tuple[str, str, tuple[str, ...], str]]:
        rows = self.baseline_items()
        by_url = {row[1]: row for row in rows}
        active_batches = {"batch-1"} if checkpoint == "batch-1" else {"batch-1", "batch-2"}
        for group in pilot["groups"]:
            if group["batch"] not in active_batches:
                continue
            source = group["new_source"]
            by_url[source["url"]] = (source["title"], source["url"], tuple(source["target_collection"]), "bookmark")
            for retirement in group["retirements"]:
                if checkpoint == "purge" and retirement["action"] != "archive":
                    by_url.pop(retirement["original_url"])
                else:
                    by_url[retirement["original_url"]] = (
                        retirement["original_title"],
                        retirement["original_url"],
                        tuple(retirement["target_collection"]),
                        "bookmark",
                    )
        return list(by_url.values())

    def test_build_freezes_exact_counts_and_supersedes_old_wave(self) -> None:
        organization, wave, spec = self.inputs()
        pilot = browser_gateway_pilot.build_pilot(organization, wave, spec)
        self.assertEqual(browser_gateway_pilot.validate_pilot(pilot), [])
        self.assertEqual(pilot["source"]["supersedes_wave_id"], wave["wave_id"])
        self.assertEqual(pilot["summary"]["stage_for_purge_count"], 16)
        self.assertEqual(pilot["summary"]["archive_count"], 4)
        self.assertFalse(pilot["execution_authorized"])
        self.assertFalse(pilot["safari_execution_authorized"])

    def test_wrong_counts_or_partial_manifest_are_rejected(self) -> None:
        organization, wave, spec = self.inputs()
        invalid = copy.deepcopy(spec)
        invalid["groups"][0]["retirements"].pop()
        with self.assertRaisesRegex(browser_gateway_pilot.BrowserGatewayPilotError, "manifest"):
            browser_gateway_pilot.build_pilot(organization, wave, invalid)

    def test_batch_one_verification_passes_and_detects_reading_list_drift(self) -> None:
        organization, wave, spec = self.inputs()
        pilot = browser_gateway_pilot.build_pilot(organization, wave, spec)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.export(root / "source.zip", self.baseline_items())
            baseline = self.export(root / "baseline.zip", self.baseline_items())
            current = self.export(root / "current.zip", self.checkpoint_items(pilot, "batch-1"))
            pilot["source"]["baseline_export_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
            result = browser_gateway_pilot.verify_checkpoint(
                pilot, source, baseline, current, "batch-1", observed_on="2026-08-15"
            )
            self.assertEqual(result["status"], "passed", result["reasons"])
            self.assertEqual(result["observed"]["bookmark_count"], 316)
            self.assertEqual(result["observed"]["reading_list_count"], 89)
            self.assertEqual(result["new_source_review_after"], "2026-09-29")

            drifted_rows = self.checkpoint_items(pilot, "batch-1")
            drifted_rows = [
                row for row in drifted_rows if row[1] != "https://reading-89.invalid/source"
            ]
            drifted = self.export(root / "drifted.zip", drifted_rows)
            failed = browser_gateway_pilot.verify_checkpoint(
                pilot, source, baseline, drifted, "batch-1", observed_on="2026-08-15"
            )
            self.assertEqual(failed["status"], "failed")
            self.assertIn("reading_list_drift", failed["reasons"])


if __name__ == "__main__":
    unittest.main()
