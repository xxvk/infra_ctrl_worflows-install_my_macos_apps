#!/usr/bin/env python3
"""Hermetic application inventory, planning, and install contract tests."""

from __future__ import annotations

import argparse
import json
import plistlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/macos_apps/catalog.json"
sys.path.insert(0, str(ROOT / "scripts"))

import macos_apps  # noqa: E402


def fixture_catalog() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def write_bundle(root: Path, name: str, bundle_id: str, version: str) -> Path:
    bundle = root / f"{name}.app"
    contents = bundle / "Contents"
    contents.mkdir(parents=True)
    (contents / "Info.plist").write_bytes(
        plistlib.dumps(
            {
                "CFBundleDisplayName": name,
                "CFBundleIdentifier": bundle_id,
                "CFBundleShortVersionString": version,
            }
        )
    )
    return bundle


class AppCatalogAndSourceTests(unittest.TestCase):
    def test_npm_global_presence_requires_exact_package_in_fnm_24(self) -> None:
        app = {
            "name": "Fixture npm",
            "npm_package": "fixture",
            "npm_version": "1.2.3",
            "npm_runtime_manager": "fnm",
            "npm_runtime_version": "24",
        }
        response = subprocess.CompletedProcess(
            [], 0, stdout=json.dumps({"dependencies": {"fixture": {"version": "1.2.3"}}}), stderr=""
        )
        with mock.patch.object(macos_apps.shutil, "which", return_value="/fake/fnm"):
            with mock.patch.object(macos_apps.subprocess, "run", return_value=response) as run:
                self.assertTrue(macos_apps.npm_package_present(app))
        self.assertEqual(
            run.call_args.args[0],
            ["fnm", "exec", "--using=24", "npm", "list", "--global", "--depth=0", "--json"],
        )

    def test_version_comparison_normalizes_missing_segments(self) -> None:
        self.assertTrue(macos_apps.version_below("1.9", "2.0.0"))
        self.assertFalse(macos_apps.version_below("2", "2.0.0"))
        self.assertFalse(macos_apps.version_below("2.0.1", "2.0.0"))

    def test_homebrew_casks_use_faked_command_response(self) -> None:
        response = subprocess.CompletedProcess(
            ["brew", "list", "--cask"],
            0,
            stdout="fixture-brew\nanother-cask\n",
            stderr="",
        )
        with mock.patch.object(macos_apps.shutil, "which", return_value="/fake/brew"):
            with mock.patch.object(macos_apps.subprocess, "run", return_value=response) as run:
                self.assertEqual(
                    macos_apps.installed_brew_casks(),
                    {"fixture-brew", "another-cask"},
                )
        run.assert_called_once_with(
            ["/fake/brew", "list", "--cask"],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_app_store_receipt_and_website_bundle_are_distinguished(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            store = write_bundle(root, "Fixture Store", "com.example.store", "1.0")
            receipt = store / "Contents/_MASReceipt/receipt"
            receipt.parent.mkdir()
            receipt.write_bytes(b"fixture")
            store_app = next(
                app for app in fixture_catalog()["apps"] if app["name"] == "Fixture Store"
            )
            source = macos_apps.detect_source(
                store_app,
                {"name": "Fixture Store", "path": str(store)},
                set(),
            )
            self.assertEqual(source["detected"], "app_store")
            self.assertTrue(source["match"])

            website = write_bundle(
                root,
                "Fixture Website",
                "com.example.website",
                "1.0",
            )
            website_app = next(
                app
                for app in fixture_catalog()["apps"]
                if app["name"] == "Fixture Website"
            )
            source = macos_apps.detect_source(
                website_app,
                {
                    "name": "Fixture Website",
                    "path": str(website),
                    "bundle_identifier": "com.example.website",
                },
                set(),
            )
            self.assertEqual(source["detected"], "official_web")
            self.assertTrue(source["match"])

    def test_filesystem_inventory_reads_fixture_bundle(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            apps = Path(tmp)
            write_bundle(apps, "Fixture Website", "com.example.website", "1.2.3")
            with mock.patch.object(macos_apps, "APP_DIRS", [apps]):
                with mock.patch.object(macos_apps, "installed_brew_casks", return_value=set()):
                    found = macos_apps.installed_apps(fixture_catalog())
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]["version"], "1.2.3")
            self.assertEqual(found[0]["catalog_name"], "Fixture Website")
            self.assertEqual(found[0]["source"]["detected"], "official_web")


class PlanningAndCommandTests(unittest.TestCase):
    def test_plan_without_roles_defaults_to_auto_base_capacity(self) -> None:
        selection = {
            "roles": ["base", "compact"],
            "requested_roles": ["auto"],
            "selected_apps": ["Fixture Store"],
            "excluded_apps": [],
            "reasons": {"Fixture Store": ["base"]},
        }
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            with mock.patch.object(macos_apps, "STATE", state):
                with mock.patch.object(macos_apps, "CATALOG", FIXTURE):
                    with mock.patch.object(macos_apps, "catalog", side_effect=fixture_catalog):
                        with mock.patch.object(macos_apps, "installed_apps", return_value=[]):
                            with mock.patch.object(macos_apps, "storage_gb", return_value=256.0):
                                with mock.patch.object(macos_apps.machine_roles, "load_roles", return_value={}):
                                    with mock.patch.object(
                                        macos_apps.machine_roles,
                                        "resolve",
                                        return_value=selection,
                                    ) as resolve:
                                        macos_apps.plan(argparse.Namespace(profile="portable"))
            result = json.loads(next(state.glob("plan-*.json")).read_text(encoding="utf-8"))
        self.assertEqual([item["name"] for item in result["missing"]], ["Fixture Store"])
        self.assertEqual(result["role_selection"], selection)
        self.assertEqual(resolve.call_args.args[2], ["auto"])

    def test_role_plan_uses_resolved_core_plus_role_selection(self) -> None:
        selection = {
            "roles": ["base", "developer"],
            "selected_apps": ["Fixture Store"],
            "excluded_apps": [],
            "reasons": {"Fixture Store": ["base"]},
        }
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            with mock.patch.object(macos_apps, "STATE", state):
                with mock.patch.object(macos_apps, "CATALOG", FIXTURE):
                    with mock.patch.object(macos_apps, "catalog", side_effect=fixture_catalog):
                        with mock.patch.object(macos_apps, "installed_apps", return_value=[]):
                            with mock.patch.object(macos_apps, "storage_gb", return_value=256.0):
                                with mock.patch.object(macos_apps.machine_roles, "load_roles", return_value={}):
                                    with mock.patch.object(macos_apps.machine_roles, "resolve", return_value=selection) as resolve:
                                        macos_apps.plan(
                                            argparse.Namespace(
                                                profile="portable",
                                                roles="auto,developer",
                                                include_app=[],
                                                exclude_app=[],
                                            )
                                        )
            result = json.loads(next(state.glob("plan-*.json")).read_text(encoding="utf-8"))
        self.assertEqual([item["name"] for item in result["missing"]], ["Fixture Store"])
        self.assertEqual(result["role_selection"], selection)
        self.assertEqual(resolve.call_args.kwargs["storage_gb"], 256.0)

    def test_portable_plan_excludes_heavy_and_reports_version_issue(self) -> None:
        selection = {
            "roles": ["base", "compact"],
            "requested_roles": ["auto"],
            "selected_apps": [
                "Fixture Brew",
                "Fixture Store",
                "Fixture Website",
                "Fixture Heavy",
            ],
            "excluded_apps": [],
            "reasons": {},
        }
        installed = [
            {
                "name": "Fixture Brew",
                "version": "1.0.0",
                "path": "/Applications/Fixture Brew.app",
                "catalog_name": "Fixture Brew",
                "source": {"match": True},
            }
        ]
        with tempfile.TemporaryDirectory() as tmp:
            state = Path(tmp)
            with mock.patch.object(macos_apps, "STATE", state):
                with mock.patch.object(macos_apps, "CATALOG", FIXTURE):
                    with mock.patch.object(macos_apps, "catalog", side_effect=fixture_catalog):
                        with mock.patch.object(macos_apps, "installed_apps", return_value=installed):
                            with mock.patch.object(macos_apps, "storage_gb", return_value=256.0):
                                with mock.patch.object(macos_apps.machine_roles, "load_roles", return_value={}):
                                    with mock.patch.object(macos_apps.machine_roles, "resolve", return_value=selection):
                                        macos_apps.plan(argparse.Namespace(profile="portable"))
            plan = json.loads(next(state.glob("plan-*.json")).read_text())
        self.assertEqual(plan["profile"], "portable")
        self.assertEqual(
            {app["name"] for app in plan["missing"]},
            {"Fixture Store", "Fixture Website"},
        )
        self.assertNotIn(
            "Fixture Heavy",
            {app["name"] for app in plan["missing"]},
        )
        self.assertEqual(plan["version_issues"][0]["app"], "Fixture Brew")

    def test_command_rendering_is_stable(self) -> None:
        app = fixture_catalog()["apps"][0]
        self.assertEqual(
            macos_apps.install_commands(app, force=True),
            [
                [
                    "env",
                    "HOMEBREW_NO_AUTO_UPDATE=1",
                    "HOMEBREW_NO_INSTALL_UPGRADE=1",
                    "brew",
                    "tap",
                    "example/tools",
                ],
                [
                    "env",
                    "HOMEBREW_NO_AUTO_UPDATE=1",
                    "HOMEBREW_NO_INSTALL_UPGRADE=1",
                    "brew",
                    "install",
                    "--force",
                    "--cask",
                    "fixture-brew",
                ],
            ],
        )

    def test_high_risk_commands_are_exactly_scoped_and_versioned(self) -> None:
        cask = {
            "name": "Pinned Cask",
            "brew_tap": "example/tools",
            "brew_cask": "example/tools/pinned",
            "brew_trust_cask": "example/tools/pinned",
        }
        self.assertEqual(
            macos_apps.install_commands(cask)[1],
            [
                "env",
                "HOMEBREW_NO_AUTO_UPDATE=1",
                "brew",
                "trust",
                "--cask",
                "example/tools/pinned",
            ],
        )
        npm = {
            "name": "Pinned npm",
            "npm_package": "fixture",
            "npm_version": "1.2.3",
            "npm_runtime_manager": "fnm",
            "npm_runtime_version": "24",
        }
        self.assertEqual(
            macos_apps.install_commands(npm),
            [["fnm", "exec", "--using=24", "npm", "install", "--global", "fixture@1.2.3"]],
        )

    def test_fnm_runtime_install_is_scoped_to_node_24(self) -> None:
        runtime = {
            "name": "Node.js 24 LTS",
            "runtime_manager": "fnm",
            "runtime_version": "24",
        }
        self.assertEqual(
            macos_apps.install_commands(runtime),
            [["fnm", "install", "24"], ["fnm", "default", "24"]],
        )

    def test_npm_global_without_declared_runtime_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "npm_runtime_manager"):
            macos_apps.install_commands(
                {"name": "Ambiguous", "npm_package": "fixture", "npm_version": "1.2.3"}
            )

    def test_unpinned_npm_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "npm_version"):
            macos_apps.install_commands({"name": "Unsafe", "npm_package": "unsafe"})

    def test_tap_verification_stops_on_revision_drift(self) -> None:
        app = {
            "name": "Pinned Cask",
            "brew_tap": "example/tools",
            "brew_tap_repository": "https://github.com/example/homebrew-tools",
            "brew_tap_revision": "a" * 40,
        }
        responses = iter(
            [
                subprocess.CompletedProcess([], 0, stdout="/tmp/tap\n", stderr=""),
                subprocess.CompletedProcess(
                    [],
                    0,
                    stdout="https://github.com/example/homebrew-tools\n",
                    stderr="",
                ),
                subprocess.CompletedProcess([], 0, stdout=f"{'b' * 40}\n", stderr=""),
            ]
        )
        with self.assertRaisesRegex(RuntimeError, "tap drift"):
            macos_apps.verify_tap_source(app, runner=lambda *args, **kwargs: next(responses))


class InstallTransactionTests(unittest.TestCase):
    def _plan(self, root: Path) -> Path:
        path = root / "plan.json"
        path.write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "generated_at": "2026-07-23T00:00:00+09:00",
                    "profile": "portable",
                    "missing": [fixture_catalog()["apps"][0]],
                    "source_mismatches": [],
                }
            ),
            encoding="utf-8",
        )
        return path

    def test_invalid_plan_stops_before_external_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = root / "invalid.json"
            plan.write_text(
                json.dumps({"missing": [], "source_mismatches": []}),
                encoding="utf-8",
            )
            with mock.patch.object(macos_apps.subprocess, "run") as run:
                with self.assertRaisesRegex(SystemExit, "schema_version"):
                    macos_apps.install(
                        argparse.Namespace(
                            plan=str(plan),
                            only=["Fixture Brew"],
                            apply=False,
                        )
                    )
            run.assert_not_called()

    def test_dry_run_executes_no_external_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self._plan(root)
            with mock.patch.object(macos_apps, "STATE", root / "state"):
                with mock.patch.object(
                    macos_apps,
                    "load_app_catalog",
                    return_value=fixture_catalog(),
                ):
                    with mock.patch.object(macos_apps.shutil, "which", return_value="/fake/brew"):
                        with mock.patch.object(macos_apps.subprocess, "run") as run:
                            macos_apps.install(
                                argparse.Namespace(
                                    plan=str(plan),
                                    only=["Fixture Brew"],
                                    apply=False,
                                )
                            )
            run.assert_not_called()
            record = json.loads(next((root / "state").glob("install-*.json")).read_text())
            self.assertFalse(record["apply"])
            self.assertEqual(record["measurements"][0]["status"], "dry_run")
            self.assertEqual(
                record["measurements"][0]["provenance"]["source_class"],
                "third_party_homebrew",
            )

    def test_missing_homebrew_never_bootstraps_from_network(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self._plan(root)
            with mock.patch.object(macos_apps, "STATE", root / "state"):
                with mock.patch.object(
                    macos_apps,
                    "load_app_catalog",
                    return_value=fixture_catalog(),
                ):
                    with mock.patch.object(macos_apps.shutil, "which", return_value=None):
                        with mock.patch.object(macos_apps.subprocess, "run") as run:
                            with self.assertRaisesRegex(SystemExit, "Automatic network-to-shell"):
                                macos_apps.install(
                                    argparse.Namespace(
                                        plan=str(plan),
                                        only=["Fixture Brew"],
                                        apply=True,
                                    )
                                )
            run.assert_not_called()

    def test_repeat_apply_renders_same_idempotent_homebrew_sequence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self._plan(root)
            completed = subprocess.CompletedProcess([], 0, stdout="", stderr="")
            with mock.patch.object(macos_apps, "STATE", root / "state"):
                with mock.patch.object(
                    macos_apps,
                    "load_app_catalog",
                    return_value=fixture_catalog(),
                ):
                    with mock.patch.object(macos_apps.shutil, "which", return_value="/fake/brew"):
                        with mock.patch.object(macos_apps, "brew_cache_path", return_value=None):
                            with mock.patch.object(macos_apps, "installed_size", return_value=123):
                                with mock.patch.object(
                                    macos_apps,
                                    "stamp",
                                    side_effect=["first", "second"],
                                ):
                                    with mock.patch.object(
                                        macos_apps.subprocess,
                                        "run",
                                        return_value=completed,
                                    ) as run:
                                        args = argparse.Namespace(
                                            plan=str(plan),
                                            only=["Fixture Brew"],
                                            apply=True,
                                        )
                                        macos_apps.install(args)
                                        macos_apps.install(args)
            calls = [call.args[0] for call in run.call_args_list]
            self.assertEqual(calls[:2], calls[2:])
            self.assertEqual(len(list((root / "state").glob("install-*.json"))), 2)

    def test_interrupted_apply_writes_no_success_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self._plan(root)
            with mock.patch.object(macos_apps, "STATE", root / "state"):
                with mock.patch.object(
                    macos_apps,
                    "load_app_catalog",
                    return_value=fixture_catalog(),
                ):
                    with mock.patch.object(macos_apps.shutil, "which", return_value="/fake/brew"):
                        with mock.patch.object(macos_apps, "brew_cache_path", return_value=None):
                            with mock.patch.object(
                                macos_apps.subprocess,
                                "run",
                                side_effect=subprocess.CalledProcessError(1, ["brew"]),
                            ):
                                with self.assertRaises(subprocess.CalledProcessError):
                                    macos_apps.install(
                                        argparse.Namespace(
                                            plan=str(plan),
                                            only=["Fixture Brew"],
                                            apply=True,
                                        )
                                    )
            self.assertFalse(list((root / "state").glob("install-*.json")))

    def test_unknown_plan_target_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self._plan(root)
            with mock.patch.object(
                macos_apps,
                "load_app_catalog",
                return_value=fixture_catalog(),
            ):
                with self.assertRaisesRegex(SystemExit, "App not found"):
                    macos_apps.install(
                        argparse.Namespace(
                            plan=str(plan),
                            only=["Not In Plan"],
                            apply=False,
                        )
                    )

    def test_more_than_five_targets_are_rejected_before_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plan = self._plan(root)
            with mock.patch.object(
                macos_apps,
                "load_app_catalog",
                return_value=fixture_catalog(),
            ):
                with mock.patch.object(macos_apps.subprocess, "run") as run:
                    with self.assertRaisesRegex(SystemExit, "at most five"):
                        macos_apps.install(
                            argparse.Namespace(
                                plan=str(plan),
                                only=["Fixture Brew"] * 6,
                                apply=True,
                            )
                        )
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
