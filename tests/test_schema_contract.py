#!/usr/bin/env python3
"""Hermetic tests for registered JSON Schemas and version migrations."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "schema_contract"
sys.path.insert(0, str(ROOT / "scripts"))

import schema_contract  # noqa: E402


class SchemaContractTests(unittest.TestCase):
    def test_every_registered_tracked_example_validates(self) -> None:
        result = schema_contract.validate_tracked()
        self.assertEqual(result["status"], "passed", result["errors"])
        self.assertEqual(result["formats"], 13)
        self.assertGreaterEqual(result["examples"], 19)

    def test_plan_rejects_missing_version_and_wrong_field_type(self) -> None:
        missing_version = json.loads((FIXTURES / "app-plan-v0.json").read_text())
        errors = schema_contract.validate_document(missing_version, "app-plan")
        self.assertTrue(any("schema_version" in error for error in errors))

        invalid = json.loads((FIXTURES / "app-plan-v1.json").read_text())
        invalid["missing"] = "not-an-array"
        errors = schema_contract.validate_document(invalid, "app-plan")
        self.assertTrue(any("$.missing" in error and "array" in error for error in errors))

    def test_unsupported_schema_keyword_fails_closed(self) -> None:
        schema = {
            "$schema": schema_contract.SCHEMA_DIALECT,
            "type": "object",
            "unevaluatedProperties": False,
        }
        with self.assertRaisesRegex(
            schema_contract.SchemaContractError,
            "unsupported schema keywords",
        ):
            schema_contract.validate_instance({}, schema)

    def test_upgrade_and_downgrade_preserve_unknown_fields(self) -> None:
        original = json.loads((FIXTURES / "app-plan-v0.json").read_text())
        upgraded = schema_contract.migrate_document(original, "app-plan", 1)
        self.assertEqual(upgraded["schema_version"], 1)
        self.assertEqual(upgraded["future_top_level"], "preserve")
        self.assertEqual(
            upgraded["missing"][0]["future_field"],
            {"preserve": True},
        )
        with self.assertRaisesRegex(
            schema_contract.SchemaContractError,
            "--allow-downgrade",
        ):
            schema_contract.migrate_document(upgraded, "app-plan", 0)
        downgraded = schema_contract.migrate_document(
            upgraded,
            "app-plan",
            0,
            allow_downgrade=True,
        )
        self.assertEqual(downgraded, original)

    def test_preview_does_not_write_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "migrated.json"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                returncode = schema_contract.main(
                    [
                        "migrate",
                        "app-plan",
                        str(FIXTURES / "app-plan-v0.json"),
                        "--to",
                        "1",
                        "--output",
                        str(output),
                    ]
                )
            self.assertEqual(returncode, 0)
            self.assertFalse(output.exists())
            self.assertEqual(json.loads(stdout.getvalue())["status"], "preview")

    def test_apply_requires_confirmation_and_separate_output(self) -> None:
        source = FIXTURES / "app-plan-v0.json"
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            returncode = schema_contract.main(
                ["migrate", "app-plan", str(source), "--to", "1", "--apply"]
            )
        self.assertEqual(returncode, 1)
        self.assertIn("--confirm", stderr.getvalue())

        stderr = io.StringIO()
        with redirect_stderr(stderr):
            returncode = schema_contract.main(
                [
                    "migrate",
                    "app-plan",
                    str(source),
                    "--to",
                    "1",
                    "--apply",
                    "--confirm",
                    schema_contract.WRITE_CONFIRMATION,
                    "--output",
                    str(source),
                ]
            )
        self.assertEqual(returncode, 1)
        self.assertIn("must differ", stderr.getvalue())

    def test_apply_writes_verified_output_and_refuses_conflict(self) -> None:
        source = FIXTURES / "app-plan-v0.json"
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "migrated.json"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                returncode = schema_contract.main(
                    [
                        "migrate",
                        "app-plan",
                        str(source),
                        "--to",
                        "1",
                        "--apply",
                        "--confirm",
                        schema_contract.WRITE_CONFIRMATION,
                        "--output",
                        str(output),
                    ]
                )
            result = json.loads(stdout.getvalue())
            self.assertEqual(returncode, 0)
            self.assertEqual(result["status"], "written")
            self.assertTrue(result["verified"])
            schema_contract.load_and_validate(output, "app-plan")

            output.write_text('{"different": true}\n', encoding="utf-8")
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                returncode = schema_contract.main(
                    [
                        "migrate",
                        "app-plan",
                        str(source),
                        "--to",
                        "1",
                        "--apply",
                        "--confirm",
                        schema_contract.WRITE_CONFIRMATION,
                        "--output",
                        str(output),
                    ]
                )
            self.assertEqual(returncode, 1)
            self.assertIn("refusing to overwrite", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
