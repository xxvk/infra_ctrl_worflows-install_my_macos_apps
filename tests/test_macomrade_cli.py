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

    def test_storage_routes_are_stable_and_never_add_authorization(self) -> None:
        expected = {
            ("scan", "storage"): "scan",
            ("review", "storage"): "review",
            ("plan", "storage"): "plan",
            ("apply", "storage"): "apply",
            ("verify", "storage"): "verify",
            ("history", "storage"): "history",
        }
        for key, prefix in expected.items():
            with self.subTest(route=key):
                command = macomrade.command_for(
                    macomrade.route_index()[key],
                    ["--state-dir", "/tmp/storage-state"],
                    python="/fixture/python",
                )
                self.assertEqual(command[:3], ["/fixture/python", "scripts/storage_lifecycle.py", prefix])
                self.assertNotIn("--apply", command)
                self.assertNotIn("--confirm", command)

    def test_browser_routes_are_stable_redacted_handoffs(self) -> None:
        expected = {
            ("scan", "browser"): ("scripts/safari_export.py", "inspect"),
            ("review", "browser"): ("scripts/browser_lifecycle.py", "review-safari-export"),
            ("plan", "browser"): ("scripts/browser_transactions.py", "plan-safari-export"),
            ("apply", "browser"): ("scripts/browser_transactions.py", "apply-live-safari"),
            ("verify", "browser"): ("scripts/browser_transactions.py", "verify-post-export"),
            ("history", "browser"): ("scripts/browser_lifecycle.py", "inspect-ledger"),
        }
        for key, (script, prefix) in expected.items():
            with self.subTest(route=key):
                route = macomrade.route_index()[key]
                command = macomrade.command_for(
                    route,
                    ["/tmp/private-input.json"],
                    python="/fixture/python",
                )
                self.assertEqual(command[:3], ["/fixture/python", script, prefix])
                self.assertNotIn("--apply", command)
                self.assertNotIn("--confirm", command)
        self.assertFalse(
            macomrade.route_index()[("apply", "browser")].mutating_capable
        )
        capability = macomrade.route_index()[("scan", "browser-capabilities")]
        self.assertFalse(capability.mutating_capable)
        self.assertEqual(
            macomrade.command_for(capability, [], python="/fixture/python"),
            [
                "/fixture/python",
                "scripts/browser_sources.py",
                "inspect-safari",
            ],
        )
        private_review = macomrade.route_index()[("review", "browser-duplicates")]
        self.assertTrue(private_review.mutating_capable)
        self.assertEqual(
            macomrade.command_for(
                private_review,
                ["/tmp/private-export.zip", "--output", "Private/browser/review.json"],
                python="/fixture/python",
            ),
            [
                "/fixture/python",
                "scripts/browser_review.py",
                "export-private-duplicates",
                "/tmp/private-export.zip",
                "--output",
                "Private/browser/review.json",
            ],
        )
        organization = macomrade.route_index()[("review", "browser-organization")]
        self.assertTrue(organization.mutating_capable)
        self.assertEqual(
            macomrade.command_for(
                organization,
                [
                    "/tmp/private-export.zip",
                    "--spec",
                    "/tmp/private-spec.json",
                    "--output",
                    "Private/browser/organization.json",
                ],
                python="/fixture/python",
            ),
            [
                "/fixture/python",
                "scripts/browser_organization.py",
                "compile-safari-export",
                "/tmp/private-export.zip",
                "--spec",
                "/tmp/private-spec.json",
                "--output",
                "Private/browser/organization.json",
            ],
        )
        evidence = macomrade.route_index()[("review", "browser-evidence")]
        self.assertTrue(evidence.mutating_capable)
        self.assertEqual(
            macomrade.command_for(
                evidence,
                ["/tmp/private-export.zip", "--exported-on", "2026-08-15"],
                python="/fixture/python",
            ),
            [
                "/fixture/python",
                "scripts/browser_evidence.py",
                "import-safari-export",
                "/tmp/private-export.zip",
                "--exported-on",
                "2026-08-15",
            ],
        )
        reconciliation = macomrade.route_index()[("review", "browser-reconciliation")]
        self.assertTrue(reconciliation.mutating_capable)
        self.assertEqual(
            macomrade.command_for(
                reconciliation,
                [
                    "Private/browser/organization.json",
                    "/tmp/new-export.zip",
                    "--reconciled-on",
                    "2026-08-16",
                ],
                python="/fixture/python",
            ),
            [
                "/fixture/python",
                "scripts/browser_reconciliation.py",
                "reconcile-safari-export",
                "Private/browser/organization.json",
                "/tmp/new-export.zip",
                "--reconciled-on",
                "2026-08-16",
            ],
        )
        gateway = macomrade.route_index()[("review", "browser-gateway")]
        self.assertFalse(gateway.mutating_capable)
        self.assertEqual(
            macomrade.command_for(
                gateway,
                ["Private/browser/organization.json"],
                python="/fixture/python",
            ),
            [
                "/fixture/python",
                "scripts/browser_gateway.py",
                "audit-organization",
                "Private/browser/organization.json",
            ],
        )
        wave = macomrade.route_index()[("review", "browser-gateway-wave")]
        self.assertTrue(wave.mutating_capable)
        command = macomrade.command_for(
            wave,
            ["Private/browser/organization.json", "--spec", "/tmp/wave.json"],
            python="/fixture/python",
        )
        self.assertEqual(command[:3], ["/fixture/python", "scripts/browser_gateway.py", "sync-wave"])
        self.assertNotIn("--apply", command)
        self.assertNotIn("--confirm", command)
        gateway_plan = macomrade.route_index()[("plan", "browser-gateway")]
        self.assertFalse(gateway_plan.mutating_capable)
        self.assertEqual(
            macomrade.command_for(
                gateway_plan,
                ["Private/browser/gateway/wave-2026-08-15-01.json"],
                python="/fixture/python",
            ),
            [
                "/fixture/python",
                "scripts/browser_gateway.py",
                "plan-wave",
                "Private/browser/gateway/wave-2026-08-15-01.json",
            ],
        )
        pilot = macomrade.route_index()[("review", "browser-gateway-pilot")]
        self.assertTrue(pilot.mutating_capable)
        pilot_command = macomrade.command_for(
            pilot,
            ["Private/browser/organization.json", "Private/browser/gateway/wave.json"],
            python="/fixture/python",
        )
        self.assertEqual(
            pilot_command[:3],
            ["/fixture/python", "scripts/browser_gateway_pilot.py", "freeze"],
        )
        self.assertNotIn("--apply", pilot_command)
        order = macomrade.route_index()[("review", "browser-gateway-order")]
        self.assertTrue(order.mutating_capable)
        order_command = macomrade.command_for(
            order,
            ["Private/browser/gateway/convergence.json", "--spec", "/tmp/order.json"],
            python="/fixture/python",
        )
        self.assertEqual(
            order_command[:3],
            ["/fixture/python", "scripts/browser_gateway_order.py", "Private/browser/gateway/convergence.json"],
        )
        self.assertNotIn("--apply", order_command)
        self.assertNotIn("--confirm", order_command)
        pilot_verify = macomrade.route_index()[("verify", "browser-gateway-pilot")]
        self.assertFalse(pilot_verify.mutating_capable)
        self.assertEqual(
            macomrade.command_for(
                pilot_verify,
                ["Private/browser/gateway/pilot.json", "--checkpoint", "batch-1"],
                python="/fixture/python",
            )[:3],
            ["/fixture/python", "scripts/browser_gateway_pilot.py", "verify"],
        )

    def test_browser_acceptance_route_requires_an_explicit_subcommand(self) -> None:
        route = macomrade.route_index()[("verify", "browser-acceptance")]
        command = macomrade.command_for(
            route,
            ["inspect-live", "/tmp/private-export.zip"],
            python="/fixture/python",
        )
        self.assertEqual(
            command,
            [
                "/fixture/python",
                "scripts/browser_acceptance.py",
                "inspect-live",
                "/tmp/private-export.zip",
            ],
        )
        self.assertFalse(route.mutating_capable)
        self.assertNotIn("--apply", command)

    def test_schema_routes_are_explicit_and_do_not_authorize_writes(self) -> None:
        self.assertEqual(
            macomrade.command_for(
                macomrade.route_index()[("verify", "schemas")],
                [],
                python="/fixture/python",
            ),
            [
                "/fixture/python",
                "scripts/schema_contract.py",
                "validate-tracked",
            ],
        )
        migration = macomrade.command_for(
            macomrade.route_index()[("migration", "schema")],
            ["app-plan", "/tmp/plan.json", "--to", "1"],
            python="/fixture/python",
        )
        self.assertNotIn("--apply", migration)

    def test_role_and_adapter_routes_preserve_safe_handoffs(self) -> None:
        roles = macomrade.command_for(
            macomrade.route_index()[("diagnostics", "roles")],
            ["--roles", "auto,developer", "--storage-gb", "256"],
            python="/fixture/python",
        )
        self.assertEqual(
            roles,
            [
                "/fixture/python",
                "scripts/machine_roles.py",
                "explain",
                "--roles",
                "auto,developer",
                "--storage-gb",
                "256",
            ],
        )
        adapters = macomrade.command_for(
            macomrade.route_index()[("plan", "adapters")],
            ["--adapter", "claude-vm"],
            python="/fixture/python",
        )
        self.assertEqual(adapters[:3], ["/fixture/python", "scripts/app_adapters.py", "plan"])
        self.assertNotIn("--apply", adapters)

    def test_benchmark_report_and_monitor_routes_remain_non_repairing(self) -> None:
        for family, target in (
            ("diagnostics", "benchmark"),
            ("diagnostics", "report"),
            ("diagnostics", "publication"),
            ("scan", "monitor"),
        ):
            with self.subTest(family=family, target=target):
                command = macomrade.command_for(macomrade.route_index()[(family, target)], [])
                self.assertNotIn("--apply", command)
                self.assertNotIn("repair", command)

    def test_publication_audit_route_is_read_only_inventory(self) -> None:
        command = macomrade.command_for(
            macomrade.route_index()[("diagnostics", "publication")],
            ["--state-dir", "/tmp/state"],
            python="/fixture/python",
        )
        self.assertEqual(
            command,
            [
                "/fixture/python",
                "scripts/publication_audit.py",
                "inspect",
                "--state-dir",
                "/tmp/state",
            ],
        )
        self.assertNotIn("publish", command)
        self.assertNotIn("rewrite", command)

    def test_release_manifest_route_is_preview_only(self) -> None:
        command = macomrade.command_for(
            macomrade.route_index()[("diagnostics", "release-manifest")],
            [],
            python="/fixture/python",
        )
        self.assertEqual(
            command,
            ["/fixture/python", "scripts/release_manifest.py", "preview"],
        )
        self.assertNotIn("--apply", command)
        self.assertNotIn("publish", command)

    def test_public_clone_route_does_not_authorize_publication(self) -> None:
        command = macomrade.command_for(
            macomrade.route_index()[("diagnostics", "public-clone")],
            ["--state-dir", "/tmp/public-clone-state"],
            python="/fixture/python",
        )
        self.assertEqual(
            command,
            [
                "/fixture/python",
                "scripts/public_clone_rehearsal.py",
                "run",
                "--state-dir",
                "/tmp/public-clone-state",
            ],
        )
        self.assertNotIn("publish", command)
        self.assertNotIn("--apply", command)

    def test_diagnostic_preview_and_export_are_separate_routes(self) -> None:
        preview = macomrade.command_for(
            macomrade.route_index()[("diagnostics", "bundle")],
            [],
            python="/fixture/python",
        )
        self.assertEqual(
            preview,
            [
                "/fixture/python",
                "scripts/diagnostic_bundle.py",
                "preview",
            ],
        )
        export = macomrade.command_for(
            macomrade.route_index()[("apply", "diagnostic-bundle")],
            ["--output", "/tmp/diagnostics.zip"],
            python="/fixture/python",
        )
        self.assertNotIn("--apply", export)
        self.assertEqual(export[-2:], ["--output", "/tmp/diagnostics.zip"])

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
