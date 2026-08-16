#!/usr/bin/env python3
"""Hermetic catalog schema contract tests."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/macos_apps/catalog.json"
sys.path.insert(0, str(ROOT / "scripts"))

import validate_app_catalog  # noqa: E402


class AppCatalogValidationTests(unittest.TestCase):
    def test_dsh_desktop_is_the_pinned_hairyf_tauri_dmg(self) -> None:
        catalog = json.loads((ROOT / "references/app-catalog.json").read_text())
        by_name = {app["name"]: app for app in catalog["apps"]}
        desktop = by_name["DeepSeek Harness Desktop"]
        self.assertEqual(desktop["tier"], "core")
        self.assertEqual(desktop["source"], "official_web")
        self.assertEqual(desktop["delivery_method"], "vendor-download")
        self.assertIsNone(desktop["brew_cask"])
        self.assertEqual(
            desktop["github_repository"],
            "https://github.com/hairyf/deepseek-harness-desktop",
        )
        self.assertEqual(desktop["github_release"], "v0.1.10")
        self.assertEqual(
            desktop["github_artifact"],
            "Deepseek.Harness.Desktop_0.1.10_aarch64.dmg",
        )
        self.assertEqual(
            desktop["artifact_sha256"],
            "645deba675e888b52601b023b244e1622c23deafc2ede16894ba301fe43097ac",
        )
        self.assertEqual(
            desktop["application_path"],
            "/Applications/Deepseek Harness Desktop.app",
        )
        self.assertEqual(
            desktop["bundle_identifiers"],
            ["io.github.hairyf.deepseek-harness-desktop"],
        )
        blocked = desktop["blocked_releases"]
        self.assertEqual(len(blocked), 1)
        self.assertEqual(
            blocked[0]["repository"],
            "https://github.com/anywhere-labs/deepseek-harness-desktop",
        )
        self.assertEqual(blocked[0]["release"], "v2.0.0")
        self.assertEqual(blocked[0]["status"], "blocked")
        self.assertIn("compatibility decision", blocked[0]["reason"])
        self.assertIn("cold-start", blocked[0]["reconsideration_gate"])
        self.assertEqual(desktop["guide"], "components/deepseek-harness-desktop.md")

        guide = (ROOT / desktop["guide"]).read_text(encoding="utf-8")
        self.assertIn("data/dsh", guide)
        self.assertIn("Never automate `xattr", guide)
        self.assertIn("separate deliverables", guide)

        policy = json.loads((ROOT / "references/source-policy.json").read_text())
        self.assertNotIn("jangrui/tap", policy["third_party_homebrew"])

    def test_xcodes_app_is_a_core_homebrew_cask(self) -> None:
        catalog = json.loads((ROOT / "references/app-catalog.json").read_text())
        by_name = {app["name"]: app for app in catalog["apps"]}
        xcodes = by_name["Xcodes"]
        self.assertEqual(xcodes["tier"], "core")
        self.assertEqual(xcodes["source"], "homebrew")
        self.assertEqual(xcodes["delivery_method"], "homebrew-cask")
        self.assertEqual(xcodes["brew_cask"], "xcodes-app")
        self.assertEqual(xcodes["guide"], "components/xcodes.md")

    def test_xcodes_guide_preserves_auth_activation_and_cleanup_recovery(self) -> None:
        guide = (ROOT / "components/xcodes.md").read_text(encoding="utf-8")
        for expected in (
            "HTTP 401",
            "Privileged Helper",
            "Make active",
            "xcode-select -p",
            "root-owned",
            "CONFIRM REMOVE OLD XCODE",
            "/Library/Developer",
        ):
            self.assertIn(expected, guide)

    def test_repository_node_runtime_and_npm_globals_use_fnm_24(self) -> None:
        catalog = json.loads((ROOT / "references/app-catalog.json").read_text())
        by_name = {app["name"]: app for app in catalog["apps"]}
        node = by_name["node"]
        self.assertEqual(node["runtime_manager"], "fnm")
        self.assertEqual(node["runtime_version"], "24")
        self.assertNotIn("brew_formula", node)
        npm = by_name["npm"]
        self.assertEqual(npm["runtime_manager"], "fnm")
        self.assertEqual(npm["runtime_version"], "24")
        self.assertNotIn("brew_formula", npm)
        for name in ("Cloudflare Wrangler", "WordPress Studio CLI"):
            self.assertEqual(by_name[name]["npm_runtime_manager"], "fnm")
            self.assertEqual(by_name[name]["npm_runtime_version"], "24")

    def test_fixture_catalog_is_structurally_valid(self) -> None:
        catalog = json.loads(FIXTURE.read_text())
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for app in catalog["apps"]:
                guide = root / app["guide"]
                guide.parent.mkdir(parents=True, exist_ok=True)
                guide.write_text("# fixture\n", encoding="utf-8")
            self.assertEqual(validate_app_catalog.validate(catalog, root=root), [])

    def test_duplicate_missing_source_and_invalid_store_url_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            guide = root / "components/example.md"
            guide.parent.mkdir(parents=True)
            guide.write_text("# fixture\n", encoding="utf-8")
            catalog = {
                "apps": [
                    {
                        "name": "Duplicate",
                        "category": "Test",
                        "tier": "core",
                        "guide": "components/example.md",
                        "app_store_url": "https://invalid.example/app",
                    },
                    {
                        "name": "Duplicate",
                        "category": "Test",
                        "tier": "invalid",
                        "guide": "components/example.md",
                    },
                ]
            }
            errors = validate_app_catalog.validate(catalog, root=root)
        self.assertTrue(any("duplicate name" in error for error in errors))
        self.assertTrue(any("no source field" in error for error in errors))
        self.assertTrue(any("does not look like an App Store URL" in error for error in errors))
        self.assertTrue(any("tier 'invalid'" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
