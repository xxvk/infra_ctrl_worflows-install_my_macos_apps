#!/usr/bin/env python3
"""Hermetic App Adapter SDK contracts for WeChat and Claude VM."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import app_adapters  # noqa: E402


class AppAdapterTests(unittest.TestCase):
    def test_repository_adapter_catalog_is_valid(self) -> None:
        result = app_adapters.validate()
        self.assertEqual(result["status"], "passed", result["errors"])
        self.assertEqual(result["adapter_ids"], ["claude-vm", "wechat"])

    def test_wechat_inspection_is_metadata_only_and_plan_is_manual(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            root = home / "Library/Containers/com.tencent.xinWeChat"
            root.mkdir(parents=True)
            (root / "metadata.bin").write_bytes(b"fixture")
            inspection = app_adapters.inspect("wechat", home=home)
        self.assertEqual(inspection["adapter_id"], "wechat")
        self.assertEqual(inspection["privacy_boundary"], "metadata_only")
        self.assertEqual(inspection["roots"][0]["relative_path"], "Library/Containers/com.tencent.xinWeChat")
        self.assertGreater(inspection["roots"][0]["allocated_bytes"], 0)
        plan = app_adapters.plan("wechat", inspection=inspection)
        self.assertEqual(plan["execution_mode"], "manual_handoff_only")
        self.assertFalse(plan["operations"][0]["automatable"])
        self.assertNotIn("apply", plan)

    def test_claude_plan_delegates_to_existing_exact_mutations(self) -> None:
        report = {
            "vm_bundle_exists": True,
            "vm_bundle_bytes": 100,
            "images": [
                {"path": "/Users/example/Library/Application Support/Claude/vm_bundles/claudevm.bundle/rootfs.img", "exists": True, "bytes": 40},
                {"path": "/Users/example/Library/Application Support/Claude/vm_bundles/claudevm.bundle/sessiondata.img", "exists": True, "bytes": 60},
            ],
            "processes_holding_vm": [],
        }
        with mock.patch.object(app_adapters.claude_vm_cleanup, "report", return_value=report):
            inspection = app_adapters.inspect("claude-vm", home=Path("/Users/example"))
        plan = app_adapters.plan("claude-vm", inspection=inspection)
        self.assertEqual(plan["execution_mode"], "existing_transaction_only")
        self.assertEqual(
            [item["action_id"] for item in plan["operations"]],
            ["claude-vm.remove-images", "claude-vm.remove-bundle"],
        )
        self.assertTrue(all(item["confirmation_mode"] == "exact" for item in plan["operations"]))
        self.assertNotIn("/Users/example", str(inspection))


if __name__ == "__main__":
    unittest.main()
