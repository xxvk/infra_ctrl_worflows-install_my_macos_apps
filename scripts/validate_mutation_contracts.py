#!/usr/bin/env python3
"""Validate complete transaction contracts for every supported mutation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from transaction_contract import load_registry


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FIELDS = {
    "id", "script", "selector", "risk", "targets", "inspect", "plan",
    "confirmation", "apply", "verify", "record", "backup_rollback",
    "interruption", "idempotency",
}
ALLOWED_RISKS = {"low", "medium", "high", "destructive"}
REQUIRED_ACTION_IDS = {
    "apps.install", "icloud.materialize", "state.materialize", "state.migrate",
    "state.cleanup", "preferences.apply", "capacities.remove-app",
    "claude-vm.remove-images", "claude-vm.remove-bundle", "claude-vm.lock",
    "claude-vm.unlock", "docker-desktop.remove-data",
    "openclaw.remove-leftovers", "tcc.reset", "dotfiles.link",
    "drift-schedule.install", "drift-schedule.uninstall",
    "skill-runtime.uninstall", "startup-items.disable", "dock.save-baseline",
    "component-state.migrate", "supply-chain.capture",
    "clean-mac.session-update", "clean-mac.finalize",
    "schema.migrate-write",
    "diagnostics.export",
}


def validate(root: Path = ROOT) -> dict[str, Any]:
    root = root.resolve()
    registry = load_registry(root / "references/mutation-contracts.json")
    errors = []
    if registry.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    if registry.get("phase_order") != ["inspect", "plan", "confirm", "apply", "verify", "record"]:
        errors.append("phase_order is invalid")
    actions = registry.get("actions")
    if not isinstance(actions, list):
        actions = []
        errors.append("actions must be a list")
    seen = set()
    for index, action in enumerate(actions):
        if not isinstance(action, dict):
            errors.append(f"action[{index}] must be an object")
            continue
        action_id = action.get("id")
        missing = sorted(REQUIRED_FIELDS - set(action))
        if missing:
            errors.append(f"{action_id or index} missing fields: {', '.join(missing)}")
        if action_id in seen:
            errors.append(f"duplicate action id: {action_id}")
        seen.add(action_id)
        script = root / str(action.get("script", ""))
        if not script.is_file():
            errors.append(f"{action_id} script not found: {action.get('script')}")
            continue
        source = script.read_text(encoding="utf-8")
        if source.count(str(action_id)) < 2:
            errors.append(
                f"{action_id} must be both declared and emitted by "
                f"{action.get('script')}"
            )
        risk = action.get("risk")
        if risk not in ALLOWED_RISKS:
            errors.append(f"{action_id} has invalid risk: {risk}")
        confirmation = action.get("confirmation")
        if not isinstance(confirmation, dict) or not confirmation.get("mode") or not confirmation.get("value"):
            errors.append(f"{action_id} confirmation contract is incomplete")
        elif risk in {"high", "destructive"}:
            if confirmation.get("mode") not in {"exact", "interactive_exact"}:
                errors.append(f"{action_id} high-risk confirmation is not exact")
            elif str(confirmation.get("value")) not in source:
                errors.append(f"{action_id} exact confirmation token is absent from script")
        for field in REQUIRED_FIELDS - {"id", "script", "confirmation", "risk"}:
            if not action.get(field):
                errors.append(f"{action_id} has empty {field}")
    missing_actions = sorted(REQUIRED_ACTION_IDS - seen)
    extra_actions = sorted(seen - REQUIRED_ACTION_IDS)
    if missing_actions:
        errors.append("unregistered mutation actions: " + ", ".join(missing_actions))
    if extra_actions:
        errors.append("unexpected mutation actions: " + ", ".join(extra_actions))
    return {
        "status": "passed" if not errors else "failed",
        "action_count": len(actions),
        "required_action_count": len(REQUIRED_ACTION_IDS),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    result = validate(args.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
