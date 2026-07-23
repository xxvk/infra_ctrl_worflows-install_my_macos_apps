#!/usr/bin/env python3
"""Validate that the tracked bootstrap definition is self-contained."""

from __future__ import annotations

import json
from pathlib import Path

from config_layers import load_app_catalog


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = [
    "SKILL.md",
    "README.md",
    "state/README.md",
    "state/locator.json",
    "Private/manifest.json",
    "Private/chrome-profiles.json",
    "Private/app-catalog-overlay.json",
    "Private/dock-order.json",
    "Private/system-preferences-values.json",
    "Private/keyboard.yaml",
    "Private/keyboards/logitech-k240-japanese-dictation.yaml",
    "references/app-catalog.json",
    "references/configuration-layers.md",
    "references/release-acceptance-matrix.json",
    "references/testing-contract.md",
    "references/mutation-contracts.json",
    "references/mutation-transaction-contract.md",
    "references/component-state-boundary.md",
    "references/source-policy.json",
    "references/source-policy.md",
    "references/clean-mac-acceptance.json",
    "references/clean-mac-acceptance-status.json",
    "references/clean-mac-release-acceptance.md",
    "references/runtime-and-developer-baseline.md",
    "references/permissions-preferences-bootstrap.md",
    "references/keyboard-and-logitech.md",
    "references/startup-dock-and-security.md",
    "references/application-installation-workflow.md",
    "references/application-maintenance.md",
    "settings/privacy.yaml",
    "settings/system-preferences.yaml",
    "settings/system-preferences-values.json",
    "settings/manual-actions.yaml",
    "settings/dock-order.json",
    "settings/keyboard.yaml",
    "settings/keyboards/logitech-k240-japanese-dictation.yaml",
    "references/icloud-git-integrity.md",
    "references/machine-local-state.md",
    "scripts/bootstrap_macos.py",
    "scripts/icloud_git_guard.py",
    "scripts/migrate_state.py",
    "scripts/state_paths.py",
    "scripts/macos_apps.py",
    "scripts/macos_permissions.py",
    "scripts/macos_permissions_cleanup.py",
    "scripts/macos_preferences.py",
    "scripts/validate_release_contract.py",
    "scripts/validate_skill_structure.py",
    "scripts/release_check.py",
    "scripts/transaction_contract.py",
    "scripts/validate_mutation_contracts.py",
    "scripts/component_state.py",
    "scripts/supply_chain.py",
    "scripts/clean_mac_acceptance.py",
    "scripts/audit_component_frontmatter.py",
    "tests/fixtures/macos_apps/catalog.json",
    "tests/fixtures/macos_apps/command-responses.json",
    "tests/test_app_catalog_validation.py",
    "tests/test_macos_apps.py",
    "tests/test_platform_fixtures.py",
    "tests/test_release_check.py",
    "tests/test_mutation_contracts.py",
    "tests/test_component_state.py",
    "tests/test_supply_chain.py",
    "tests/test_clean_mac_acceptance.py",
]


def main() -> int:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    catalog = load_app_catalog()
    guide_missing = []
    for app in catalog.get("apps", []):
        guide = app.get("guide")
        if guide and not (ROOT / guide).is_file():
            guide_missing.append({"name": app.get("name"), "guide": guide})
    result = {
        "mode": "tracked_definition_only",
        "state_read": False,
        "required_files": len(REQUIRED_FILES),
        "missing_files": missing,
        "catalog_apps": len(catalog.get("apps", [])),
        "missing_guides": guide_missing,
        "status": "passed" if not missing and not guide_missing else "failed",
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
