#!/usr/bin/env python3
"""Hermetic tests for the read-only DSH Computer Use verification script."""

from __future__ import annotations

import json
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import verify_dsh_computer_use as verifier  # noqa: E402

DUMP_OUTPUT_OK = """# == dsh-computer-use
- id: computer-use-host
  name: dsh-computer-use/host
  config:
    stateDir: !!js dshHomePath('computer-use')
- id: computer-use-tool
  name: dsh-computer-use/tool
"""


def make_bundle(root: Path, bundle_id: str, version: str = "0.3.0") -> Path:
    bundle = root / "DSH Computer Use.app"
    contents = bundle / "Contents"
    contents.mkdir(parents=True)
    (contents / "Info.plist").write_bytes(
        plistlib.dumps(
            {
                "CFBundleIdentifier": bundle_id,
                "CFBundleShortVersionString": version,
            }
        )
    )
    return bundle


class BundleCheckTests(unittest.TestCase):
    def test_missing_bundle_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(verifier, "APP_PATH", Path(tmp) / "absent.app"):
                result = verifier.bundle_check()
        self.assertFalse(result["ok"])
        self.assertEqual(result["reason"], "app bundle missing")

    def test_matching_bundle_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            make_bundle(Path(tmp), verifier.BUNDLE_ID)
            with mock.patch.object(verifier, "APP_PATH", Path(tmp) / "DSH Computer Use.app"):
                result = verifier.bundle_check()
        self.assertTrue(result["ok"])
        self.assertEqual(result["bundle_identifier"], verifier.BUNDLE_ID)
        self.assertEqual(result["version"], "0.3.0")

    def test_mismatched_bundle_id_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            make_bundle(Path(tmp), "com.example.wrong")
            with mock.patch.object(verifier, "APP_PATH", Path(tmp) / "DSH Computer Use.app"):
                result = verifier.bundle_check()
        self.assertFalse(result["ok"])
        self.assertIn("unexpected bundle id", result["reason"])


class CatalogCheckTests(unittest.TestCase):
    def test_matching_catalog_entry_passes(self) -> None:
        entry = {
            "name": "DSH Computer Use",
            "brew_cask": "zrui-c/tap/dsh-computer-use",
            "application_path": "/Applications/DSH Computer Use.app",
            "bundle_identifiers": [verifier.BUNDLE_ID],
        }
        result = verifier.catalog_check(entry)
        self.assertTrue(result["ok"])
        self.assertEqual(result["problems"], [])

    def test_wrong_cask_and_missing_bundle_id_fail(self) -> None:
        entry = {
            "name": "DSH Computer Use",
            "brew_cask": "some-other/tap/cask",
            "application_path": "/Applications/DSH Computer Use.app",
            "bundle_identifiers": [],
        }
        result = verifier.catalog_check(entry)
        self.assertFalse(result["ok"])
        joined = "\n".join(result["problems"])
        self.assertIn("brew_cask", joined)
        self.assertIn("bundle_identifiers", joined)


class PluginCheckTests(unittest.TestCase):
    def _run(self, stdout: str, returncode: int = 0, stderr: str = "") -> dict:
        response = subprocess.CompletedProcess(
            ["dsh", "--profile", "web", "--dump-config"],
            returncode,
            stdout,
            stderr,
        )
        with mock.patch.object(verifier.subprocess, "run", return_value=response):
            return verifier.plugin_check()

    def test_enabled_rows_pass(self) -> None:
        result = self._run(DUMP_OUTPUT_OK)
        self.assertTrue(result["ok"])
        self.assertEqual(result["rows"], {"computer-use-host": 1, "computer-use-tool": 1})

    def test_missing_row_fails(self) -> None:
        result = self._run("- id: some-other-plugin\n")
        self.assertFalse(result["ok"])
        self.assertEqual(result["rows"]["computer-use-host"], 0)

    def test_duplicate_row_fails(self) -> None:
        result = self._run(DUMP_OUTPUT_OK + "- id: computer-use-host\n  name: dsh-computer-use/host\n")
        self.assertFalse(result["ok"])
        self.assertEqual(result["rows"]["computer-use-host"], 2)

    def test_nonzero_exit_fails_with_stderr(self) -> None:
        result = self._run("", returncode=1, stderr="boom")
        self.assertFalse(result["ok"])
        self.assertIn("exit 1", result["reason"])

    def test_subprocess_error_fails(self) -> None:
        with mock.patch.object(
            verifier.subprocess, "run", side_effect=OSError("no dsh")
        ):
            result = verifier.plugin_check()
        self.assertFalse(result["ok"])
        self.assertIn("dsh dump-config failed", result["reason"])


class ReportShapeTests(unittest.TestCase):
    def _run_main(self, tmp: str) -> tuple[int, dict]:
        make_bundle(Path(tmp), verifier.BUNDLE_ID)
        catalog = Path(tmp) / "catalog.json"
        catalog.write_text(
            json.dumps(
                {
                    "apps": [
                        {
                            "name": "DSH Computer Use",
                            "brew_cask": "zrui-c/tap/dsh-computer-use",
                            "application_path": "/Applications/DSH Computer Use.app",
                            "bundle_identifiers": [verifier.BUNDLE_ID],
                        }
                    ]
                }
            )
        )
        response = subprocess.CompletedProcess([], 0, DUMP_OUTPUT_OK, "")
        patches = [
            mock.patch.object(verifier, "APP_PATH", Path(tmp) / "DSH Computer Use.app"),
            mock.patch.object(verifier, "CATALOG", catalog),
            mock.patch.object(verifier.subprocess, "run", return_value=response),
            mock.patch.object(verifier.sys, "argv", ["verify_dsh_computer_use.py"]),
        ]
        for patch in patches:
            patch.start()
        try:
            with mock.patch("sys.stdout") as stdout:
                code = verifier.main()
        finally:
            for patch in reversed(patches):
                patch.stop()
        output = "".join(call.args[0] for call in stdout.write.call_args_list)
        return code, json.loads(output)

    def test_full_report_passes_and_marks_tcc_manual(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code, report = self._run_main(tmp)
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["kind"], "dsh_computer_use_verification")
        for check in ("bundle", "catalog", "plugin"):
            self.assertTrue(report["checks"][check]["ok"])
        for service in ("Accessibility", "Screen Recording"):
            self.assertEqual(
                report["tcc_status"][service],
                "manual_verification_required",
            )
        self.assertIn("no permission grant", report["policy"])


if __name__ == "__main__":
    unittest.main()
