#!/usr/bin/env python3
"""Hermetic tests for public and iCloud-synced Private configuration layers."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import config_layers  # noqa: E402


class ConfigurationLayerTests(unittest.TestCase):
    def test_deep_merge_preserves_unknown_fields_and_replaces_arrays(self) -> None:
        base = {
            "known": {"enabled": False, "future": "preserve"},
            "items": ["base"],
        }
        overlay = {"known": {"enabled": True}, "items": ["private"]}

        merged = config_layers.deep_merge(base, overlay)

        self.assertEqual(
            merged,
            {
                "known": {"enabled": True, "future": "preserve"},
                "items": ["private"],
            },
        )
        self.assertFalse(base["known"]["enabled"])

    def test_repository_icloud_private_manifest_is_valid_when_present(self) -> None:
        if not config_layers.DEFAULT_MANIFEST.is_file():
            self.skipTest("public-only checkout has no iCloud Private overlay")
        result = config_layers.audit_manifest(environ={})
        manifest = json.loads(config_layers.DEFAULT_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["overlay_count"], len(manifest["overlays"]))
        observed = set(result["checked_overlays"]) | set(
            result["missing_optional_overlays"]
        )
        declared = {row["path"] for row in manifest["overlays"]}
        self.assertEqual(observed, declared)
        self.assertIn("Private/browser/organization.json", observed)

    def test_app_catalog_overlay_merges_by_name_and_renders_account_prompt(self) -> None:
        base = {
            "schema_version": 1,
            "apps": [
                {
                    "name": "Example",
                    "future_field": {"preserved": True},
                    "follow_up": ["Sign in with {preferred_account}"],
                }
            ],
        }
        overlay = {
            "schema_version": 1,
            "kind": "app_catalog_private_overlay",
            "apps": {"Example": {"preferred_account": "person@example.com"}},
        }

        merged = config_layers.apply_app_catalog_overlay(base, overlay)

        self.assertEqual(merged["apps"][0]["preferred_account"], "person@example.com")
        self.assertEqual(
            merged["apps"][0]["follow_up"],
            ["Sign in with person@example.com"],
        )
        self.assertEqual(merged["apps"][0]["future_field"], {"preserved": True})
        self.assertNotIn("preferred_account", base["apps"][0])

    def test_app_catalog_overlay_rejects_unknown_app(self) -> None:
        base = {"schema_version": 1, "apps": [{"name": "Known"}]}
        overlay = {
            "schema_version": 1,
            "kind": "app_catalog_private_overlay",
            "apps": {"Unknown": {"preferred_account": "person@example.com"}},
        }
        with self.assertRaises(config_layers.ConfigurationLayerError):
            config_layers.apply_app_catalog_overlay(base, overlay)

    def test_app_catalog_without_private_overlay_uses_public_base(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base_path = root / "catalog.json"
            base_path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "apps": [
                            {
                                "name": "Public",
                                "category": "Utility",
                                "tier": "optional",
                                "guide": "components/public.md",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = config_layers.load_app_catalog(
                base_path,
                root / "Private" / "app-catalog-overlay.json",
            )

            self.assertEqual(result["apps"][0]["name"], "Public")

    def test_public_only_environment_ignores_existing_private_overlay(self) -> None:
        result = config_layers.load_app_catalog(
            environ={"MACOMRADE_PUBLIC_ONLY": "1"},
        )
        base = config_layers.load_json(config_layers.DEFAULT_CATALOG)
        self.assertEqual(result, base)

    def test_legacy_locator_resolves_to_icloud_private_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "config").mkdir()
            (root / "Private").mkdir()
            target = root / "Private" / "profiles.json"
            target.write_text('{"profiles": []}', encoding="utf-8")
            locator = root / "config" / "profiles.json"
            locator.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "tracked_private_config_locator",
                        "private_path": "Private/profiles.json",
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(
                config_layers.resolve_config_path(locator, root=root),
                target.resolve(),
            )

    def test_yaml_locator_resolves_to_icloud_private_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "settings").mkdir()
            (root / "Private").mkdir()
            target = root / "Private" / "keyboard.yaml"
            target.write_text("dictation:\n  enabled: true\n", encoding="utf-8")
            locator = root / "settings" / "keyboard.yaml"
            locator.write_text(
                "schema_version: 1\n"
                "kind: tracked_private_config_locator\n"
                "private_path: Private/keyboard.yaml\n",
                encoding="utf-8",
            )

            self.assertEqual(
                config_layers.resolve_config_path(locator, root=root),
                target.resolve(),
            )

    def test_current_icloud_locator_kind_resolves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "settings").mkdir()
            (root / "Private").mkdir()
            target = root / "Private" / "dock.json"
            target.write_text('{"schema_version": 1}', encoding="utf-8")
            locator = root / "settings" / "dock.json"
            locator.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "icloud_private_config_locator",
                        "private_path": "Private/dock.json",
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(config_layers.resolve_config_path(locator, root=root), target.resolve())

    def test_private_directory_is_ignored_and_examples_are_tracked(self) -> None:
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("/Private/", ignore)
        self.assertTrue((ROOT / "examples/private/manifest.json").is_file())

    def test_default_missing_private_manifest_is_valid_public_only_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = config_layers.audit_manifest(root / "Private/manifest.json", root=root)
        self.assertEqual(result["status"], "valid")
        self.assertEqual(result["mode"], "public_only")
        self.assertEqual(result["overlay_count"], 0)

    def test_repository_personal_locators_resolve_to_private_files(self) -> None:
        if not config_layers.DEFAULT_MANIFEST.is_file():
            self.skipTest("public-only checkout has no iCloud Private overlay")
        mappings = {
            ROOT / "config" / "chrome-profiles.json": ROOT
            / "Private"
            / "chrome-profiles.json",
            ROOT / "settings" / "dock-order.json": ROOT
            / "Private"
            / "dock-order.json",
            ROOT / "settings" / "system-preferences-values.json": ROOT
            / "Private"
            / "system-preferences-values.json",
            ROOT / "settings" / "keyboard.yaml": ROOT
            / "Private"
            / "keyboard.yaml",
            ROOT
            / "settings"
            / "keyboards"
            / "logitech-k240-japanese-dictation.yaml": ROOT
            / "Private"
            / "keyboards"
            / "logitech-k240-japanese-dictation.yaml",
        }
        for locator, target in mappings.items():
            with self.subTest(locator=locator):
                self.assertEqual(
                    config_layers.resolve_config_path(locator),
                    target.resolve(),
                )

    def test_optional_missing_overlay_is_allowed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private = root / "Private"
            private.mkdir()
            manifest = private / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "icloud_private_overlay_manifest",
                        "merge_precedence": [
                            "public_base",
                            "icloud_private_overlay",
                        ],
                        "overlays": [
                            {
                                "id": "future",
                                "path": "Private/future.json",
                                "optional": True,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            result = config_layers.audit_manifest(manifest, root=root)
            self.assertEqual(result["missing_optional_overlays"], ["Private/future.json"])

    def test_secret_bearing_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private = root / "Private"
            private.mkdir()
            overlay = private / "account.json"
            overlay.write_text('{"access_token": "must-not-be-tracked"}', encoding="utf-8")
            manifest = private / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "tracked_private_overlay_manifest",
                        "merge_precedence": [
                            "public_base",
                            "tracked_private_overlay",
                        ],
                        "overlays": [
                            {"id": "account", "path": "Private/account.json"}
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(config_layers.ConfigurationLayerError):
                config_layers.audit_manifest(manifest, root=root)

    def test_secret_bearing_yaml_keys_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private = root / "Private"
            private.mkdir()
            overlay = private / "keyboard.yaml"
            overlay.write_text("profile:\n  access-token: forbidden\n", encoding="utf-8")
            manifest = private / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "tracked_private_overlay_manifest",
                        "merge_precedence": [
                            "public_base",
                            "tracked_private_overlay",
                        ],
                        "overlays": [
                            {
                                "id": "keyboard",
                                "path": "Private/keyboard.yaml",
                                "format": "yaml",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(config_layers.ConfigurationLayerError):
                config_layers.audit_manifest(manifest, root=root)

    def test_overlay_path_cannot_escape_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            private = root / "Private"
            private.mkdir()
            manifest = private / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "kind": "tracked_private_overlay_manifest",
                        "merge_precedence": [
                            "public_base",
                            "tracked_private_overlay",
                        ],
                        "overlays": [{"id": "escape", "path": "../outside.json"}],
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(config_layers.ConfigurationLayerError):
                config_layers.audit_manifest(manifest, root=root)


if __name__ == "__main__":
    unittest.main()
