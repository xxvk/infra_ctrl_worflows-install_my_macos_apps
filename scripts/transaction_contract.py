#!/usr/bin/env python3
"""Load and stamp mutation transaction contracts."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "references/mutation-contracts.json"


def load_registry(path: Path = REGISTRY) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def contract_for(action_id: str, path: Path = REGISTRY) -> dict[str, Any]:
    matches = [
        action
        for action in load_registry(path).get("actions", [])
        if action.get("id") == action_id
    ]
    if len(matches) != 1:
        raise KeyError(f"mutation action id is not uniquely registered: {action_id}")
    return matches[0]


def transaction_metadata(
    action_id: str,
    *,
    phase: str,
    status: str,
    targets: list[str],
    path: Path = REGISTRY,
) -> dict[str, Any]:
    registry = load_registry(path)
    if phase not in registry.get("phase_order", []):
        raise ValueError(f"invalid transaction phase: {phase}")
    contract = contract_for(action_id, path)
    canonical = json.dumps(contract, sort_keys=True, separators=(",", ":")).encode()
    return {
        "schema_version": 1,
        "action_id": action_id,
        "phase": phase,
        "status": status,
        "targets": targets,
        "contract_sha256": hashlib.sha256(canonical).hexdigest(),
        "recorded_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }


def require_confirmation(action_id: str, provided: str, path: Path = REGISTRY) -> None:
    confirmation = contract_for(action_id, path).get("confirmation", {})
    expected = confirmation.get("value")
    if confirmation.get("mode") not in {"exact", "interactive_exact"}:
        return
    if provided != expected:
        raise ValueError(f'confirmation for {action_id} must be exactly "{expected}"')
