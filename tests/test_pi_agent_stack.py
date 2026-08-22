#!/usr/bin/env python3
"""Pi Agent stack catalog and pnpm installation contracts."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import macos_apps  # noqa: E402
import pnpm_global  # noqa: E402
import supply_chain  # noqa: E402


class PiAgentStackTests(unittest.TestCase):
    def test_catalog_pins_two_ordered_core_packages(self) -> None:
        catalog = json.loads((ROOT / "references/mac-app-catalog.json").read_text())
        by_name = {app["name"]: app for app in catalog["apps"]}
        pi = by_name["Pi Coding Agent"]
        web = by_name["PI WEB"]

        self.assertEqual(pi["tier"], "core")
        self.assertEqual(pi["npm_package"], "@earendil-works/pi-coding-agent")
        self.assertEqual(pi["npm_version"], "0.84.2")
        self.assertEqual(pi["npm_install_client"], "pnpm")
        self.assertEqual(pi["npm_lifecycle_policy"], "ignore_all")
        self.assertEqual(web["tier"], "core")
        self.assertEqual(web["npm_package"], "@jmfederico/pi-web")
        self.assertEqual(web["npm_version"], "1.202608.1")
        self.assertEqual(web["npm_install_client"], "pnpm")
        self.assertEqual(web["npm_lifecycle_policy"], "allow_listed")
        self.assertEqual(web["npm_allowed_builds"], ["node-pty"])
        self.assertIn("Pi Coding Agent", web["install_after"])

    def test_source_policy_pins_registry_integrity_and_scripts(self) -> None:
        policy = json.loads((ROOT / "references/source-policy.json").read_text())
        npm = policy["npm_globals"]
        self.assertEqual(npm["@earendil-works/pi-coding-agent"]["version"], "0.84.2")
        self.assertTrue(npm["@earendil-works/pi-coding-agent"]["integrity"].startswith("sha512-"))
        self.assertEqual(npm["@earendil-works/pi-coding-agent"]["lifecycle_policy"], "ignore_all")
        self.assertEqual(npm["@jmfederico/pi-web"]["version"], "1.202608.1")
        self.assertTrue(npm["@jmfederico/pi-web"]["integrity"].startswith("sha512-"))
        self.assertEqual(npm["@jmfederico/pi-web"]["allowed_builds"], ["node-pty"])

    def test_pnpm_commands_apply_narrow_lifecycle_policies(self) -> None:
        common = {
            "npm_runtime_manager": "fnm",
            "npm_runtime_version": "24",
            "npm_install_client": "pnpm",
        }
        pi = {
            **common,
            "name": "Pi Coding Agent",
            "npm_package": "@earendil-works/pi-coding-agent",
            "npm_version": "0.84.2",
            "npm_lifecycle_policy": "ignore_all",
        }
        web = {
            **common,
            "name": "PI WEB",
            "npm_package": "@jmfederico/pi-web",
            "npm_version": "1.202608.1",
            "npm_lifecycle_policy": "allow_listed",
            "npm_allowed_builds": ["node-pty"],
        }
        self.assertEqual(
            macos_apps.install_commands(pi),
            [[
                "fnm", "exec", "--using=24", "pnpm", "add", "--global",
                "--ignore-scripts", "@earendil-works/pi-coding-agent@0.84.2",
            ]],
        )
        self.assertEqual(
            macos_apps.install_commands(web),
            [[
                "fnm", "exec", "--using=24", "pnpm", "add", "--global",
                "--allow-build=node-pty", "@jmfederico/pi-web@1.202608.1",
            ]],
        )

    def test_pnpm_presence_uses_runtime_scoped_inspection(self) -> None:
        app = {
            "name": "PI WEB",
            "npm_package": "@jmfederico/pi-web",
            "npm_version": "1.202608.1",
            "npm_runtime_manager": "fnm",
            "npm_runtime_version": "24",
            "npm_install_client": "pnpm",
        }
        with mock.patch.object(macos_apps.pnpm_global, "package_present", return_value=True) as present:
            self.assertTrue(macos_apps.npm_package_present(app))
        present.assert_called_once_with("24", "@jmfederico/pi-web", "1.202608.1")

    def test_pnpm_listing_and_runtime_prefix_are_normalized(self) -> None:
        payload = [{
            "dependencies": {
                "@jmfederico/pi-web": {"version": "1.202608.1"},
            }
        }]
        self.assertEqual(
            pnpm_global.parse_global_listing(payload),
            {"@jmfederico/pi-web": "1.202608.1"},
        )
        result = subprocess.CompletedProcess([], 0, stdout="/tmp/fnm-node\n", stderr="")
        runner = mock.Mock(return_value=result)
        env = pnpm_global.runtime_environment("24", runner=runner)
        self.assertEqual(env["PNPM_HOME"], "/tmp/fnm-node")
        self.assertEqual(
            runner.call_args.args[0],
            ["fnm", "exec", "--using=24", "npm", "prefix", "--global"],
        )

    def test_supply_inspection_reads_pnpm_owned_packages(self) -> None:
        policy = {
            "third_party_homebrew": {},
            "observed_unmanaged_homebrew": {},
            "npm_globals": {
                "@jmfederico/pi-web": {
                    "version": "1.202608.1",
                    "install_client": "pnpm",
                }
            },
        }

        def runner(command, **_kwargs):
            payload = [] if command[:2] == ["brew", "tap-info"] else {}
            return subprocess.CompletedProcess(command, 0, stdout=json.dumps(payload), stderr="")

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "policy.json"
            path.write_text(json.dumps(policy), encoding="utf-8")
            with mock.patch.object(
                supply_chain.pnpm_global,
                "global_packages",
                return_value={"@jmfederico/pi-web": "1.202608.1"},
            ):
                result = supply_chain.inspect_live(policy_path=path, runner=runner)
        self.assertEqual(result["npm_globals"][0]["install_client"], "pnpm")
        self.assertEqual(result["npm_globals"][0]["status"], "match")


if __name__ == "__main__":
    unittest.main()
