#!/usr/bin/env python3
"""Hermetic contracts for macomrade's remembered storage lifecycle."""

from __future__ import annotations

import datetime as dt
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import schema_contract  # noqa: E402
import storage_lifecycle as storage  # noqa: E402


MIB = 1024**2
GIB = 1024**3


class StorageLifecycleTests(unittest.TestCase):
    def candidate(self, **overrides: object) -> dict[str, object]:
        value: dict[str, object] = {
            "id": "candidate-fixture",
            "path": "~/Downloads/archive.zip",
            "path_hash": "a" * 64,
            "kind": "user_item",
            "logical_bytes": 2 * GIB,
            "allocated_bytes": 2 * GIB,
            "estimated_reclaimable_bytes": 2 * GIB,
            "file_count": 1,
            "confidence": "high",
            "risk": "reversible",
            "action_class": "trash",
            "eligible": True,
            "fingerprint": "b" * 64,
            "cloud": {
                "provider": "none",
                "is_ubiquitous": False,
                "is_uploaded": None,
                "is_uploading": None,
                "has_unresolved_conflicts": None,
                "downloading_status": None,
                "is_dataless": False,
            },
            "reasons": ["allocated_threshold"],
        }
        value.update(overrides)
        return value

    def test_registered_storage_examples_validate(self) -> None:
        result = schema_contract.validate_tracked()
        self.assertEqual(result["status"], "passed", result["errors"])
        kinds = {row["kind"] for row in result["results"]}
        self.assertTrue(
            {
                "storage-policy",
                "storage-scan",
                "storage-decision-ledger",
                "storage-plan",
                "storage-transaction",
            }.issubset(kinds)
        )

    def test_public_policy_and_private_intent_merge_without_authorization(self) -> None:
        public = {
            "schema_version": 1,
            "kind": "storage_policy",
            "role_targets_bytes": {"compact": 50 * GIB, "expanded": 100 * GIB},
            "default_role": "compact",
            "private_overridable": ["target_free_bytes", "path_rules", "archive_targets"],
            "execution_authorized": False,
            "path_rules": [{"pattern": "~/Library/Caches/*", "decision": "safe_cache"}],
            "archive_targets": [],
        }
        private = {
            "schema_version": 1,
            "kind": "storage_private_policy",
            "target_free_bytes": 75 * GIB,
            "path_rules": [{"pattern": "~/Movies/*", "decision": "archive"}],
            "archive_targets": [{"id": "vault", "path": "/Volumes/Vault"}],
            "execution_authorized": True,
        }
        merged = storage.merge_policy(public, private)
        self.assertEqual(merged["target_free_bytes"], 75 * GIB)
        self.assertFalse(merged["execution_authorized"])
        self.assertEqual(merged["path_rules"][0]["decision"], "archive")
        self.assertEqual(merged["path_rules"][1]["decision"], "safe_cache")

    def test_scan_deduplicates_hardlinks_and_never_follows_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = root / "payload"
            payload.write_bytes(b"x" * 8192)
            os.link(payload, root / "hardlink")
            outside = root.parent / f"{root.name}-outside"
            outside.write_bytes(b"y" * 16384)
            try:
                (root / "link").symlink_to(outside)
                metrics = storage.scan_path(root, cross_filesystems=False)
            finally:
                outside.unlink(missing_ok=True)
        self.assertEqual(metrics["file_count"], 1)
        self.assertGreaterEqual(metrics["logical_bytes"], 8192)
        self.assertLess(metrics["logical_bytes"], 16384)
        self.assertEqual(metrics["hardlink_duplicates"], 1)
        self.assertEqual(metrics["symlink_count"], 1)

    def test_sparse_file_keeps_logical_and_allocated_bytes_distinct(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sparse.img"
            with path.open("wb") as handle:
                handle.seek(64 * MIB - 1)
                handle.write(b"\0")
            metrics = storage.scan_path(path)
        self.assertEqual(metrics["logical_bytes"], 64 * MIB)
        self.assertLess(metrics["allocated_bytes"], metrics["logical_bytes"])

    def test_public_policy_allowlists_mole_scan_cache_with_regeneration_proof(self) -> None:
        policy = storage.load_policy(public_only=True)
        path = Path.home() / ".cache" / "mole"
        metrics = {
            "logical_bytes": 200 * MIB,
            "allocated_bytes": 200 * MIB,
            "file_count": 1000,
            "device": 1,
            "inode": 2,
            "volume": "1",
            "latest_mtime_ns": 3,
            "git_repository_count": 0,
            "clone_exclusive_unknown": True,
        }
        candidate = storage.classify_candidate(
            path=path,
            metrics=metrics,
            cloud=storage.default_cloud_metadata(),
            policy=policy,
        )
        self.assertEqual(candidate["action_class"], "safe_cache")
        self.assertTrue(candidate["eligible"])
        self.assertIn("Mole", candidate["regeneration_proof"])

    def test_git_ignored_artifact_requires_rebuild_marker_and_no_active_project_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            (repo / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
            (repo / "package-lock.json").write_text("{}\n", encoding="utf-8")
            artifact = repo / "node_modules"
            artifact.mkdir()
            (artifact / "package.bin").write_bytes(b"x" * 4096)
            policy = storage.default_policy_for_tests()
            policy["candidate_thresholds"]["allocated_bytes"] = 1

            ready = storage.discover_developer_artifacts(repo, policy=policy, active_cwds=set())
            blocked = storage.discover_developer_artifacts(repo, policy=policy, active_cwds={repo})

        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0]["kind"], "developer_artifact")
        self.assertEqual(ready[0]["action_class"], "safe_cache")
        self.assertTrue(ready[0]["eligible"])
        self.assertTrue(ready[0]["git_ignored"])
        self.assertEqual(ready[0]["tracked_file_count"], 0)
        self.assertTrue(ready[0]["rebuild_marker"].endswith("package-lock.json"))
        self.assertEqual(len(blocked), 1)
        self.assertFalse(blocked[0]["eligible"])
        self.assertIn("active_project_working_directory", blocked[0]["reasons"])

    def test_git_artifact_apply_recheck_fails_when_project_becomes_active(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            (repo / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
            (repo / "package-lock.json").write_text("{}\n", encoding="utf-8")
            artifact = repo / "node_modules"
            artifact.mkdir()
            (artifact / "package.bin").write_bytes(b"x" * 4096)
            policy = storage.default_policy_for_tests()
            policy["candidate_thresholds"]["allocated_bytes"] = 1
            candidate = storage.discover_developer_artifacts(
                repo,
                policy=policy,
                active_cwds=set(),
            )[0]
            backend = storage.LocalActionBackend(Path(tmp) / "state", policy)

            with mock.patch.object(storage, "active_process_working_directories", return_value={repo}):
                self.assertFalse(backend.verify_candidate(candidate))

    def test_inaccessible_child_is_recorded_not_treated_as_empty_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            child = root / "blocked"
            child.write_text("fixture")
            original = Path.lstat

            def lstat(value):
                if value == child:
                    raise PermissionError("fixture denied")
                return original(value)

            with mock.patch.object(Path, "lstat", lstat):
                metrics = storage.scan_path(root)
        self.assertEqual(metrics["inaccessible_count"], 1)

    def test_third_party_file_provider_is_read_only_handoff(self) -> None:
        candidate = storage.classify_candidate(
            path=Path.home() / "Library" / "CloudStorage" / "Drive" / "large.bin",
            metrics={"logical_bytes": 2 * GIB, "allocated_bytes": 2 * GIB, "file_count": 1, "latest_mtime_ns": 1, "device": 1, "inode": 2, "volume": "fixture", "clone_exclusive_unknown": False},
            cloud={"provider": "google_drive", "is_ubiquitous": False, "is_dataless": False},
            policy=storage.default_policy_for_tests(),
        )
        self.assertFalse(candidate["eligible"])
        self.assertEqual(candidate["action_class"], "provider_ui")
        self.assertEqual(candidate["estimated_reclaimable_bytes"], 0)

    def test_clone_unknown_lowers_high_confidence(self) -> None:
        policy = storage.default_policy_for_tests()
        policy["path_rules"] = [{"pattern": "~/Library/Caches/Fixture*", "decision": "safe_cache", "kind": "developer_cache", "regeneration_proof": "fixture"}]
        candidate = storage.classify_candidate(
            path=Path.home() / "Library" / "Caches" / "Fixture",
            metrics={"logical_bytes": 2 * GIB, "allocated_bytes": 2 * GIB, "file_count": 1, "latest_mtime_ns": 1, "device": 1, "inode": 2, "volume": "fixture", "clone_exclusive_unknown": True},
            cloud=storage.default_cloud_metadata(),
            policy=policy,
        )
        self.assertEqual(candidate["confidence"], "high")
        self.assertEqual(candidate["reclaim_confidence"], "medium")
        self.assertIn("apfs_clone_exclusive_bytes_unknown", candidate["reasons"])

    def test_unreviewed_user_items_are_proposals_not_executable_actions(self) -> None:
        metrics = {
            "logical_bytes": 2 * GIB,
            "allocated_bytes": 2 * GIB,
            "file_count": 1,
            "latest_mtime_ns": 1,
            "device": 1,
            "inode": 2,
            "volume": "fixture",
            "clone_exclusive_unknown": False,
        }
        local = storage.classify_candidate(
            path=Path.home() / "Downloads" / "unreviewed.zip",
            metrics=metrics,
            cloud=storage.default_cloud_metadata(),
            policy=storage.default_policy_for_tests(),
        )
        cloud = storage.classify_candidate(
            path=Path.home() / "Desktop" / "unreviewed-cloud-folder",
            metrics=metrics,
            cloud={
                "provider": "icloud",
                "is_ubiquitous": True,
                "is_uploaded": True,
                "is_uploading": False,
                "is_downloading": False,
                "has_unresolved_conflicts": False,
                "downloading_status": "current",
                "is_dataless": False,
            },
            policy=storage.default_policy_for_tests(),
        )
        self.assertEqual(local["action_class"], "review")
        self.assertEqual(local["proposed_action_class"], "trash")
        self.assertFalse(local["eligible"])
        self.assertEqual(local["estimated_reclaimable_bytes"], 0)
        self.assertEqual(cloud["action_class"], "review")
        self.assertEqual(cloud["proposed_action_class"], "icloud_offload")
        self.assertFalse(cloud["eligible"])

    def test_app_managed_photo_library_is_always_protected(self) -> None:
        policy = storage.default_policy_for_tests()
        policy["path_rules"] = [{"pattern": "~/Pictures/*", "decision": "archive"}]
        candidate = storage.classify_candidate(
            path=Path.home() / "Pictures" / "Photos Library.photoslibrary",
            metrics={
                "logical_bytes": 3 * GIB,
                "allocated_bytes": 3 * GIB,
                "file_count": 100,
                "latest_mtime_ns": 1,
                "device": 1,
                "inode": 2,
                "volume": "fixture",
                "clone_exclusive_unknown": False,
            },
            cloud=storage.default_cloud_metadata(),
            policy=policy,
        )
        self.assertEqual(candidate["kind"], "app_managed_library")
        self.assertEqual(candidate["action_class"], "review")
        self.assertFalse(candidate["eligible"])
        self.assertEqual(candidate["estimated_reclaimable_bytes"], 0)
        self.assertIn("protected_app_managed_library", candidate["reasons"])

    def test_tree_containing_git_repository_is_always_protected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "source"
            marker = root / "project" / ".git"
            marker.mkdir(parents=True)
            (marker / "HEAD").write_text("ref: refs/heads/main\n")
            payload = root / "payload.bin"
            payload.write_bytes(b"fixture")
            metrics = storage.scan_path(root)
            policy = storage.default_policy_for_tests()
            policy["path_rules"] = [{"pattern": str(root), "decision": "archive"}]
            candidate = storage.classify_candidate(
                path=root,
                metrics={**metrics, "logical_bytes": 2 * GIB, "allocated_bytes": 2 * GIB},
                cloud=storage.default_cloud_metadata(),
                policy=policy,
            )
        self.assertEqual(metrics["git_repository_count"], 1)
        self.assertEqual(candidate["action_class"], "review")
        self.assertFalse(candidate["eligible"])
        self.assertEqual(candidate["estimated_reclaimable_bytes"], 0)
        self.assertIn("contains_git_repository", candidate["reasons"])

    def test_application_support_remains_aggregate_with_nested_git_repository(self) -> None:
        policy = storage.default_policy_for_tests()
        policy["path_rules"] = [
            {
                "pattern": "~/Library/Application Support*",
                "kind": "app_support_aggregate",
                "decision": "protected",
            }
        ]
        candidate = storage.classify_candidate(
            path=Path.home() / "Library" / "Application Support",
            metrics={
                "logical_bytes": 10 * GIB,
                "allocated_bytes": 10 * GIB,
                "file_count": 100,
                "latest_mtime_ns": 1,
                "device": 1,
                "inode": 2,
                "volume": "fixture",
                "git_repository_count": 3,
                "clone_exclusive_unknown": False,
            },
            cloud=storage.default_cloud_metadata(),
            policy=policy,
        )
        self.assertEqual(candidate["kind"], "app_support_aggregate")
        self.assertFalse(candidate["eligible"])
        self.assertEqual(candidate["action_class"], "review")
        self.assertIn("protected_or_app_specific", candidate["reasons"])

    def test_reviewed_rules_promote_cloud_and_file_actions_without_authorizing_execution(self) -> None:
        metrics = {
            "logical_bytes": 2 * GIB,
            "allocated_bytes": 2 * GIB,
            "file_count": 1,
            "latest_mtime_ns": 1,
            "device": 1,
            "inode": 2,
            "volume": "fixture",
            "git_repository_count": 0,
            "clone_exclusive_unknown": False,
        }
        policy = storage.default_policy_for_tests()
        policy["path_rules"] = [
            {"pattern": "~/Desktop/reviewed-cloud", "decision": "cloud_on_demand"},
            {"pattern": "~/Downloads/reviewed-file", "decision": "delete_after_backup"},
        ]
        cloud = storage.classify_candidate(
            path=Path.home() / "Desktop" / "reviewed-cloud",
            metrics=metrics,
            cloud={
                "provider": "icloud",
                "is_ubiquitous": True,
                "is_uploaded": True,
                "is_uploading": False,
                "is_downloading": False,
                "has_unresolved_conflicts": False,
                "downloading_status": "current",
                "is_dataless": False,
            },
            policy=policy,
        )
        local = storage.classify_candidate(
            path=Path.home() / "Downloads" / "reviewed-file",
            metrics=metrics,
            cloud=storage.default_cloud_metadata(),
            policy=policy,
        )
        self.assertTrue(cloud["eligible"])
        self.assertEqual(cloud["action_class"], "icloud_offload")
        self.assertTrue(local["eligible"])
        self.assertEqual(local["action_class"], "trash")
        self.assertFalse(policy["execution_authorized"])

    def test_deep_scan_expands_review_only_root_and_retains_review_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            child = root / "child"
            child.mkdir(parents=True)
            metrics = {
                "logical_bytes": 2 * GIB,
                "allocated_bytes": 2 * GIB,
                "file_count": 1,
                "latest_mtime_ns": 1,
                "device": 1,
                "inode": 2,
                "volume": "fixture",
                "hardlink_duplicates": 0,
                "symlink_count": 0,
                "inaccessible_count": 0,
                "cross_device_skipped": 0,
                "git_repository_count": 0,
                "clone_exclusive_unknown": False,
            }
            with mock.patch.object(storage, "scan_path", return_value=metrics):
                result = storage.build_scan(
                    policy=storage.default_policy_for_tests(),
                    mode="deep",
                    roots=[root],
                    disk_usage=lambda _path: storage.shutil._ntuple_diskusage(256 * GIB, 128 * GIB, 128 * GIB),
                )
        self.assertTrue(result["roots"][0]["expanded"])
        self.assertEqual(len(result["candidates"]), 1)
        self.assertEqual(result["candidates"][0]["action_class"], "review")
        self.assertFalse(result["candidates"][0]["eligible"])

    def test_volatile_volume_free_space_does_not_stale_candidate_fingerprint(self) -> None:
        metrics = {"logical_bytes": 2 * GIB, "allocated_bytes": 2 * GIB, "file_count": 1, "latest_mtime_ns": 1, "device": 1, "inode": 2, "volume": "fixture", "clone_exclusive_unknown": False}
        cloud = {"provider": "icloud", "is_ubiquitous": True, "is_uploaded": True, "is_uploading": False, "is_downloading": False, "has_unresolved_conflicts": False, "downloading_status": "current", "is_dataless": False, "resource_identifier": "fixture", "volume_uuid": "volume", "volume_available_bytes": 10 * GIB}
        first = storage.classify_candidate(path=Path.home() / "Desktop" / "fixture", metrics=metrics, cloud=cloud, policy=storage.default_policy_for_tests())
        second = storage.classify_candidate(path=Path.home() / "Desktop" / "fixture", metrics=metrics, cloud={**cloud, "volume_available_bytes": 20 * GIB}, policy=storage.default_policy_for_tests())
        self.assertEqual(first["fingerprint"], second["fingerprint"])

    def test_dataless_cloud_item_is_not_read_or_high_value_reclaim(self) -> None:
        candidate = storage.classify_candidate(
            path=Path.home() / "Desktop" / "cloud-project",
            metrics={
                "logical_bytes": 3 * GIB,
                "allocated_bytes": 512 * 1024,
                "file_count": 50,
                "latest_mtime_ns": 1,
                "device": 1,
                "inode": 2,
                "volume": "fixture",
                "hardlink_duplicates": 0,
                "symlink_count": 0,
                "inaccessible_count": 0,
                "cross_device_skipped": 0,
                "clone_exclusive_unknown": True,
            },
            cloud={
                "provider": "icloud",
                "is_ubiquitous": True,
                "is_uploaded": True,
                "is_uploading": False,
                "has_unresolved_conflicts": False,
                "downloading_status": "notDownloaded",
                "is_dataless": True,
            },
            policy=storage.default_policy_for_tests(),
        )
        self.assertEqual(candidate["allocated_bytes"], 512 * 1024)
        self.assertEqual(candidate["estimated_reclaimable_bytes"], 0)
        self.assertFalse(candidate["eligible"])
        self.assertIn("cloud_placeholder_low_local_allocation", candidate["reasons"])

    def test_sanitized_known_icloud_samples_are_not_reclaim_targets(self) -> None:
        for logical, allocated in ((3194806686, 876544), (2496489148, 970752)):
            with self.subTest(logical=logical):
                candidate = storage.classify_candidate(
                    path=Path.home() / "Desktop" / "sample",
                    metrics={"logical_bytes": logical, "allocated_bytes": allocated, "file_count": 25000, "latest_mtime_ns": 1, "device": 1, "inode": logical, "volume": "fixture", "clone_exclusive_unknown": True},
                    cloud={"provider": "icloud", "is_ubiquitous": True, "is_uploaded": True, "is_uploading": False, "is_downloading": False, "has_unresolved_conflicts": False, "downloading_status": "current", "is_dataless": False},
                    policy=storage.default_policy_for_tests(),
                )
                self.assertLess(candidate["allocated_bytes"], MIB)
                self.assertEqual(candidate["estimated_reclaimable_bytes"], 0)
                self.assertFalse(candidate["eligible"])

    def test_decision_expiry_and_materialization_rules(self) -> None:
        now = dt.datetime(2026, 8, 14, tzinfo=dt.timezone.utc)
        candidate = self.candidate()
        keep = storage.decision_effect(
            candidate,
            {"decision": "keep_local", "decided_at": "2026-08-01T00:00:00+00:00", "fingerprint": candidate["fingerprint"]},
            now=now,
        )
        self.assertTrue(keep["suppress"])
        stale_cache = storage.decision_effect(
            candidate,
            {"decision": "safe_cache", "decided_at": "2026-07-01T00:00:00+00:00", "fingerprint": candidate["fingerprint"]},
            now=now,
        )
        self.assertFalse(stale_cache["suppress"])
        rematerialized = storage.decision_effect(
            dict(candidate, allocated_bytes=2 * GIB, fingerprint="c" * 64),
            {"decision": "cloud_on_demand", "decided_at": "2026-08-13T00:00:00+00:00", "fingerprint": candidate["fingerprint"]},
            now=now,
        )
        self.assertFalse(rematerialized["suppress"])

    def test_review_after_requires_date(self) -> None:
        with self.assertRaisesRegex(storage.StorageError, "review_after"):
            storage.build_decision(self.candidate(), "review_after", review_after=None)

    def test_reviewed_delete_promotes_unprotected_candidate_to_trash(self) -> None:
        candidate = self.candidate(
            id="reviewed-trash",
            action_class="review",
            risk="review",
            eligible=False,
            estimated_reclaimable_bytes=0,
            potential_reclaimable_bytes=3 * GIB,
        )
        decision = storage.build_decision(candidate, "delete_after_backup")
        plan = storage.build_plan(
            storage.scan_fixture(free_bytes=10 * GIB, candidates=[candidate]),
            storage.default_policy_for_tests(),
            decisions=[decision],
            target="auto",
        )
        self.assertEqual(plan["minimum_action_set"][0]["action_class"], "trash")
        self.assertEqual(plan["estimated_reclaimable_bytes"], 3 * GIB)

    def test_reviewed_delete_cannot_override_app_support_protection(self) -> None:
        candidate = self.candidate(
            id="protected-app-data",
            kind="app_support_aggregate",
            action_class="review",
            risk="review",
            eligible=False,
            estimated_reclaimable_bytes=0,
            potential_reclaimable_bytes=3 * GIB,
        )
        decision = storage.build_decision(candidate, "delete_after_backup")
        plan = storage.build_plan(
            storage.scan_fixture(free_bytes=10 * GIB, candidates=[candidate]),
            storage.default_policy_for_tests(),
            decisions=[decision],
            target="auto",
        )
        self.assertEqual(plan["minimum_action_set"], [])

    def test_changed_candidate_requires_a_fresh_review(self) -> None:
        candidate = self.candidate(
            id="changed-item",
            action_class="review",
            risk="review",
            eligible=False,
            estimated_reclaimable_bytes=0,
            potential_reclaimable_bytes=3 * GIB,
        )
        decision = storage.build_decision(candidate, "delete_after_backup")
        changed = dict(candidate, fingerprint="changed-fingerprint")
        plan = storage.build_plan(
            storage.scan_fixture(free_bytes=10 * GIB, candidates=[changed]),
            storage.default_policy_for_tests(),
            decisions=[decision],
            target="auto",
        )
        self.assertEqual(plan["minimum_action_set"], [])

    def test_planner_separates_curves_and_stops_at_minimum_set(self) -> None:
        scan = storage.scan_fixture(
            free_bytes=45 * GIB,
            candidates=[
                self.candidate(id="cache", action_class="safe_cache", risk="low", estimated_reclaimable_bytes=3 * GIB, regeneration_proof="fixture proof"),
                self.candidate(id="icloud", action_class="icloud_offload", risk="low", estimated_reclaimable_bytes=4 * GIB),
                self.candidate(id="trash", action_class="trash", risk="reversible", estimated_reclaimable_bytes=10 * GIB),
            ],
        )
        plan = storage.build_plan(scan, storage.default_policy_for_tests(), decisions=[], target="auto")
        self.assertEqual(plan["target_free_bytes"], 50 * GIB)
        self.assertEqual([row["candidate_id"] for row in plan["minimum_action_set"]], ["cache", "icloud"])
        self.assertEqual(plan["estimated_reclaimable_bytes"], 7 * GIB)
        self.assertEqual(plan["staged_bytes"], 0)
        self.assertNotIn("measured_reclaimed_bytes", plan)

    def test_target_parser_supports_relative_and_absolute_human_units(self) -> None:
        scan = storage.scan_fixture(free_bytes=65 * GIB, candidates=[])
        policy = storage.default_policy_for_tests()

        relative = storage.build_plan(scan, policy, decisions=[], target="+10GiB")
        absolute = storage.build_plan(scan, policy, decisions=[], target="80GiB")
        decimal = storage.build_plan(scan, policy, decisions=[], target="80GB")

        self.assertEqual(relative["target_free_bytes"], 75 * GIB)
        self.assertEqual(relative["target_request"], "+10GiB")
        self.assertEqual(relative["target_mode"], "relative")
        self.assertEqual(absolute["target_free_bytes"], 80 * GIB)
        self.assertEqual(absolute["target_mode"], "absolute")
        self.assertEqual(decimal["target_free_bytes"], 80_000_000_000)
        with self.assertRaisesRegex(storage.StorageError, "target"):
            storage.build_plan(scan, policy, decisions=[], target="ten gigs")

    def test_apfs_snapshot_and_swap_parsers_create_read_only_system_facts(self) -> None:
        apfs = storage.parse_apfs_inventory(
            {
                "Containers": [
                    {
                        "CapacityCeiling": 256 * GIB,
                        "CapacityFree": 70 * GIB,
                        "Volumes": [
                            {"Roles": ["System"], "CapacityInUse": 12 * GIB},
                            {"Roles": ["Data"], "CapacityInUse": 130 * GIB},
                            {"Roles": ["VM"], "CapacityInUse": 9 * GIB},
                        ],
                    }
                ]
            }
        )
        snapshots = storage.parse_apfs_snapshots(
            {"Snapshots": [{"SnapshotName": "com.apple.os.update-fixture", "Purgeable": False, "LimitingContainerShrink": True}]}
        )
        swap = storage.parse_swapusage("vm.swapusage: total = 8192.00M used = 6839.25M free = 1352.75M (encrypted)")

        self.assertEqual(apfs["capacity_bytes"], 256 * GIB)
        self.assertEqual(apfs["volumes"][2]["roles"], ["VM"])
        self.assertFalse(apfs["volumes"][2]["eligible"])
        self.assertEqual(snapshots["items"][0]["kind"], "os_update")
        self.assertFalse(snapshots["items"][0]["eligible"])
        self.assertEqual(swap["used_bytes"], int(6839.25 * MIB))
        self.assertEqual(swap["durability"], "transient")

    def test_private_tmp_and_optional_apps_are_manual_handoffs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            temp_tree = root / "dependency-audit.fixture"
            temp_tree.mkdir()
            (temp_tree / "payload").write_bytes(b"x" * 8192)
            app = root / "Optional Fixture.app"
            app.mkdir()
            (app / "payload").write_bytes(b"x" * 8192)
            metrics = {
                "logical_bytes": 2 * GIB,
                "allocated_bytes": 2 * GIB,
                "file_count": 1,
                "latest_mtime_ns": 1,
                "device": 1,
                "inode": 2,
                "volume": "fixture",
                "hardlink_duplicates": 0,
                "symlink_count": 0,
                "inaccessible_count": 0,
                "git_repository_count": 0,
                "clone_exclusive_unknown": False,
            }
            tmp_rows = storage.discover_private_tmp_handoffs(
                root,
                threshold_bytes=GIB,
                metrics_for_path=lambda _path: metrics,
            )
            app_rows = storage.discover_optional_app_handoffs(
                {"apps": [{"name": "Optional Fixture", "tier": "optional", "lifecycle_status": "active", "guide": "components/optional-fixture.md"}]},
                [{"name": "Optional Fixture", "catalog_name": "Optional Fixture", "path": str(app)}],
                metrics_for_path=lambda _path: metrics,
            )

        for row in [tmp_rows[0], app_rows[0]]:
            self.assertFalse(row["eligible"])
            self.assertEqual(row["estimated_reclaimable_bytes"], 0)
            self.assertEqual(row["potential_reclaimable_bytes"], 2 * GIB)
            self.assertEqual(row["action_class"], "manual_handoff")

        decision = storage.build_decision(tmp_rows[0], "delete_after_backup")
        plan = storage.build_plan(
            storage.scan_fixture(free_bytes=10 * GIB, candidates=[tmp_rows[0]]),
            storage.default_policy_for_tests(),
            decisions=[decision],
            target="50GiB",
        )
        self.assertEqual(plan["minimum_action_set"], [])

    def test_scan_contract_records_system_facts_without_authorization(self) -> None:
        system_facts = {
            "status": "complete",
            "execution_authorized": False,
            "startup_apfs": {"status": "available", "capacity_bytes": 256 * GIB, "free_bytes": 70 * GIB, "volumes": []},
            "snapshots": {"status": "available", "items": []},
            "vm": {"status": "available", "durability": "transient", "eligible": False},
            "protected_aggregates": [],
            "home_top": [],
            "errors": [],
        }
        result = storage.build_scan(
            policy=storage.default_policy_for_tests(),
            mode="quick",
            roots=[],
            system_facts=system_facts,
            disk_usage=lambda _path: storage.shutil._ntuple_diskusage(256 * GIB, 186 * GIB, 70 * GIB),
        )
        self.assertEqual(result["system_facts"], system_facts)
        self.assertFalse(result["system_facts"]["execution_authorized"])

    def test_deep_home_facts_report_partial_traversal_without_raw_error_text(self) -> None:
        completed = subprocess.CompletedProcess(
            ["du"],
            1,
            stdout="2048\t/Users/fixture/Library\n4096\t/Users/fixture\n",
            stderr="permission denied: secret-path",
        )
        with mock.patch.object(Path, "is_dir", return_value=True), mock.patch.object(
            storage.subprocess, "run", return_value=completed
        ):
            rows, complete = storage._deep_home_top_facts(Path("/Users/fixture"))

        self.assertFalse(complete)
        self.assertEqual(rows[0]["path"], "/Users/fixture/Library")
        self.assertEqual(rows[0]["allocated_bytes"], 2 * MIB)
        self.assertNotIn("secret-path", json.dumps(rows))

    def test_scan_summary_caps_home_evidence_but_full_record_retains_it(self) -> None:
        candidates = [self.candidate(id=f"candidate-{index}") for index in range(30)]
        candidate = candidates[0]
        result = storage.scan_fixture(free_bytes=70 * GIB, candidates=candidates)
        result["system_facts"]["home_top"] = [
            {
                "path": f"~/item-{index}",
                "allocated_bytes": (30 - index) * MIB,
                "authority": "filesystem_allocated_evidence",
                "eligible": False,
                "action_class": "evidence_only",
            }
            for index in range(30)
        ]

        summary = storage.scan_summary(result, Path("/tmp/scan.json"))

        self.assertEqual(len(result["system_facts"]["home_top"]), 30)
        self.assertEqual(len(summary["system_facts"]["home_top"]), 20)
        self.assertEqual(summary["system_facts"]["omitted_home_top_count"], 10)
        self.assertEqual(summary["candidates"][0]["id"], candidate["id"])
        self.assertEqual(summary["candidates"][0]["allocated_bytes"], 2 * GIB)
        self.assertNotIn("cloud", summary["candidates"][0])
        self.assertNotIn("fingerprint", summary["candidates"][0])
        self.assertEqual(len(summary["candidates"]), 20)
        self.assertEqual(summary["omitted_candidate_count"], 10)

    def test_stale_plan_and_wrong_confirmation_fail_before_backend(self) -> None:
        backend = storage.FakeActionBackend()
        plan = storage.plan_fixture([self.candidate(action_class="safe_cache")])
        plan["plan_sha256"] = "0" * 64
        with self.assertRaisesRegex(storage.StorageError, "plan hash"):
            storage.apply_plan(plan, action_class="safe_cache", confirmation="PURGE APPROVED REGENERABLE CACHES", backend=backend)
        self.assertEqual(backend.calls, [])

        plan = storage.freeze_plan(storage.plan_fixture([self.candidate(action_class="safe_cache")]))
        with self.assertRaisesRegex(storage.StorageError, "confirmation"):
            storage.apply_plan(plan, action_class="safe_cache", confirmation="wrong", backend=backend)
        self.assertEqual(backend.calls, [])

    def test_apply_cli_previews_without_confirmation_or_writes(self) -> None:
        plan = storage.freeze_plan(storage.plan_fixture([self.candidate(action_class="trash")]))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plan.json"
            path.write_text(json.dumps(plan), encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                code = storage.main(["apply", str(path), "--action-class", "trash", "--state-dir", str(Path(tmp) / "state")])
            result = json.loads(output.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "dry_run")
        self.assertEqual(result["required_confirmation"], "MOVE STORAGE ITEMS TO TRASH")
        self.assertFalse(result["writes"])

    def test_icloud_apply_rejects_upload_conflict_and_downloading(self) -> None:
        backend = storage.FakeActionBackend()
        for cloud in (
            {"is_uploaded": False, "is_uploading": False, "has_unresolved_conflicts": False, "downloading_status": "current"},
            {"is_uploaded": True, "is_uploading": False, "has_unresolved_conflicts": True, "downloading_status": "current"},
            {"is_uploaded": True, "is_uploading": False, "has_unresolved_conflicts": False, "downloading_status": "downloading"},
        ):
            value = self.candidate(action_class="icloud_offload", cloud={"provider": "icloud", "is_ubiquitous": True, "is_dataless": False, **cloud})
            plan = storage.freeze_plan(storage.plan_fixture([value]))
            with self.assertRaises(storage.StorageError):
                storage.apply_plan(plan, action_class="icloud_offload", confirmation="REMOVE ICLOUD LOCAL COPIES", backend=backend)
        self.assertEqual(backend.calls, [])

    def test_target_reached_stops_remaining_actions(self) -> None:
        items = [
            self.candidate(id="one", action_class="safe_cache", estimated_reclaimable_bytes=4 * GIB, regeneration_proof="fixture proof"),
            self.candidate(id="two", action_class="safe_cache", estimated_reclaimable_bytes=4 * GIB, regeneration_proof="fixture proof"),
        ]
        plan = storage.freeze_plan(storage.plan_fixture(items, free_bytes=47 * GIB, target_free_bytes=50 * GIB))
        backend = storage.FakeActionBackend(free_bytes=[47 * GIB, 51 * GIB])
        record = storage.apply_plan(plan, action_class="safe_cache", confirmation="PURGE APPROVED REGENERABLE CACHES", backend=backend)
        self.assertEqual(record["status"], "target_reached_replan_required")
        self.assertEqual(len(backend.calls), 1)

    def test_verify_preserves_apply_measurement_instead_of_counting_later_changes(self) -> None:
        source = {
            "schema_version": 1,
            "kind": "storage_apply_record",
            "record_id": "apply-fixture",
            "created_at": "2026-08-14T00:00:00+00:00",
            "plan_id": "plan-fixture",
            "action_id": "storage.cache-purge",
            "status": "applied_replan_required",
            "free_bytes_before": 10 * GIB,
            "free_bytes_after": 12 * GIB,
            "staged_bytes": 0,
            "measured_reclaimed_bytes": 2 * GIB,
            "actions": [{"candidate_id": "cache", "status": "purged"}],
            "replan_required": True,
        }

        result = storage.build_verify_record(source, observed_free_bytes=20 * GIB)

        self.assertEqual(result["free_bytes_before"], 10 * GIB)
        self.assertEqual(result["free_bytes_after"], 12 * GIB)
        self.assertEqual(result["measured_reclaimed_bytes"], 2 * GIB)
        self.assertEqual(result["observed_free_bytes_at_verify"], 20 * GIB)
        self.assertEqual(result["measurement_scope"], "apply_transaction")

    def test_trash_staging_is_not_measured_reclaim_until_bound_purge(self) -> None:
        plan = storage.freeze_plan(storage.plan_fixture([self.candidate(action_class="trash")]))
        backend = storage.FakeActionBackend(free_bytes=[10 * GIB, 10 * GIB])
        record = storage.apply_plan(plan, action_class="trash", confirmation="MOVE STORAGE ITEMS TO TRASH", backend=backend)
        self.assertEqual(record["staged_bytes"], 2 * GIB)
        self.assertEqual(record["measured_reclaimed_bytes"], 0)
        self.assertEqual(len(record["trash_manifest"]), 1)

        purge = storage.purge_manifest(
            record,
            confirmation="PURGE MANIFEST BOUND TRASH ITEMS",
            backend=storage.FakeActionBackend(free_bytes=[10 * GIB, 12 * GIB]),
        )
        self.assertEqual(purge["measured_reclaimed_bytes"], 2 * GIB)

    def test_mole_import_is_idempotent_and_evidence_only(self) -> None:
        payload = {
            "sessions": [{"command": "analyze", "started_at": "2026-08-01T00:00:00Z", "size": 42}],
            "deletions": [{"path": "~/Downloads/a", "size_kb": 12, "timestamp": "2026-08-01T00:00:00Z", "status": "deleted"}],
        }
        first = storage.import_mole_history(payload, existing=[])
        second = storage.import_mole_history(payload, existing=first)
        self.assertEqual(first, second)
        self.assertTrue(all(row["authority"] == "evidence_only" for row in first))
        self.assertTrue(all("decision" not in row for row in first))

    def test_weekly_notification_thresholds_and_low_battery(self) -> None:
        self.assertFalse(storage.should_notify_weekly(free_bytes=40 * GIB, target_free_bytes=50 * GIB, new_high_confidence_bytes=10 * GIB, battery_percent=15, on_ac_power=False, cooldown_active=False))
        self.assertTrue(storage.should_notify_weekly(free_bytes=40 * GIB, target_free_bytes=50 * GIB, new_high_confidence_bytes=0, battery_percent=90, on_ac_power=False, cooldown_active=False))
        self.assertTrue(storage.should_notify_weekly(free_bytes=60 * GIB, target_free_bytes=50 * GIB, new_high_confidence_bytes=5 * GIB, battery_percent=90, on_ac_power=False, cooldown_active=False))
        self.assertFalse(storage.should_notify_weekly(free_bytes=40 * GIB, target_free_bytes=50 * GIB, new_high_confidence_bytes=10 * GIB, battery_percent=90, on_ac_power=False, cooldown_active=True))

    def test_redacted_export_has_aliases_and_hashes_not_raw_paths(self) -> None:
        result = storage.redact_for_export({"path": str(Path.home() / "秘密"), "record": str(Path.home() / "Library" / "record.json")})
        serialized = json.dumps(result, ensure_ascii=False)
        self.assertNotIn(str(Path.home()), serialized)
        self.assertNotIn("秘密", serialized)
        self.assertIn("path_hash", serialized)

    def test_decision_sync_writes_only_non_authorizing_private_intent(self) -> None:
        ledger = {
            "decisions": [
                {"path_pattern": "~/Movies/*", "decision": "archive"},
                {"path_pattern": "~/Downloads/*", "decision": "unknown"},
            ]
        }
        with tempfile.TemporaryDirectory() as tmp:
            destination = Path(tmp) / "storage-policy.json"
            record = storage.sync_decisions(
                ledger,
                confirmation="SYNC STORAGE DECISIONS",
                destination=destination,
                public_policy=storage.default_policy_for_tests(),
            )
            saved = json.loads(destination.read_text())
        self.assertEqual(record["status"], "synced")
        self.assertFalse(saved["execution_authorized"])
        self.assertEqual(saved["path_rules"], [{"pattern": "~/Movies/*", "decision": "archive"}])

    def test_archive_refuses_offline_private_target(self) -> None:
        policy = storage.default_policy_for_tests()
        policy["archive_targets"] = [{"id": "offline", "path": "/Volumes/Definitely Offline Fixture"}]
        backend = storage.LocalActionBackend(Path(tempfile.gettempdir()) / "macomrade-test-state", policy)
        candidate = self.candidate(action_class="archive", archive_target_id="offline")
        with self.assertRaisesRegex(storage.StorageError, "offline"):
            backend._archive(candidate)

    def test_archive_refuses_insufficient_capacity_before_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.bin"
            source.write_bytes(b"fixture")
            destination = root / "archive"
            destination.mkdir()
            policy = storage.default_policy_for_tests()
            policy["archive_targets"] = [{"id": "vault", "path": str(destination)}]
            backend = storage.LocalActionBackend(root / "state", policy)
            candidate = self.candidate(path=str(source), action_class="archive", archive_target_id="vault", logical_bytes=GIB)
            with mock.patch.object(storage.shutil, "disk_usage", return_value=storage.shutil._ntuple_diskusage(GIB, GIB, 1)):
                with self.assertRaisesRegex(storage.StorageError, "insufficient"):
                    backend._archive(candidate)
            self.assertEqual(list(destination.iterdir()), [])

    def test_replaced_or_resized_candidate_fails_fresh_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "candidate.bin"
            path.write_bytes(b"a" * 4096)
            policy = storage.default_policy_for_tests()
            backend = storage.LocalActionBackend(Path(tmp) / "state", policy)
            backend.metadata = mock.Mock()
            backend.metadata.inspect.return_value = storage.default_cloud_metadata()
            candidate = storage.classify_candidate(path=path, metrics=storage.scan_path(path), cloud=storage.default_cloud_metadata(), policy=policy)
            path.write_bytes(b"b" * 8192)
            self.assertFalse(backend.verify_candidate(candidate))

    def test_manifest_restore_refuses_overwrite_and_restores_exact_item(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trash = root / "trash-item"
            trash.write_text("fixture")
            original = root / "restored" / "item"
            record = {
                "plan_id": "plan-fixture",
                "record_id": "apply-fixture",
                "trash_manifest": [{"candidate_id": "one", "trash_path": str(trash), "original_path": str(original), "trash_inode": trash.lstat().st_ino}],
            }
            backend = storage.LocalActionBackend(root / "state", storage.default_policy_for_tests())
            result = storage.restore_manifest(record, confirmation="RESTORE STORAGE ITEMS", backend=backend)
            self.assertEqual(result["status"], "restored_replan_required")
            self.assertTrue(original.is_file())
            self.assertFalse(trash.exists())


if __name__ == "__main__":
    unittest.main()
