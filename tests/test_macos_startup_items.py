#!/usr/bin/env python3
"""Timeout and unavailable-state contracts for startup inventory."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import macos_startup_items as startup  # noqa: E402


class StartupItemsTests(unittest.TestCase):
    def test_timeout_is_unavailable_not_empty(self) -> None:
        with mock.patch.object(startup.shutil, "which", return_value="/usr/bin/sfltool"), mock.patch.object(
            startup,
            "run",
            return_value=subprocess.CompletedProcess([], 124, "", "timed out after 30s"),
        ):
            rows = startup.background_tasks()
        self.assertEqual(rows[0]["name"], "<unavailable>")
        self.assertIn("timed out", rows[0]["error"])
        self.assertFalse(rows[0]["removable"])


if __name__ == "__main__":
    unittest.main()
