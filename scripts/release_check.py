#!/usr/bin/env python3
"""Run the complete local release check, hermetic by default."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]


def build_checks(*, include_live_smoke: bool, python: str = sys.executable) -> list[tuple[str, list[str]]]:
    checks = [
        ("catalog-json", [python, "-m", "json.tool", "references/app-catalog.json"]),
        ("catalog-contract", [python, "scripts/validate_app_catalog.py"]),
        ("component-state-boundary", [python, "scripts/audit_component_frontmatter.py"]),
        ("supply-chain", [python, "scripts/supply_chain.py", "validate"]),
        ("clean-mac-acceptance", [python, "scripts/clean_mac_acceptance.py", "validate"]),
        ("unified-cli", [python, "scripts/macomrade.py", "validate", "--json"]),
        ("configuration-layers", [python, "scripts/config_layers.py", "audit"]),
        ("release-contract", [python, "scripts/validate_release_contract.py"]),
        ("mutation-contracts", [python, "scripts/validate_mutation_contracts.py"]),
        ("skill-structure", [python, "scripts/validate_skill_structure.py"]),
        ("bootstrap-definition", [python, "scripts/bootstrap_validate.py"]),
        (
            "hermetic-tests",
            [python, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        ),
        (
            "python-compile",
            [
                "/usr/bin/env",
                "PYTHONPYCACHEPREFIX=/tmp/install-macos-apps-release-pycache",
                python,
                "-m",
                "compileall",
                "-q",
                "scripts",
            ],
        ),
    ]
    if include_live_smoke:
        checks.append(("live-macos-smoke", ["/bin/bash", "tests/smoke.sh"]))
    return checks


def run_checks(
    checks: list[tuple[str, list[str]]],
    *,
    root: Path = ROOT,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    results = []
    for check_id, command in checks:
        completed = runner(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
        row = {
            "id": check_id,
            "command": command,
            "returncode": completed.returncode,
            "status": "passed" if completed.returncode == 0 else "failed",
        }
        if completed.returncode != 0:
            row["stdout"] = completed.stdout[-4000:]
            row["stderr"] = completed.stderr[-4000:]
        results.append(row)
        if completed.returncode != 0:
            break
    return {
        "status": "passed" if results and all(row["status"] == "passed" for row in results) else "failed",
        "mode": "live_macos" if any(row["id"] == "live-macos-smoke" for row in results) else "hermetic",
        "checks_run": len(results),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-live-smoke",
        action="store_true",
        help="also inspect the current Mac through tests/smoke.sh; still dry-run only",
    )
    args = parser.parse_args()
    result = run_checks(build_checks(include_live_smoke=args.include_live_smoke))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
