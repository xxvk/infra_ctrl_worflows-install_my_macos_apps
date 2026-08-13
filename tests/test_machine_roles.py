#!/usr/bin/env python3
"""Hermetic contracts for composable machine-role selection."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import machine_roles  # noqa: E402


def catalog() -> dict:
    return {
        "apps": [
            {"name": "Core App", "tier": "core"},
            {"name": "Developer Option", "tier": "optional"},
            {"name": "Robot Option", "tier": "optional"},
        ]
    }


def roles() -> dict:
    return {
        "schema_version": 1,
        "kind": "machine_role_catalog",
        "base_role": "base",
        "roles": {
            "base": {
                "description_key": "role.base.description",
                "inherits": [],
                "include_apps": [],
                "exclude_apps": [],
            },
            "compact": {
                "description_key": "role.compact.description",
                "inherits": ["base"],
                "include_apps": [],
                "exclude_apps": [],
            },
            "expanded": {
                "description_key": "role.expanded.description",
                "inherits": ["base"],
                "include_apps": [],
                "exclude_apps": [],
            },
            "developer": {
                "description_key": "role.developer.description",
                "inherits": ["base"],
                "include_apps": ["Developer Option"],
                "exclude_apps": [],
            },
            "robotics": {
                "description_key": "role.robotics.description",
                "inherits": ["developer"],
                "include_apps": ["Robot Option"],
                "exclude_apps": ["Developer Option"],
            },
        },
    }


class MachineRoleTests(unittest.TestCase):
    def test_real_catalog_is_valid(self) -> None:
        result = machine_roles.validate()
        self.assertEqual(result["status"], "passed", result["errors"])

    def test_roles_inherit_and_explain_selected_apps(self) -> None:
        selection = machine_roles.resolve(
            roles(),
            catalog(),
            ["compact", "robotics"],
            storage_gb=256,
        )
        self.assertEqual(selection["roles"], ["base", "compact", "developer", "robotics"])
        self.assertEqual(selection["selected_apps"], ["Core App", "Robot Option"])
        self.assertEqual(selection["reasons"]["Core App"], ["base"])
        self.assertEqual(selection["reasons"]["Robot Option"], ["robotics"])
        self.assertIn("Developer Option", selection["excluded_apps"])

    def test_auto_selects_capacity_role_and_explicit_overrides_win(self) -> None:
        selection = machine_roles.resolve(
            roles(),
            catalog(),
            ["auto", "developer"],
            storage_gb=1024,
            include_apps=["Robot Option"],
            exclude_apps=["Core App"],
        )
        self.assertEqual(selection["roles"], ["base", "expanded", "developer"])
        self.assertEqual(selection["selected_apps"], ["Developer Option", "Robot Option"])
        self.assertEqual(selection["reasons"]["Robot Option"], ["explicit_include"])
        self.assertIn("Core App", selection["excluded_apps"])

    def test_unknown_role_and_catalog_app_are_rejected(self) -> None:
        with self.assertRaisesRegex(machine_roles.MachineRoleError, "unknown role"):
            machine_roles.resolve(roles(), catalog(), ["unknown"], storage_gb=256)

        invalid = roles()
        invalid["roles"]["developer"]["include_apps"] = ["Not Cataloged"]
        with self.assertRaisesRegex(machine_roles.MachineRoleError, "unknown catalog app"):
            machine_roles.validate_catalog(invalid, catalog())


if __name__ == "__main__":
    unittest.main()
