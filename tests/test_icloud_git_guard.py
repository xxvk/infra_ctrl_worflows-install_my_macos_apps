#!/usr/bin/env python3
"""Hermetic tests for the iCloud-aware Git integrity guard."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import icloud_git_guard as guard  # noqa: E402


def make_git_fixture(root: Path, *, pointer: bool = False) -> tuple[Path, Path]:
    worktree = root / "Mobile Documents" / "repo"
    worktree.mkdir(parents=True)
    git_dir = root / "Mobile Documents" / "parent.git" / "modules" / "repo"
    if pointer:
        git_dir.mkdir(parents=True)
        (worktree / ".git").write_text(
            f"gitdir: {os.path.relpath(git_dir, worktree)}\n", encoding="utf-8"
        )
    else:
        git_dir = worktree / ".git"
        git_dir.mkdir()

    (git_dir / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
    (git_dir / "config").write_text("[core]\n\trepositoryformatversion = 0\n", encoding="utf-8")
    (git_dir / "objects" / "pack").mkdir(parents=True)
    (git_dir / "objects" / "pack" / "pack-test.pack").write_bytes(
        b"PACK\x00\x00\x00\x02\x00\x00\x00\x00"
    )
    (git_dir / "objects" / "pack" / "pack-test.idx").write_bytes(b"\xfftOc\x00\x00\x00\x02")
    (worktree / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    (worktree / "README.md").write_text("# Readme\n", encoding="utf-8")
    (worktree / "VERSION").write_text("0.1.0\n", encoding="utf-8")
    (worktree / "references").mkdir()
    (worktree / "references" / "app-catalog.json").write_text("{}\n", encoding="utf-8")
    return worktree, git_dir


class ICloudGitGuardTests(unittest.TestCase):
    def test_detects_icloud_style_paths(self) -> None:
        self.assertTrue(guard.is_icloud_path(Path("/Users/me/Library/Mobile Documents/repo")))
        self.assertTrue(guard.is_icloud_path(Path("/Users/me/Library/CloudStorage/Drive/repo")))
        self.assertFalse(guard.is_icloud_path(Path("/Users/me/src/repo")))

    def test_resolves_submodule_git_pointer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            worktree, git_dir = make_git_fixture(Path(tmp), pointer=True)
            self.assertEqual(guard.resolve_git_dir(worktree), git_dir.resolve())

    def test_dataless_pack_blocks_git_commands_without_reading_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            worktree, git_dir = make_git_fixture(Path(tmp))
            pack = git_dir / "objects" / "pack" / "pack-test.pack"
            report = guard.inspect_repository(
                worktree,
                flag_reader=lambda path: {"hidden", "compressed", "dataless"}
                if path.resolve() == pack.resolve()
                else set(),
            )
            self.assertEqual(report["status"], "materialization_required")
            self.assertFalse(report["git_commands_safe"])
            self.assertIn(
                "icloud_item_not_materialized",
                {finding["code"] for finding in report["findings"]},
            )

    def test_invalid_pack_magic_is_integrity_failure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            worktree, git_dir = make_git_fixture(Path(tmp))
            (git_dir / "objects" / "pack" / "pack-test.pack").write_bytes(b"BAD!")
            report = guard.inspect_repository(worktree, flag_reader=lambda _: set())
            self.assertEqual(report["status"], "invalid_git_data")
            self.assertFalse(report["git_commands_safe"])
            self.assertIn("invalid_pack_header", {row["code"] for row in report["findings"]})

    def test_healthy_fixture_is_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            worktree, git_dir = make_git_fixture(Path(tmp), pointer=True)
            report = guard.inspect_repository(worktree, flag_reader=lambda _: set())
            self.assertEqual(report["status"], "ready")
            self.assertTrue(report["git_commands_safe"])
            self.assertEqual(Path(report["git_dir"]), git_dir.resolve())

    def test_materialize_defaults_to_plan_only(self) -> None:
        calls: list[list[str]] = []
        paths = [Path("/tmp/a.pack")]
        result = guard.materialize_paths(
            paths,
            tool="/usr/bin/fileproviderctl",
            apply=False,
            runner=lambda command, timeout: calls.append(command),
        )
        self.assertEqual(calls, [])
        self.assertEqual(result[0]["command"], ["/usr/bin/fileproviderctl", "materialize", "/tmp/a.pack"])
        self.assertEqual(result[0]["status"], "planned")

    def test_materialization_plan_collapses_git_objects_by_default(self) -> None:
        report = {
            "git_dir": "/tmp/repo/.git",
            "findings": [
                {
                    "code": "icloud_item_not_materialized",
                    "path": "/tmp/repo/.git/objects/aa/object-one",
                },
                {
                    "code": "icloud_item_not_materialized",
                    "path": "/tmp/repo/.git/objects/pack/pack-one.pack",
                },
            ],
        }
        self.assertEqual(
            guard.materialization_paths(report),
            [Path("/tmp/repo/.git/objects")],
        )
        self.assertEqual(
            guard.materialization_paths(report, exact=True),
            [
                Path("/tmp/repo/.git/objects/aa/object-one"),
                Path("/tmp/repo/.git/objects/pack/pack-one.pack"),
            ],
        )

    def test_detects_when_fileproviderctl_removed_materialize_command(self) -> None:
        class Result:
            returncode = 64
            stdout = ""
            stderr = "Commands:\n  dump\n  evaluate\n  check | repair\n"

        self.assertFalse(
            guard.fileprovider_supports_materialize(
                "/usr/bin/fileproviderctl",
                runner=lambda command: Result(),
            )
        )

    def test_detects_legacy_fileproviderctl_materialize_command(self) -> None:
        class Result:
            returncode = 0
            stdout = "materialize <item>  Causes the specified item to be written on disk"
            stderr = ""

        self.assertTrue(
            guard.fileprovider_supports_materialize(
                "/usr/bin/fileproviderctl",
                runner=lambda command: Result(),
            )
        )

    def test_verify_refuses_to_run_git_when_preflight_blocks(self) -> None:
        calls: list[list[str]] = []
        report = {
            "status": "materialization_required",
            "git_commands_safe": False,
            "repo": "/tmp/repo",
        }
        result = guard.verify_repository(
            report,
            timeout=1,
            runner=lambda command, cwd, timeout: calls.append(command),
        )
        self.assertEqual(calls, [])
        self.assertEqual(result["status"], "preflight_blocked")

    def test_cli_inspect_json_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            worktree, _ = make_git_fixture(Path(tmp))
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "icloud_git_guard.py"),
                    "inspect",
                    "--repo",
                    str(worktree),
                    "--json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            payload = json.loads(completed.stdout)
            self.assertEqual(payload["schema_version"], 1)
            self.assertEqual(payload["status"], "ready")


if __name__ == "__main__":
    unittest.main()
