#!/usr/bin/env python3
"""Verify the DSH Computer Use companion is installed, sourced, and enabled.

Read-only check that reports three layers as independent evidence:

1. bundle  - /Applications/DSH Computer Use.app exists with the expected
             bundle identifier and a readable version;
2. catalog - the tracked mac-app catalog entry for DSH Computer Use stays
             consistent (name, cask, application path, bundle identifier);
3. plugin  - `dsh --profile web --dump-config` composes the
             `computer-use-host` and `computer-use-tool` loader rows exactly
             once (the plugin is enabled in the web profile).

The script never reads the TCC database, never changes a permission, never
writes profile configuration, and never sends a model request. TCC grant
status (Accessibility / Screen Recording) is intentionally reported as
`manual_verification_required`; macOS does not expose a portable read API and
the user grants those interactively.
"""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import re
import subprocess
import sys
from pathlib import Path

from state_paths import add_state_dir_argument, resolve_state_dir

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "references" / "mac-app-catalog.json"
APP_PATH = Path("/Applications/DSH Computer Use.app")
BUNDLE_ID = "tech.zrui.dsh-computer-use"
PLUGIN_ROWS = ("computer-use-host", "computer-use-tool")
TCC_SERVICES = ("Accessibility", "Screen Recording")


def load_catalog_entry() -> dict:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    for app in catalog.get("apps", []):
        if app.get("name") == "DSH Computer Use":
            return app
    return {}


def bundle_check() -> dict:
    if not APP_PATH.is_dir():
        return {"ok": False, "reason": "app bundle missing"}
    info = APP_PATH / "Contents" / "Info.plist"
    try:
        with info.open("rb") as handle:
            plist = plistlib.load(handle)
    except (OSError, plistlib.InvalidFileException) as exc:
        return {"ok": False, "reason": f"Info.plist unreadable: {exc}"}
    identifier = plist.get("CFBundleIdentifier")
    version = plist.get("CFBundleShortVersionString")
    return {
        "ok": identifier == BUNDLE_ID,
        "bundle_identifier": identifier,
        "version": version,
        "reason": "ok" if identifier == BUNDLE_ID else f"unexpected bundle id {identifier!r}",
    }


def catalog_check(entry: dict) -> dict:
    problems = []
    expected = {
        "name": "DSH Computer Use",
        "brew_cask": "zrui-c/tap/dsh-computer-use",
        "application_path": "/Applications/DSH Computer Use.app",
    }
    for key, want in expected.items():
        got = entry.get(key)
        if got != want:
            problems.append(f"{key}: expected {want!r}, got {got!r}")
    if BUNDLE_ID not in entry.get("bundle_identifiers", []):
        problems.append(f"bundle_identifiers missing {BUNDLE_ID!r}")
    return {"ok": not problems, "problems": problems}


def plugin_check() -> dict:
    command = ["dsh", "--profile", "web", "--dump-config"]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=False, timeout=60
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "reason": f"dsh dump-config failed: {exc}"}
    output = result.stdout or ""
    error = (result.stderr or "").strip()
    rows = {row: len(re.findall(rf"(?m)^- id: {re.escape(row)}\s*$", output)) for row in PLUGIN_ROWS}
    ok = result.returncode == 0 and all(count == 1 for count in rows.values())
    return {
        "ok": ok,
        "returncode": result.returncode,
        "rows": rows,
        "reason": (
            "ok"
            if ok
            else (
                f"dump-config exit {result.returncode}: {error[:200]}"
                if result.returncode != 0
                else f"unexpected row counts: {rows}"
            )
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_state_dir_argument(parser)
    args = parser.parse_args()
    resolve_state_dir(args.state_dir)  # validate override even though we write nothing

    bundle = bundle_check()
    entry = load_catalog_entry()
    catalog = catalog_check(entry)
    plugin = plugin_check()
    checks = {"bundle": bundle, "catalog": catalog, "plugin": plugin}
    report = {
        "schema_version": 1,
        "kind": "dsh_computer_use_verification",
        "captured_at": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
        "app": {"path": str(APP_PATH), "expected_bundle_identifier": BUNDLE_ID},
        "checks": checks,
        "tcc_status": {
            service: "manual_verification_required" for service in TCC_SERVICES
        },
        "policy": "Read-only verification; no permission grant, profile write, or model request was attempted.",
    }
    passed = all(check["ok"] for check in checks.values())
    report["status"] = "passed" if passed else "failed"
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
