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
