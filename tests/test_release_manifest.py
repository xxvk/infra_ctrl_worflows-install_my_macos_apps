from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import release_manifest  # noqa: E402


PASSED_RELEASE = {
    "schema_version": 1,
    "status": "passed",
    "mode": "hermetic",
    "checks_run": 2,
    "results": [
        {"id": "schemas", "status": "passed", "returncode": 0, "command": ["fixture"]},
        {"id": "tests", "status": "passed", "returncode": 0, "command": ["fixture"]},
    ],
}

PASSED_BENCHMARK = {
    "schema_version": 1,
    "kind": "performance_benchmark",
    "comparison": {"status": "passed", "baseline_present": False, "violations": []},
    "operations": {
        "inventory": {
            "summary": {
                "cold_elapsed_ms": 100,
                "warm_elapsed_ms": 80,
                "peak_rss_bytes": 1024,
                "output_bytes": 200,
                "state_growth_bytes": 300,
            }
        }
    },
}


def git_runner(*, dirty: bool = False):
    def run(command, **_kwargs):
        command = [str(item) for item in command]
        if command[-2:] == ["rev-parse", "HEAD"]:
            return subprocess.CompletedProcess(command, 0, "a" * 40 + "\n", "")
        if command[-3:] == ["status", "--porcelain", "--untracked-files=all"]:
            return subprocess.CompletedProcess(command, 0, " M README.md\n" if dirty else "", "")
        raise AssertionError(f"unexpected command: {command}")

    return run


class ReleaseManifestTests(unittest.TestCase):
    def test_repository_definition_is_valid(self) -> None:
        result = release_manifest.validate_definition()
        self.assertEqual(result["status"], "passed", result["errors"])

    def test_release_status_tracks_the_current_version_section(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "references").mkdir()
            (root / "VERSION").write_text("0.2.0\n", encoding="utf-8")
            (root / "references" / "release-roadmap.md").write_text(
                "## 0.1.0 — old\n\nStatus: **shipped**\n\n"
                "## 0.2.0 — current\n\nStatus: **release_candidate**\n",
                encoding="utf-8",
            )
            self.assertEqual(release_manifest.release_status(root=root), "release_candidate")

    def test_manifest_binds_required_evidence_without_publication_authority(self) -> None:
        manifest = release_manifest.build_manifest(
            runner=git_runner(),
            release_result=PASSED_RELEASE,
            benchmark=PASSED_BENCHMARK,
        )
        self.assertEqual(manifest["candidate"]["version"], "0.2.0")
        self.assertEqual(manifest["source"]["commit"], "a" * 40)
        self.assertEqual(manifest["source"]["worktree"], "clean")
        self.assertTrue(manifest["schemas"])
        self.assertTrue(manifest["public_inputs"])
        self.assertEqual(manifest["validation"]["status"], "passed")
        self.assertEqual(manifest["benchmark"]["status"], "passed")
        self.assertEqual(manifest["status"], "candidate")
        self.assertFalse(manifest["authority"]["commit_authorized"])
        self.assertFalse(manifest["authority"]["tag_authorized"])
        self.assertFalse(manifest["authority"]["push_authorized"])
        self.assertFalse(manifest["authority"]["release_authorized"])
        self.assertFalse(manifest["authority"]["visibility_change_authorized"])
        self.assertNotIn("generated_at", manifest)

    def test_dirty_source_is_review_required_and_deterministic(self) -> None:
        first = release_manifest.build_manifest(
            runner=git_runner(dirty=True),
            release_result=PASSED_RELEASE,
            benchmark=PASSED_BENCHMARK,
        )
        second = release_manifest.build_manifest(
            runner=git_runner(dirty=True),
            release_result=PASSED_RELEASE,
            benchmark=PASSED_BENCHMARK,
        )
        self.assertEqual(first, second)
        self.assertEqual(first["status"], "review_required")
        self.assertIn("dirty_worktree", first["blockers"])

    def test_preview_writes_nothing_and_contains_no_private_overlay(self) -> None:
        manifest = release_manifest.build_manifest(
            runner=git_runner(),
            release_result=PASSED_RELEASE,
            benchmark=None,
        )
        serialized = json.dumps(manifest)
        self.assertNotIn("Private/", serialized)
        self.assertNotIn("/Users/", serialized)
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "release-manifest.json"
            result = release_manifest.preview(manifest, output=destination)
            self.assertFalse(destination.exists())
        self.assertFalse(result["write_authorized"])
        self.assertFalse(result["publication_authorized"])


if __name__ == "__main__":
    unittest.main()
