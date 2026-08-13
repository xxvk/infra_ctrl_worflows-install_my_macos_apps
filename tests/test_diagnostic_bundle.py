#!/usr/bin/env python3
"""Hermetic tests for redacted diagnostic preview and export."""

from __future__ import annotations

import datetime as dt
import io
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from collections import Counter
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import diagnostic_bundle  # noqa: E402


FIXED_TIME = dt.datetime(2026, 7, 23, tzinfo=dt.timezone.utc)


def fake_runner(*, failing_check: bool = False):
    def run(command, **_kwargs):
        command = [str(item) for item in command]
        if command[-1:] == ["--version"] and "macomrade" in command[0]:
            return subprocess.CompletedProcess(command, 0, "macomrade 0.1.0\n", "")
        if command == ["sw_vers", "-productVersion"]:
            return subprocess.CompletedProcess(command, 0, "27.0\n", "")
        if command == ["uname", "-m"]:
            return subprocess.CompletedProcess(command, 0, "arm64\n", "")
        if command[-4:] == [
            "scripts/icloud_git_guard.py",
            "inspect",
            "--repo",
            ".",
        ]:
            return subprocess.CompletedProcess(command, 0, "status: ready\n", "")
        if command == ["git", "rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, f"{'a' * 40}\n", "")
        if command == ["git", "status", "--porcelain", "--untracked-files=all"]:
            return subprocess.CompletedProcess(command, 0, " M tracked.py\n?? new.py\n", "")
        if failing_check and any(
            item.endswith("validate_release_contract.py") for item in command
        ):
            unsafe = (
                "person@example.com /Users/example/private/secret-name.txt "
                "Private/chrome-profiles.json "
                "access_token=abc123secret https://example.com/path?token=secret "
                + ("x" * 5000)
            )
            return subprocess.CompletedProcess(command, 7, "", unsafe)
        return subprocess.CompletedProcess(
            command,
            0,
            '{"status":"passed","owner":"person@example.com"}\n',
            "",
        )

    return run


def fixture_diagnostics() -> dict:
    return diagnostic_bundle.collect(
        runner=fake_runner(failing_check=True),
        now=lambda: FIXED_TIME,
    )


class DiagnosticBundleTests(unittest.TestCase):
    def test_repository_definition_is_bounded_and_valid(self) -> None:
        result = diagnostic_bundle.validate_definition()
        self.assertEqual(result["status"], "passed", result["errors"])
        self.assertEqual(result["checks"], 6)
        self.assertEqual(result["policy_hashes"], 6)
        self.assertEqual(result["log_limit_bytes"], 4096)

    def test_collection_is_bounded_redacted_and_schema_valid(self) -> None:
        result = fixture_diagnostics()
        serialized = json.dumps(result)
        self.assertNotIn("person@example.com", serialized)
        self.assertNotIn("/Users/mini", serialized)
        self.assertNotIn("access_token", serialized)
        self.assertNotIn("?token=secret", serialized)
        failed = next(row for row in result["checks"] if row["status"] == "failed")
        self.assertTrue(failed["log"]["truncated"])
        self.assertLessEqual(
            len(failed["log"]["stderr_tail"].encode("utf-8")),
            diagnostic_bundle.LOG_LIMIT_BYTES,
        )
        self.assertEqual(failed["failure_class"], "command_failed")
        self.assertEqual(
            result["failure_classes"],
            [
                {
                    "class": "command_failed",
                    "count": 1,
                    "check_ids": ["release-contract"],
                }
            ],
        )
        self.assertTrue(all(row["path"] in diagnostic_bundle.POLICY_PATHS for row in result["policy_hashes"]))
        self.assertNotIn("Private/", serialized)
        self.assertNotIn("TCC.db", serialized)
        self.assertEqual(result["product"]["source"]["worktree_status"], "dirty")
        self.assertEqual(result["product"]["source"]["change_count"], 2)
        self.assertEqual(
            len(result["product"]["source"]["implementation_hashes"]),
            len(diagnostic_bundle.IMPLEMENTATION_PATHS),
        )

    def test_structured_sensitive_fields_are_removed(self) -> None:
        counts: Counter[str] = Counter()
        sanitized = diagnostic_bundle.sanitize_value(
            {
                "access_token": "secret",
                "preferred_account": "person@example.com",
                "hostname": "private-mac",
                "safe": "keep",
            },
            counts=counts,
        )
        self.assertEqual(sanitized, {"safe": "keep"})
        self.assertEqual(counts["credential_fields_removed"], 1)
        self.assertEqual(counts["account_fields_removed"], 1)
        self.assertEqual(counts["host_fields_removed"], 1)

    def test_unavailable_source_guard_never_runs_git(self) -> None:
        runner = mock.Mock(
            return_value=subprocess.CompletedProcess([], 1, "", "unavailable")
        )
        result = diagnostic_bundle.source_revision(runner=runner)
        self.assertEqual(
            result,
            {
                "guard": "unavailable",
                "revision": "unavailable",
                "worktree_status": "unavailable",
                "change_count": None,
                "implementation_hashes": diagnostic_bundle.implementation_hashes(),
            },
        )
        self.assertEqual(runner.call_count, 1)

    def test_preview_redacts_home_output_and_exposes_exact_payload(self) -> None:
        diagnostics = fixture_diagnostics()
        result = diagnostic_bundle.preview(
            diagnostics,
            output=Path("/Users/private-person/Desktop/support.zip"),
        )
        self.assertEqual(result["output"], "<HOME>/<redacted-path>")
        self.assertEqual(result["payload_preview"]["diagnostics"], diagnostics)
        self.assertFalse(result["manifest"]["policy"]["sharing_authorized"])
        self.assertTrue(
            result["manifest"]["policy"]["local_payload_review_required"]
        )

    def test_preview_builds_verified_manifest_without_writing(self) -> None:
        diagnostics = fixture_diagnostics()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "diagnostics.zip"
            result = diagnostic_bundle.preview(diagnostics, output=output)
            self.assertFalse(output.exists())
        self.assertEqual(result["status"], "preview")
        self.assertFalse(result["export_authorized"])
        self.assertTrue(result["predicted_zip"]["verified"])
        self.assertEqual(result["predicted_zip"]["manifest_files"], 2)

    def test_export_requires_exact_confirmation_and_never_overwrites(self) -> None:
        diagnostics = fixture_diagnostics()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "diagnostics.zip"
            with self.assertRaisesRegex(
                diagnostic_bundle.DiagnosticBundleError,
                diagnostic_bundle.EXPORT_CONFIRMATION,
            ):
                diagnostic_bundle.export(
                    diagnostics,
                    output,
                    confirmation="wrong",
                )
            self.assertFalse(output.exists())

            result = diagnostic_bundle.export(
                diagnostics,
                output,
                confirmation=diagnostic_bundle.EXPORT_CONFIRMATION,
            )
            self.assertEqual(result["status"], "exported")
            self.assertTrue(result["verified"])
            self.assertFalse(result["publication_authorized"])

            with zipfile.ZipFile(output) as archive:
                self.assertEqual(
                    sorted(archive.namelist()),
                    ["diagnostics.json", "manifest.json", "redaction-report.json"],
                )
                exported = archive.read("diagnostics.json").decode("utf-8")
                self.assertNotIn("person@example.com", exported)
                self.assertNotIn("/Users/mini", exported)
                self.assertNotIn("access_token", exported)

            with self.assertRaisesRegex(
                diagnostic_bundle.DiagnosticBundleError,
                "refusing to overwrite",
            ):
                diagnostic_bundle.export(
                    diagnostics,
                    output,
                    confirmation=diagnostic_bundle.EXPORT_CONFIRMATION,
                )

    def test_export_cannot_overwrite_destination_created_during_link(self) -> None:
        diagnostics = fixture_diagnostics()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "diagnostics.zip"

            def race(_temporary, destination):
                Path(destination).write_text("racer", encoding="utf-8")
                raise FileExistsError

            with mock.patch.object(diagnostic_bundle.os, "link", side_effect=race):
                with self.assertRaisesRegex(
                    diagnostic_bundle.DiagnosticBundleError,
                    "refusing to overwrite",
                ):
                    diagnostic_bundle.export(
                        diagnostics,
                        output,
                        confirmation=diagnostic_bundle.EXPORT_CONFIRMATION,
                    )
            self.assertEqual(output.read_text(encoding="utf-8"), "racer")

    def test_zip_bytes_are_deterministic_for_same_diagnostics(self) -> None:
        diagnostics = fixture_diagnostics()
        artifacts, manifest = diagnostic_bundle.build_artifacts(diagnostics)
        self.assertEqual(
            diagnostic_bundle.build_zip(artifacts, manifest),
            diagnostic_bundle.build_zip(artifacts, manifest),
        )

    def test_export_command_without_apply_writes_nothing(self) -> None:
        diagnostics = fixture_diagnostics()
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "diagnostics.zip"
            stderr = io.StringIO()
            with mock.patch.object(
                diagnostic_bundle,
                "collect",
                return_value=diagnostics,
            ):
                with redirect_stderr(stderr):
                    returncode = diagnostic_bundle.main(
                        ["export", "--output", str(output)]
                    )
            self.assertEqual(returncode, 1)
            self.assertFalse(output.exists())
            self.assertIn("preview-only", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
