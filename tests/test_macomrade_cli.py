#!/usr/bin/env python3
"""Contract tests for the repository-local macomrade dispatcher."""

from __future__ import annotations

import io
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import macomrade  # noqa: E402


class MacomradeTests(unittest.TestCase):
    def test_contract_has_all_families_and_existing_targets(self) -> None:
        result = macomrade.validate_contract(ROOT)
        self.assertEqual(result["status"], "passed", result["errors"])
        self.assertEqual(set(result["families"]), macomrade.REQUIRED_FAMILIES)
        self.assertEqual(
            set(result["reserved_future_commands"]),
            macomrade.RESERVED_FUTURE_COMMANDS,
        )

    def test_app_plan_route_preserves_argument_order(self) -> None:
        route = macomrade.route_index()[("plan", "apps")]
        self.assertEqual(
            macomrade.command_for(route, ["--profile", "portable"], python="/fixture/python"),
            [
                "/fixture/python",
                "scripts/macos_apps.py",
                "plan",
                "--profile",
                "portable",
            ],
        )

    def test_apply_route_never_adds_apply_flag(self) -> None:
        route = macomrade.route_index()[("apply", "apps")]
        command = macomrade.command_for(route, ["/tmp/plan.json", "--only", "VLC"])
        self.assertNotIn("--apply", command)
        self.assertEqual(command[-3:], ["/tmp/plan.json", "--only", "VLC"])
        for candidate in macomrade.ROUTES:
            self.assertNotIn("--apply", macomrade.command_for(candidate, []))

    def test_explain_does_not_start_subprocess(self) -> None:
        runner = mock.Mock()
        output = io.StringIO()
        with redirect_stdout(output):
            returncode = macomrade.main(
                ["--explain", "diagnostics", "state"],
                runner=runner,
            )
        self.assertEqual(returncode, 0)
        self.assertIn("scripts/state_paths.py info", output.getvalue())
        runner.assert_not_called()

    def test_dispatch_preserves_subprocess_returncode_and_cwd(self) -> None:
        runner = mock.Mock(
            return_value=subprocess.CompletedProcess([], 17)
        )
        returncode = macomrade.main(
            ["verify", "clean-mac"],
            runner=runner,
        )
        self.assertEqual(returncode, 17)
        args, kwargs = runner.call_args
        self.assertEqual(
            args[0][1:],
            ["scripts/clean_mac_acceptance.py", "validate"],
        )
        self.assertEqual(kwargs["cwd"], ROOT)
        self.assertFalse(kwargs["check"])

    def test_unknown_and_reserved_commands_fail_before_subprocess(self) -> None:
        for argv in (["scan", "unknown"], ["mac-buro"], ["5y-plan"]):
            with self.subTest(argv=argv):
                runner = mock.Mock()
                with redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as raised:
                        macomrade.main(argv, runner=runner)
                self.assertEqual(raised.exception.code, 2)
                runner.assert_not_called()

    def test_launcher_reports_repository_version(self) -> None:
        completed = subprocess.run(
            [str(ROOT / "bin/macomrade"), "--version"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(
            completed.stdout.strip(),
            f"macomrade {macomrade.version()}",
        )


if __name__ == "__main__":
    unittest.main()
