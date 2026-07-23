#!/usr/bin/env python3
"""Hermetic fixtures for TCC and defaults platform interfaces."""

from __future__ import annotations

import json
import plistlib
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RESPONSES = json.loads(
    (ROOT / "tests/fixtures/macos_apps/command-responses.json").read_text()
)
sys.path.insert(0, str(ROOT / "scripts"))

import macos_permissions  # noqa: E402
import macos_preferences  # noqa: E402


class TccFixtureTests(unittest.TestCase):
    def test_read_only_tcc_fixture_maps_granted_and_denied_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            database = Path(tmp) / "TCC.db"
            connection = sqlite3.connect(database)
            connection.execute(
                "CREATE TABLE access (service TEXT, client TEXT, client_type INTEGER, "
                "auth_value INTEGER, auth_reason INTEGER, last_modified INTEGER)"
            )
            for row in RESPONSES["tcc"]:
                connection.execute(
                    "INSERT INTO access VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        row["service"],
                        row["client"],
                        row["client_type"],
                        row["auth_value"],
                        row["auth_reason"],
                        row["last_modified"],
                    ),
                )
            connection.commit()
            connection.close()
            with mock.patch.object(macos_permissions, "TCC_DATABASE", database):
                result = macos_permissions.tcc_inventory(
                    [{"bundle_identifier": "com.example.fixture"}]
                )
        self.assertEqual(result["status"], "verified")
        matched = result["application_records"]["com.example.fixture"]
        self.assertEqual(matched[0]["status"], "verified_granted")
        self.assertEqual(result["unmatched_clients"][0]["status"], "verified_denied")

    def test_missing_tcc_database_is_unavailable_not_empty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(
                macos_permissions,
                "TCC_DATABASE",
                Path(tmp) / "missing.db",
            ):
                result = macos_permissions.tcc_inventory([])
        self.assertEqual(result["status"], "unavailable")


class DefaultsFixtureTests(unittest.TestCase):
    def test_defaults_fixture_is_allowlisted_and_private_values_are_redacted(self) -> None:
        payload = plistlib.dumps(RESPONSES["defaults"]["NSGlobalDomain"])
        completed = subprocess.CompletedProcess(
            ["defaults"],
            0,
            stdout=payload,
            stderr=b"",
        )
        with mock.patch.object(
            macos_preferences.subprocess,
            "run",
            return_value=completed,
        ):
            result = macos_preferences.export_domain("NSGlobalDomain")
        self.assertEqual(result["status"], "verified")
        self.assertEqual(result["values"]["AppleLocale"], "ja_JP")
        self.assertEqual(
            result["values"]["NSUserDictionaryReplacementItems"],
            {"redacted": True, "count": 1},
        )
        self.assertNotIn("UntrackedKey", result["values"])

    def test_invalid_defaults_payload_is_unavailable(self) -> None:
        completed = subprocess.CompletedProcess(
            ["defaults"],
            0,
            stdout=b"not-a-plist",
            stderr=b"",
        )
        with mock.patch.object(
            macos_preferences.subprocess,
            "run",
            return_value=completed,
        ):
            result = macos_preferences.export_domain("NSGlobalDomain")
        self.assertEqual(result["status"], "unavailable")


if __name__ == "__main__":
    unittest.main()
