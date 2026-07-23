#!/usr/bin/env python3
"""Hermetic tests for the component documentation state boundary."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import component_state  # noqa: E402


class ComponentStateTests(unittest.TestCase):
    def test_detects_frontmatter_and_body_machine_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.md"
            path.write_text(
                "---\n"
                'name: "Fixture"\n'
                'installed_version: "1.2.3"\n'
                "---\n"
                "## Verification\n"
                "- [x] Version verified: `1.2.3`.\n",
                encoding="utf-8",
            )
            result = component_state.audit_path(path)
        codes = {row["code"] for row in result["violations"]}
        self.assertIn("machine_state_frontmatter", codes)
        self.assertIn("completed_checkbox", codes)
        self.assertIn("verified_version_observation", codes)

    def test_reusable_installation_knowledge_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.md"
            path.write_text(
                "---\n"
                'name: "Fixture"\n'
                'lifecycle_status: "active"\n'
                'check_command: "fixture --version"\n'
                "---\n"
                "Install with `brew install fixture` and verify with "
                "`fixture --version`.\n",
                encoding="utf-8",
            )
            result = component_state.audit_path(path)
        self.assertEqual(result["violations"], [])

    def test_migration_record_preserves_source_hash_and_lines(self) -> None:
        finding = {
            "schema_version": 1,
            "affected_guides": 1,
            "violation_count": 1,
            "findings": [
                {
                    "guide": "components/fixture.md",
                    "sha256": "abc",
                    "violations": [{"code": "completed_checkbox", "line": 4, "text": "- [x] done"}],
                }
            ],
        }
        record = component_state.migration_record(finding)
        self.assertEqual(record["action_id"], "component-state.migrate")
        self.assertEqual(record["findings"][0]["sha256"], "abc")
        self.assertFalse(record["source_deleted"])

    def test_wrong_confirmation_does_not_write_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/component_state.py"),
                    "--state-dir",
                    tmp,
                    "migrate",
                    "--apply",
                    "--confirm",
                    "wrong",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            files = list(Path(tmp).iterdir())
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("MIGRATE COMPONENT STATE", completed.stderr)
        self.assertEqual(files, [])

    def test_repository_components_are_clean(self) -> None:
        result = component_state.audit()
        self.assertEqual(result["status"], "passed", json.dumps(result["findings"], indent=2))

    def test_template_routes_runtime_results_to_machine_state(self) -> None:
        text = (ROOT / "templates/app-component.md").read_text(encoding="utf-8")
        self.assertNotIn("in frontmatter and the install log", text)
        self.assertNotIn("completion_notes", text)
        self.assertNotIn("verification_status: passed", text)
        self.assertIn("machine-local state", text)

    def test_optional_enricher_is_read_only(self) -> None:
        text = (ROOT / "scripts/enrich_optional_guides.py").read_text(encoding="utf-8")
        self.assertNotIn("path.write_text", text)
        self.assertNotIn("CATALOG.write_text", text)
        self.assertIn('"tracked_files_written": False', text)
        for name in (
            "repair_optional_frontmatter.py",
            "repair_optional_body.py",
            "repair_core_frontmatter.py",
        ):
            repair = (ROOT / "scripts" / name).read_text(encoding="utf-8")
            self.assertNotIn("path.write_text", repair, name)

    def test_generators_do_not_render_machine_state_fields(self) -> None:
        optional = (ROOT / "scripts/generate_optional_guides.py").read_text(encoding="utf-8")
        core = (ROOT / "scripts/enrich_core_guides.py").read_text(encoding="utf-8")
        for source in (optional, core):
            self.assertNotIn("installed_version:", source)
            self.assertNotIn("installed_at:", source)
            self.assertNotIn("installed_bytes:", source)


if __name__ == "__main__":
    unittest.main()
