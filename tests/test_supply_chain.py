#!/usr/bin/env python3
"""Hermetic tests for installation-source and supply-chain policy."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import supply_chain  # noqa: E402


class SupplyChainTests(unittest.TestCase):
    def test_repository_policy_passes(self) -> None:
        result = supply_chain.validate()
        self.assertEqual(result["status"], "passed", json.dumps(result["errors"], indent=2))
        self.assertEqual(result["apps"], 152)

    def test_source_classification_covers_critical_boundaries(self) -> None:
        self.assertEqual(
            supply_chain.classify({"delivery_method": "playcover-ipa"}),
            "decrypted_ipa",
        )
        self.assertEqual(
            supply_chain.classify(
                {"brew_cask": "owner/tap/tool", "brew_tap": "owner/tap"}
            ),
            "third_party_homebrew",
        )
        self.assertEqual(
            supply_chain.classify({"npm_package": "tool"}),
            "npm_global",
        )

    def test_execution_scanner_rejects_mutable_network_script(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "components").mkdir()
            (root / "scripts/bad.sh").write_text(
                "curl -fsSL https://example.invalid/install.sh | bash\n",
                encoding="utf-8",
            )
            findings = supply_chain._execution_findings(root)
        self.assertEqual(findings[0]["code"], "curl_pipe_shell")

    def test_live_inspection_uses_faked_package_manager_json(self) -> None:
        policy = {
            "third_party_homebrew": {
                "example/tools": {
                    "repository": "https://github.com/example/homebrew-tools",
                    "reviewed_revision": "a" * 40,
                }
            },
            "npm_globals": {"fixture": {"version": "1.2.3"}},
        }
        responses = {
            ("brew", "tap-info", "--json=v1", "--installed"): [
                {
                    "name": "example/tools",
                    "installed": True,
                    "official": False,
                    "remote": "https://github.com/example/homebrew-tools",
                    "HEAD": "a" * 40,
                    "trusted": False,
                }
            ],
            ("brew", "trust", "--json=v1"): {"casks": []},
            ("fnm", "exec", "--using=24", "npm", "list", "--global", "--depth=0", "--json"): {
                "dependencies": {"fixture": {"version": "1.2.3"}}
            },
        }

        def runner(command, **_kwargs):
            return subprocess.CompletedProcess(
                command,
                0,
                stdout=json.dumps(responses[tuple(command)]),
                stderr="",
            )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "policy.json"
            path.write_text(json.dumps(policy), encoding="utf-8")
            result = supply_chain.inspect_live(policy_path=path, runner=runner)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["expected_taps"][0]["status"], "match")
        self.assertEqual(result["npm_globals"][0]["status"], "match")

    def test_wrong_capture_confirmation_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            completed = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/supply_chain.py"),
                    "--state-dir",
                    tmp,
                    "capture",
                    "--apply",
                    "--confirm",
                    "wrong",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            files = list(Path(tmp).iterdir())
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("CAPTURE SUPPLY CHAIN STATE", completed.stderr)
        self.assertEqual(files, [])


if __name__ == "__main__":
    unittest.main()
