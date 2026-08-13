#!/usr/bin/env python3
"""Hermetic tests for the Clean-Mac release-acceptance harness."""

from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import clean_mac_acceptance as acceptance  # noqa: E402


FIXED_TIME = dt.datetime(2026, 9, 1, 0, 0, tzinfo=dt.timezone.utc)


def fake_runner(*, dirty: bool = False, commit: str = "a" * 40):
    responses = {
        (
            sys.executable,
            "scripts/icloud_git_guard.py",
            "inspect",
            "--repo",
            ".",
        ): "status: ready\n",
        ("git", "status", "--porcelain"): " M dirty.txt\n" if dirty else "",
        ("git", "rev-parse", "HEAD"): commit + "\n",
        ("sw_vers", "-productVersion"): "27.0\n",
        ("uname", "-m"): "arm64\n",
    }

    def run(command, **_kwargs):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=responses[tuple(command)],
            stderr="",
        )

    return run


def evidence_value(gate_id: str, index: int = 1, outcome: str = "passed") -> dict:
    if gate_id == "CM-03" and outcome == "passed":
        return {
            "status": "passed",
            "mode": "hermetic",
            "results": [
                {"id": "clean-mac-acceptance", "status": "passed"},
                {"id": "release-contract", "status": "passed"},
                {"id": "hermetic-tests", "status": "passed"},
            ],
        }
    if gate_id == "CM-04" and outcome == "passed":
        return {
            "steps": [
                {"name": name, "status": "passed"}
                for name in (
                    "tracked_definition_validation",
                    "app_scan",
                    "app_plan",
                    "permission_inventory",
                    "preference_baseline_and_check",
                )
            ]
        }
    if gate_id == "CM-06" and outcome == "passed":
        return {
            "action_id": "supply-chain.capture",
            "status": "passed",
            "record_status": "recorded",
        }
    if gate_id == "CM-11" and outcome == "passed":
        return {
            "mode": "read_only_final_drift_check",
            "app_drift": {"missing_core": [], "source_mismatches": []},
            "step_returncodes": {"apps": 0, "permissions": 0, "preferences": 0},
        }
    value = {
        "schema_version": 1,
        "kind": "clean_mac_gate_evidence",
        "gate_id": gate_id,
        "outcome": outcome,
        "observed_at": "2026-09-01T00:00:00+00:00",
        "assertions": ["Specific result was reviewed."],
        "accepted_exceptions": [],
    }
    if gate_id == "CM-12":
        value["phase"] = "install_readback" if index == 1 else "uninstall_readback"
    return value


class CleanMacAcceptanceTests(unittest.TestCase):
    def create_session(self, root: Path) -> tuple[Path, dict]:
        output = root / "session"
        result = acceptance.new_session(
            output,
            attestation="CLEAN MACHINE: UNUSED OR NEW MAC",
            root=root,
            runner=fake_runner(),
            now=lambda: FIXED_TIME,
            session_id="fixture-session",
        )
        return output, result

    def test_repository_contract_is_valid_but_hardware_is_blocked(self) -> None:
        result = acceptance.validate_contract()
        self.assertEqual(result["status"], "passed", result["errors"])
        self.assertEqual(result["gate_count"], 13)
        self.assertEqual(result["hardware_run_status"], "blocked_external")

    def test_init_requires_clean_hardware_attestation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "session"
            with self.assertRaisesRegex(
                acceptance.AcceptanceError,
                "attestation",
            ):
                acceptance.new_session(
                    output,
                    attestation="configured Mac",
                    root=Path(tmp),
                    runner=fake_runner(),
                )
            self.assertFalse(output.exists())

    def test_dirty_source_stops_before_session_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "session"
            with self.assertRaisesRegex(
                acceptance.AcceptanceError,
                "clean Git worktree",
            ):
                acceptance.new_session(
                    output,
                    attestation="CLEAN MACHINE: UNUSED OR NEW MAC",
                    root=Path(tmp),
                    runner=fake_runner(dirty=True),
                )
            self.assertFalse(output.exists())

    def test_init_records_commit_and_only_two_initial_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output, result = self.create_session(Path(tmp))
            persisted = json.loads((output / "session.json").read_text())
        self.assertEqual(result["source"]["commit"], "a" * 40)
        self.assertEqual(
            [gate["id"] for gate in persisted["gates"] if gate["outcome"] == "passed"],
            ["CM-01", "CM-02"],
        )
        self.assertFalse(result.get("publication_authorized", False))

    def test_record_sanitizes_json_and_never_persists_source_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output, _ = self.create_session(root)
            evidence = root / "private-name.json"
            value = evidence_value("CM-03")
            value["owner"] = "person@example.com"
            value["path"] = "/Users/example/private/result.json"
            evidence.write_text(json.dumps(value), encoding="utf-8")
            result = acceptance.record_gate(
                output,
                gate_id="CM-03",
                outcome="passed",
                evidence_paths=[evidence],
                note="Checked by person@example.com",
                now=lambda: FIXED_TIME,
            )
            bundled = json.loads(
                (output / "evidence/CM-03-r01-01.json").read_text(encoding="utf-8")
            )
        gate = next(row for row in result["gates"] if row["id"] == "CM-03")
        self.assertNotIn(str(evidence), json.dumps(gate))
        self.assertEqual(bundled["owner"], "<redacted-email>")
        self.assertEqual(bundled["path"], "<HOME>/private/result.json")
        self.assertEqual(gate["note"], "Checked by <redacted-email>")

    def test_secret_bearing_evidence_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output, _ = self.create_session(root)
            evidence = root / "unsafe.json"
            evidence.write_text('{"access_token":"secret"}', encoding="utf-8")
            with self.assertRaisesRegex(acceptance.AcceptanceError, "prohibited key"):
                acceptance.record_gate(
                    output,
                    gate_id="CM-03",
                    outcome="passed",
                    evidence_paths=[evidence],
                    note="",
                )

    def test_generic_pass_json_cannot_satisfy_a_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output, _ = self.create_session(root)
            evidence = root / "generic.json"
            evidence.write_text('{"status":"passed"}', encoding="utf-8")
            with self.assertRaisesRegex(
                acceptance.AcceptanceError,
                "release_check_result",
            ):
                acceptance.record_gate(
                    output,
                    gate_id="CM-03",
                    outcome="passed",
                    evidence_paths=[evidence],
                    note="",
                )

    def test_rollback_gate_requires_both_semantic_phases(self) -> None:
        definition = next(
            gate
            for gate in json.loads(acceptance.CONTRACT_PATH.read_text())["gates"]
            if gate["id"] == "CM-12"
        )
        duplicate = [evidence_value("CM-12", 1), evidence_value("CM-12", 1)]
        with self.assertRaisesRegex(acceptance.AcceptanceError, "phases"):
            acceptance.validate_evidence_semantics(
                definition,
                duplicate,
                outcome="passed",
            )

    def test_record_preview_validates_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output, before = self.create_session(root)
            evidence = root / "result.json"
            evidence.write_text(json.dumps(evidence_value("CM-03")), encoding="utf-8")
            result = acceptance.record_gate(
                output,
                gate_id="CM-03",
                outcome="passed",
                evidence_paths=[evidence],
                note="preview",
                now=lambda: FIXED_TIME,
                write=False,
            )
            persisted = json.loads((output / "session.json").read_text())
        preview = next(row for row in result["gates"] if row["id"] == "CM-03")
        actual = next(row for row in persisted["gates"] if row["id"] == "CM-03")
        self.assertEqual(preview["outcome"], "passed")
        self.assertEqual(actual["outcome"], "pending")
        self.assertFalse((output / "evidence/CM-03-r01-01.json").exists())
        self.assertEqual(persisted["updated_at"], before["updated_at"])

    def test_finalize_rejects_pending_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output, _ = self.create_session(root)
            with self.assertRaisesRegex(acceptance.AcceptanceError, "incomplete"):
                acceptance.finalize_session(
                    output,
                    root=root,
                    runner=fake_runner(),
                )

    def test_finalize_accepts_only_complete_same_commit_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output, session = self.create_session(root)
            contract = json.loads(acceptance.CONTRACT_PATH.read_text())
            required = {gate["id"]: gate["required_evidence"] for gate in contract["gates"]}
            for gate in session["gates"]:
                gate["outcome"] = "passed"
                gate["evidence"] = []
                for index in range(1, required[gate["id"]] + 1):
                    artifact_id = f"{gate['id']}-r01-{index:02d}"
                    artifact_path = output / "evidence" / f"{artifact_id}.json"
                    artifact_path.write_text(
                        json.dumps(evidence_value(gate["id"], index)) + "\n",
                        encoding="utf-8",
                    )
                    gate["evidence"].append(
                        {
                            "artifact_id": artifact_id,
                            "source_sha256": "b" * 64,
                            "bundle_sha256": acceptance.sha256_path(artifact_path),
                            "bundle_bytes": artifact_path.stat().st_size,
                            "bundle_file": f"evidence/{artifact_id}.json",
                        }
                    )
            acceptance.atomic_write(output / "session.json", session)
            result = acceptance.finalize_session(
                output,
                root=root,
                runner=fake_runner(),
                now=lambda: FIXED_TIME,
            )
        self.assertEqual(result["status"], "accepted")
        self.assertFalse(result["publication_authorized"])
        self.assertEqual(result["action_id"], "clean-mac.finalize")

    def test_finalize_rejects_tampered_evidence_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output, session = self.create_session(root)
            contract = json.loads(acceptance.CONTRACT_PATH.read_text())
            required = {gate["id"]: gate["required_evidence"] for gate in contract["gates"]}
            for gate in session["gates"]:
                gate["outcome"] = "passed"
                gate["evidence"] = []
                for index in range(1, required[gate["id"]] + 1):
                    artifact_id = f"{gate['id']}-r01-{index:02d}"
                    artifact_path = output / "evidence" / f"{artifact_id}.json"
                    artifact_path.write_text(
                        json.dumps(evidence_value(gate["id"], index)) + "\n",
                        encoding="utf-8",
                    )
                    gate["evidence"].append(
                        {
                            "artifact_id": artifact_id,
                            "source_sha256": "b" * 64,
                            "bundle_sha256": acceptance.sha256_path(artifact_path),
                            "bundle_bytes": artifact_path.stat().st_size,
                            "bundle_file": f"evidence/{artifact_id}.json",
                        }
                    )
            acceptance.atomic_write(output / "session.json", session)
            target = output / "evidence/CM-03-r01-01.json"
            target.write_text('{"status":"tampered"}\n', encoding="utf-8")
            with self.assertRaisesRegex(acceptance.AcceptanceError, "mismatch"):
                acceptance.finalize_session(
                    output,
                    root=root,
                    runner=fake_runner(),
                )

    def test_wrong_confirmation_writes_no_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "session"
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/clean_mac_acceptance.py"),
                    "init",
                    "--attest",
                    "CLEAN MACHINE: UNUSED OR NEW MAC",
                    "--session-dir",
                    str(output),
                    "--apply",
                    "--confirm",
                    "wrong",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("UPDATE CLEAN MAC ACCEPTANCE", completed.stderr)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
