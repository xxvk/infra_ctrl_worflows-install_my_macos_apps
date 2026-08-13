#!/usr/bin/env python3
"""Hermetic tests for machine-local state resolution and migration."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import migrate_state  # noqa: E402
import state_paths  # noqa: E402


class StatePathTests(unittest.TestCase):
    def test_cli_override_wins_over_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            resolved = state_paths.resolve_state_dir(
                root / "cli",
                environ={state_paths.STATE_DIR_ENV: str(root / "env")},
                home=root / "home",
                machine_id="test-machine",
            )
            self.assertEqual(resolved, (root / "cli").resolve())

    def test_environment_wins_over_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            resolved = state_paths.resolve_state_dir(
                None,
                environ={state_paths.STATE_DIR_ENV: str(root / "env")},
                home=root / "home",
                machine_id="test-machine",
            )
            self.assertEqual(resolved, (root / "env").resolve())

    def test_default_is_machine_scoped_application_support(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            resolved = state_paths.resolve_state_dir(
                None,
                environ={},
                home=home,
                machine_id="machine-abc123",
            )
            self.assertEqual(
                resolved,
                home
                / "Library/Application Support/install-macos-apps/state/machine-abc123",
            )

    def test_machine_id_is_hashed_and_does_not_expose_raw_identifier(self) -> None:
        machine_id = state_paths.machine_id(raw_identity="RAW-PLATFORM-UUID")
        self.assertRegex(machine_id, r"^mac-[0-9a-f]{12}$")
        self.assertNotIn("RAW", machine_id)

    def test_runtime_writers_do_not_default_to_repository_state(self) -> None:
        allowed = {"migrate_state.py"}
        offenders = []
        repository_state = re.compile(
            r"\b(?:ROOT|REPO_ROOT|PROJECT_ROOT|SKILL_ROOT)\s*/\s*['\"]state['\"]"
        )
        for path in sorted((ROOT / "scripts").glob("*.py")):
            if path.name in allowed:
                continue
            text = path.read_text(encoding="utf-8")
            if repository_state.search(text):
                offenders.append(path.name)
        self.assertEqual(offenders, [])


class StateMigrationTests(unittest.TestCase):
    def test_copy_first_migration_hashes_and_reads_back_every_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, destination = root / "source", root / "destination"
            (source / "nested").mkdir(parents=True)
            (source / "one.json").write_text('{"one": 1}\n', encoding="utf-8")
            (source / "nested" / "two.txt").write_text("two\n", encoding="utf-8")

            result = migrate_state.copy_and_verify(
                source,
                destination,
                flag_reader=lambda _: set(),
            )

            self.assertEqual(result["status"], "verified")
            self.assertEqual(result["source_file_count"], 2)
            self.assertEqual(result["verified_file_count"], 2)
            self.assertEqual((destination / "nested" / "two.txt").read_text(), "two\n")
            self.assertTrue(Path(result["manifest_path"]).is_file())

    def test_conflicting_destination_is_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, destination = root / "source", root / "destination"
            source.mkdir()
            destination.mkdir()
            (source / "same.json").write_text("source\n", encoding="utf-8")
            (destination / "same.json").write_text("different\n", encoding="utf-8")

            with self.assertRaises(migrate_state.MigrationConflictError):
                migrate_state.copy_and_verify(
                    source,
                    destination,
                    flag_reader=lambda _: set(),
                )

            self.assertEqual((source / "same.json").read_text(), "source\n")
            self.assertEqual((destination / "same.json").read_text(), "different\n")

    def test_dataless_source_refuses_copy_before_reading_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, destination = root / "source", root / "destination"
            source.mkdir()
            unavailable = source / "cloud.json"
            unavailable.write_text("placeholder\n", encoding="utf-8")

            with self.assertRaises(migrate_state.SourceUnavailableError):
                migrate_state.copy_and_verify(
                    source,
                    destination,
                    flag_reader=lambda path: {"dataless"}
                    if path.resolve() == unavailable.resolve()
                    else set(),
                )

            self.assertFalse(destination.exists())

    def test_cleanup_requires_confirmation_and_preserves_new_unknown_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, destination = root / "source", root / "destination"
            source.mkdir()
            (source / "old.json").write_text("old\n", encoding="utf-8")
            result = migrate_state.copy_and_verify(
                source,
                destination,
                flag_reader=lambda _: set(),
            )
            manifest = json.loads(Path(result["manifest_path"]).read_text())
            (source / "arrived-later.json").write_text("new\n", encoding="utf-8")

            with self.assertRaises(migrate_state.ConfirmationError):
                migrate_state.cleanup_verified_source(
                    source,
                    destination,
                    manifest,
                    confirmation="wrong",
                    flag_reader=lambda _: set(),
                )

            cleanup = migrate_state.cleanup_verified_source(
                source,
                destination,
                manifest,
                confirmation=migrate_state.CLEANUP_CONFIRMATION,
                flag_reader=lambda _: set(),
            )
            self.assertEqual(cleanup["removed_file_count"], 1)
            self.assertFalse((source / "old.json").exists())
            self.assertTrue((source / "arrived-later.json").exists())

    def test_cleanup_cli_without_confirmation_is_a_non_destructive_preview(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, destination = root / "source", root / "destination"
            source.mkdir()
            original = source / "old.json"
            original.write_text("old\n", encoding="utf-8")
            result = migrate_state.copy_and_verify(
                source,
                destination,
                flag_reader=lambda _: set(),
            )

            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "migrate_state.py"),
                    "cleanup-source",
                    "--source",
                    str(source),
                    "--state-dir",
                    str(destination),
                    "--manifest",
                    str(result["manifest_path"]),
                ],
                capture_output=True,
                text=True,
                check=False,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            preview = json.loads(completed.stdout)
            self.assertEqual(preview["status"], "planned")
            self.assertEqual(preview["removable_file_count"], 1)
            self.assertEqual(preview["removable_logical_bytes"], 4)
            self.assertTrue(original.is_file())


if __name__ == "__main__":
    unittest.main()
