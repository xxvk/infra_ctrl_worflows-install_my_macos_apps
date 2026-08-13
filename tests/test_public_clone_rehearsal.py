from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import public_clone_rehearsal  # noqa: E402


class PublicCloneRehearsalTests(unittest.TestCase):
    def test_repository_definition_is_valid(self) -> None:
        result = public_clone_rehearsal.validate_definition()
        self.assertEqual(result["status"], "passed", result["errors"])

    def test_environment_is_credential_free_and_public_only(self) -> None:
        environment = public_clone_rehearsal.credential_free_environment(
            home=Path("/tmp/public-home"),
            state_dir=Path("/tmp/public-state"),
            temp_dir=Path("/tmp/public-temp"),
            environ={
                "PATH": "/usr/bin:/bin",
                "LANG": "en_US.UTF-8",
                "GH_TOKEN": "must-not-pass",
                "GITHUB_TOKEN": "must-not-pass",
                "SSH_AUTH_SOCK": "/tmp/agent.sock",
                "AWS_SECRET_ACCESS_KEY": "must-not-pass",
            },
        )
        self.assertEqual(environment["MACOMRADE_PUBLIC_ONLY"], "1")
        self.assertEqual(environment["GIT_TERMINAL_PROMPT"], "0")
        self.assertEqual(environment["GIT_CONFIG_NOSYSTEM"], "1")
        self.assertEqual(environment["HOME"], "/tmp/public-home")
        self.assertEqual(
            environment["INSTALL_MY_MACOS_APPS_STATE_DIR"],
            "/tmp/public-state",
        )
        for secret_name in (
            "GH_TOKEN",
            "GITHUB_TOKEN",
            "SSH_AUTH_SOCK",
            "AWS_SECRET_ACCESS_KEY",
        ):
            self.assertNotIn(secret_name, environment)

    def test_rehearsal_runs_release_gate_and_documented_quick_start(self) -> None:
        steps = public_clone_rehearsal.rehearsal_steps(python="/fixture/python")
        self.assertEqual(
            [step_id for step_id, _command in steps],
            [
                "bootstrap-definition",
                "cli-contract",
                "schema-contract",
                "release-check",
                "app-inventory",
                "app-plan",
            ],
        )
        commands = [command for _step_id, command in steps]
        self.assertIn(
            ["/fixture/python", "scripts/release_check.py"],
            commands,
        )
        self.assertIn(
            ["./bin/macomrade", "plan", "apps", "--profile", "auto"],
            commands,
        )
        for command in commands:
            self.assertNotIn("--apply", command)
            self.assertNotIn("sudo", command)

    def test_personal_marker_detection_is_bounded(self) -> None:
        self.assertEqual(public_clone_rehearsal.personal_markers("ordinary output"), [])
        findings = public_clone_rehearsal.personal_markers(
            "contact person@example.com under /Users/alice/project"
        )
        self.assertEqual(findings, ["email_address", "absolute_user_home"])

    def test_record_contains_no_publication_authority(self) -> None:
        record = public_clone_rehearsal.build_record(
            commit="a" * 40,
            results=[
                {
                    "id": "fixture",
                    "command": ["fixture"],
                    "returncode": 0,
                    "status": "passed",
                }
            ],
            source_clean=True,
            clone_clean=True,
            private_overlay_present=False,
            markers=[],
        )
        self.assertEqual(record["status"], "passed")
        self.assertEqual(record["transport"], "credential_free_local_clone")
        self.assertFalse(record["authority"]["visibility_change_authorized"])
        self.assertFalse(record["authority"]["publication_authorized"])
        self.assertIn("not anonymous github access", record["boundary"].lower())
        serialized = str(record)
        self.assertNotIn(str(Path.home()), serialized)


if __name__ == "__main__":
    unittest.main()
