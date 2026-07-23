#!/usr/bin/env python3
# Mutation action IDs: clean-mac.session-update, clean-mac.finalize
"""Validate and maintain a machine-local Clean-Mac acceptance session."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any, Callable

from state_paths import add_state_dir_argument, resolve_state_dir


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "references/clean-mac-acceptance.json"
STATUS_PATH = ROOT / "references/clean-mac-acceptance-status.json"
SESSION_UPDATE_CONFIRMATION = "UPDATE CLEAN MAC ACCEPTANCE"
FINALIZE_CONFIRMATION = "FINALIZE CLEAN MAC ACCEPTANCE"
OUTCOMES = {"passed", "blocked", "failed"}
FORBIDDEN_EVIDENCE_KEYS = {
    "access_token",
    "api_key",
    "cookie",
    "password",
    "private_key",
    "recovery_code",
    "refresh_token",
    "session_token",
}
EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
USER_PATH = re.compile(r"/Users/[^/\s]+")
SECRET_TEXT = re.compile(
    r"(?i)\b(?:bearer\s+[A-Za-z0-9._~+/=-]{12,}|sk-[A-Za-z0-9_-]{12,})"
)
FULL_COMMIT = re.compile(r"^[0-9a-f]{40}$")


class AcceptanceError(RuntimeError):
    pass


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def redact_text(value: str) -> str:
    value = EMAIL.sub("<redacted-email>", value)
    value = USER_PATH.sub("<HOME>", value)
    return SECRET_TEXT.sub("<redacted-secret>", value)


def sanitize_evidence(value: Any, *, path: str = "$") -> Any:
    if isinstance(value, dict):
        result = {}
        for key, child in value.items():
            normalized = str(key).casefold().replace("-", "_")
            if normalized in FORBIDDEN_EVIDENCE_KEYS:
                raise AcceptanceError(f"evidence contains prohibited key: {path}.{key}")
            result[key] = sanitize_evidence(child, path=f"{path}.{key}")
        return result
    if isinstance(value, list):
        return [
            sanitize_evidence(child, path=f"{path}[{index}]")
            for index, child in enumerate(value)
        ]
    if isinstance(value, str):
        return redact_text(value)
    return value


def read_sanitized_evidence(path: Path) -> Any:
    if path.suffix.casefold() != ".json":
        raise AcceptanceError("acceptance evidence must be JSON")
    try:
        if path.stat().st_size > 10 * 1024 * 1024:
            raise AcceptanceError("acceptance evidence exceeds the 10 MiB limit")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise AcceptanceError(f"cannot read JSON evidence: {exc}") from exc
    return sanitize_evidence(value)


def _manual_evidence_valid(value: Any, gate_id: str, outcome: str) -> bool:
    return (
        isinstance(value, dict)
        and value.get("schema_version") == 1
        and value.get("kind") == "clean_mac_gate_evidence"
        and value.get("gate_id") == gate_id
        and value.get("outcome") == outcome
        and isinstance(value.get("observed_at"), str)
        and bool(value.get("observed_at"))
        and isinstance(value.get("assertions"), list)
        and bool(value.get("assertions"))
        and all(isinstance(item, str) and item for item in value["assertions"])
        and isinstance(value.get("accepted_exceptions", []), list)
    )


def validate_evidence_semantics(
    definition: dict[str, Any],
    values: list[Any],
    *,
    outcome: str,
) -> None:
    gate_id = definition["id"]
    expected_kind = definition.get("evidence_kind")
    if outcome != "passed" or expected_kind == "clean_mac_gate_evidence":
        if not all(_manual_evidence_valid(value, gate_id, outcome) for value in values):
            raise AcceptanceError(
                f"{gate_id}: evidence must use the clean_mac_gate_evidence envelope"
            )
        phases = definition.get("required_phases", [])
        if phases:
            observed = [value.get("phase") for value in values]
            if sorted(observed) != sorted(phases):
                raise AcceptanceError(
                    f"{gate_id}: evidence phases must be {', '.join(phases)}"
                )
        return
    if len(values) < definition.get("required_evidence", 0):
        raise AcceptanceError(f"{gate_id}: insufficient semantic evidence")
    value = values[0] if values else {}
    if expected_kind == "release_check_result":
        results = value.get("results", []) if isinstance(value, dict) else []
        required_ids = {"clean-mac-acceptance", "release-contract", "hermetic-tests"}
        observed_ids = {
            row.get("id")
            for row in results
            if isinstance(row, dict) and row.get("status") == "passed"
        }
        valid = (
            isinstance(value, dict)
            and value.get("status") == "passed"
            and value.get("mode") == "hermetic"
            and required_ids <= observed_ids
            and all(
                isinstance(row, dict) and row.get("status") == "passed"
                for row in results
            )
        )
    elif expected_kind == "bootstrap_assessment_result":
        steps = value.get("steps", []) if isinstance(value, dict) else []
        required_names = {
            "tracked_definition_validation",
            "app_scan",
            "app_plan",
            "permission_inventory",
            "preference_baseline_and_check",
        }
        valid = (
            isinstance(value, dict)
            and required_names
            <= {
                row.get("name")
                for row in steps
                if isinstance(row, dict)
                and row.get("status") in {"passed", "review_required"}
            }
        )
    elif expected_kind == "supply_chain_capture_result":
        valid = (
            isinstance(value, dict)
            and value.get("action_id") == "supply-chain.capture"
            and value.get("status") == "passed"
            and value.get("record_status") == "recorded"
        )
    elif expected_kind == "bootstrap_verify_result":
        drift = value.get("app_drift", {}) if isinstance(value, dict) else {}
        returncodes = value.get("step_returncodes", {}) if isinstance(value, dict) else {}
        valid = (
            isinstance(value, dict)
            and value.get("mode") == "read_only_final_drift_check"
            and drift.get("missing_core") == []
            and drift.get("source_mismatches") == []
            and bool(returncodes)
            and all(code == 0 for code in returncodes.values())
        )
    else:
        valid = False
    if not valid:
        raise AcceptanceError(
            f"{gate_id}: evidence does not satisfy {expected_kind}"
        )


def evidence_template(definition: dict[str, Any], *, phase: str | None = None) -> dict[str, Any]:
    value = {
        "schema_version": 1,
        "kind": "clean_mac_gate_evidence",
        "gate_id": definition["id"],
        "outcome": "passed",
        "observed_at": "<ISO-8601 timestamp>",
        "assertions": ["<specific verified result>"],
        "accepted_exceptions": [],
    }
    if definition.get("required_phases"):
        value["phase"] = phase or f"<one of: {', '.join(definition['required_phases'])}>"
    return value


def contract_hash(path: Path = CONTRACT_PATH) -> str:
    return sha256_path(path)


def validate_contract(
    contract_path: Path = CONTRACT_PATH,
    status_path: Path = STATUS_PATH,
) -> dict[str, Any]:
    errors = []
    try:
        contract = load_json(contract_path)
        status = load_json(status_path)
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "failed", "errors": [str(exc)]}
    if contract.get("schema_version") != 1:
        errors.append("contract schema_version must be 1")
    if contract.get("kind") != "clean_mac_release_acceptance_contract":
        errors.append("contract kind is invalid")
    if contract.get("release_version") != "0.1.0":
        errors.append("contract release_version must be 0.1.0")
    for field in (
        "clean_machine_attestation",
        "session_update_confirmation",
        "finalize_confirmation",
    ):
        if not contract.get(field):
            errors.append(f"contract missing {field}")
    gates = contract.get("gates")
    if not isinstance(gates, list) or not gates:
        errors.append("contract gates must be a non-empty list")
        gates = []
    seen = set()
    for index, gate in enumerate(gates):
        gate_id = gate.get("id")
        if not re.fullmatch(r"CM-\d{2}", str(gate_id or "")):
            errors.append(f"gate[{index}] has invalid id")
        elif gate_id in seen:
            errors.append(f"duplicate gate id: {gate_id}")
        seen.add(gate_id)
        if not gate.get("name") or not gate.get("mode") or not gate.get("command_hint"):
            errors.append(f"{gate_id or index}: incomplete gate")
        if not gate.get("evidence_kind"):
            errors.append(f"{gate_id or index}: missing evidence_kind")
        if not isinstance(gate.get("required_evidence"), int) or gate.get("required_evidence") < 0:
            errors.append(f"{gate_id or index}: invalid required_evidence")
    if seen and seen != {f"CM-{number:02d}" for number in range(1, 14)}:
        errors.append("contract must define exactly CM-01 through CM-13")
    if status.get("schema_version") != 1:
        errors.append("status schema_version must be 1")
    if status.get("release_version") != contract.get("release_version"):
        errors.append("status release_version must match contract")
    hardware_status = status.get("hardware_run_status")
    if hardware_status not in {"blocked_external", "passed"}:
        errors.append("hardware_run_status must be blocked_external or passed")
    if hardware_status == "passed":
        if not re.fullmatch(r"[0-9a-f]{64}", str(status.get("reviewed_session_sha256", ""))):
            errors.append("passed hardware status requires reviewed_session_sha256")
        if not status.get("reviewed_at"):
            errors.append("passed hardware status requires reviewed_at")
    return {
        "status": "passed" if not errors else "failed",
        "gate_count": len(gates),
        "hardware_run_status": hardware_status,
        "contract_sha256": contract_hash(contract_path) if contract_path.is_file() else None,
        "errors": errors,
    }


def run_text(
    command: list[str],
    *,
    root: Path = ROOT,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str:
    completed = runner(
        command,
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode:
        raise AcceptanceError(
            f"command failed ({completed.returncode}): {' '.join(command)}: "
            f"{redact_text(completed.stderr.strip())}"
        )
    return completed.stdout.strip()


def inspect_source(
    *,
    root: Path = ROOT,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> dict[str, Any]:
    guard = run_text(
        [
            sys.executable,
            "scripts/icloud_git_guard.py",
            "inspect",
            "--repo",
            ".",
        ],
        root=root,
        runner=runner,
    )
    if not re.search(r"^status:\s*ready\s*$", guard, flags=re.MULTILINE):
        raise AcceptanceError("iCloud Git guard did not report ready")
    dirty = run_text(["git", "status", "--porcelain"], root=root, runner=runner)
    commit = run_text(["git", "rev-parse", "HEAD"], root=root, runner=runner)
    if dirty:
        raise AcceptanceError("Clean-Mac acceptance requires a clean Git worktree")
    if not FULL_COMMIT.fullmatch(commit):
        raise AcceptanceError("Clean-Mac acceptance requires one full Git commit")
    return {
        "commit": commit,
        "worktree": "clean",
        "icloud_git_guard": "ready",
    }


def atomic_write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def session_path(value: Path) -> Path:
    return value / "session.json" if value.is_dir() else value


def new_session(
    output_dir: Path,
    *,
    attestation: str,
    root: Path = ROOT,
    contract_path: Path = CONTRACT_PATH,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    now: Callable[[], dt.datetime] = lambda: dt.datetime.now(dt.timezone.utc),
    session_id: str | None = None,
    write: bool = True,
) -> dict[str, Any]:
    contract = load_json(contract_path)
    if attestation != contract.get("clean_machine_attestation"):
        raise AcceptanceError("clean-machine attestation does not match the contract")
    if output_dir.exists():
        raise AcceptanceError(f"acceptance session already exists: {output_dir}")
    source = inspect_source(root=root, runner=runner)
    macos_version = run_text(["sw_vers", "-productVersion"], root=root, runner=runner)
    architecture = run_text(["uname", "-m"], root=root, runner=runner)
    captured = now().isoformat()
    gates = []
    for gate in contract["gates"]:
        initial = "passed" if gate["id"] in {"CM-01", "CM-02"} else "pending"
        gates.append(
            {
                "id": gate["id"],
                "name": gate["name"],
                "outcome": initial,
                "evidence": [],
                "note": (
                    "Explicit eligible-hardware attestation recorded."
                    if gate["id"] == "CM-01"
                    else "Clean worktree and full source commit recorded."
                    if gate["id"] == "CM-02"
                    else ""
                ),
                "updated_at": captured if initial == "passed" else None,
                "history": [],
            }
        )
    result = {
        "schema_version": 1,
        "kind": "clean_mac_acceptance_session",
        "action_id": "clean-mac.session-update",
        "session_id": session_id or str(uuid.uuid4()),
        "release_version": contract["release_version"],
        "status": "in_progress",
        "created_at": captured,
        "updated_at": captured,
        "machine": {
            "disposition": contract["eligible_machine_disposition"],
            "attestation": attestation,
            "macos_version": macos_version,
            "architecture": architecture,
        },
        "source": {
            **source,
            "contract_sha256": contract_hash(contract_path),
        },
        "gates": gates,
        "policy": contract["requirements"]["acceptance_effect"],
    }
    if write:
        output_dir.mkdir(parents=True)
        (output_dir / "evidence").mkdir()
        atomic_write(output_dir / "session.json", result)
    return result


def read_session(value: Path) -> tuple[Path, dict[str, Any]]:
    path = session_path(value)
    try:
        session = load_json(path)
    except (OSError, json.JSONDecodeError) as exc:
        raise AcceptanceError(f"cannot read acceptance session: {exc}") from exc
    if session.get("kind") != "clean_mac_acceptance_session":
        raise AcceptanceError("invalid acceptance session kind")
    return path, session


def evidence_copy(
    source: Path,
    destination: Path,
    *,
    artifact_id: str,
    write: bool = True,
) -> dict[str, Any]:
    sanitized = read_sanitized_evidence(source)
    target = destination / "evidence" / f"{artifact_id}.json"
    encoded = json.dumps(sanitized, ensure_ascii=False, indent=2) + "\n"
    if write:
        temporary = target.with_suffix(".json.tmp")
        temporary.write_text(encoded, encoding="utf-8")
        os.replace(temporary, target)
    return {
        "artifact_id": artifact_id,
        "source_sha256": sha256_path(source),
        "bundle_sha256": hashlib.sha256(encoded.encode("utf-8")).hexdigest(),
        "bundle_bytes": len(encoded.encode("utf-8")),
        "bundle_file": f"evidence/{artifact_id}.json",
    }


def record_gate(
    value: Path,
    *,
    gate_id: str,
    outcome: str,
    evidence_paths: list[Path],
    note: str,
    contract_path: Path = CONTRACT_PATH,
    now: Callable[[], dt.datetime] = lambda: dt.datetime.now(dt.timezone.utc),
    write: bool = True,
) -> dict[str, Any]:
    path, session = read_session(value)
    if session.get("status") != "in_progress":
        raise AcceptanceError("only an in-progress session can be updated")
    contract = load_json(contract_path)
    definitions = {gate["id"]: gate for gate in contract["gates"]}
    if gate_id not in definitions:
        raise AcceptanceError(f"unknown acceptance gate: {gate_id}")
    if gate_id in {"CM-01", "CM-02"}:
        raise AcceptanceError(f"{gate_id} is immutable after session initialization")
    if outcome not in OUTCOMES:
        raise AcceptanceError(f"invalid gate outcome: {outcome}")
    required = definitions[gate_id]["required_evidence"]
    if outcome == "passed" and len(evidence_paths) < required:
        raise AcceptanceError(
            f"{gate_id} requires at least {required} evidence artifact(s)"
        )
    sanitized_values = [
        read_sanitized_evidence(source.expanduser().resolve())
        for source in evidence_paths
    ]
    validate_evidence_semantics(
        definitions[gate_id],
        sanitized_values,
        outcome=outcome,
    )
    gate = next(row for row in session["gates"] if row["id"] == gate_id)
    timestamp = now().isoformat()
    gate["history"].append(
        {
            "outcome": gate["outcome"],
            "evidence": gate["evidence"],
            "note": gate["note"],
            "updated_at": gate["updated_at"],
        }
    )
    revision = len(gate["history"])
    artifact_specs = [
        (
            source.expanduser().resolve(),
            f"{gate_id}-r{revision:02d}-{index:02d}",
        )
        for index, source in enumerate(evidence_paths, start=1)
    ]
    artifacts = [
        evidence_copy(
            source,
            path.parent,
            artifact_id=artifact_id,
            write=False,
        )
        for source, artifact_id in artifact_specs
    ]
    if write:
        written: list[Path] = []
        try:
            artifacts = []
            for source, artifact_id in artifact_specs:
                artifact = evidence_copy(
                    source,
                    path.parent,
                    artifact_id=artifact_id,
                    write=True,
                )
                artifacts.append(artifact)
                written.append(path.parent / artifact["bundle_file"])
        except Exception:
            for target in written:
                target.unlink(missing_ok=True)
            raise
    gate.update(
        {
            "outcome": outcome,
            "evidence": artifacts,
            "note": redact_text(note)[:1000],
            "updated_at": timestamp,
        }
    )
    session["action_id"] = "clean-mac.session-update"
    session["updated_at"] = timestamp
    if write:
        atomic_write(path, session)
    return session


def finalize_session(
    value: Path,
    *,
    root: Path = ROOT,
    contract_path: Path = CONTRACT_PATH,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    now: Callable[[], dt.datetime] = lambda: dt.datetime.now(dt.timezone.utc),
    write: bool = True,
) -> dict[str, Any]:
    path, session = read_session(value)
    contract = load_json(contract_path)
    if session.get("status") != "in_progress":
        raise AcceptanceError("only an in-progress session can be finalized")
    definitions = {gate["id"]: gate for gate in contract["gates"]}
    errors = []
    if session.get("release_version") != contract.get("release_version"):
        errors.append("session release version differs from the contract")
    machine = session.get("machine", {})
    if (
        not isinstance(machine, dict)
        or machine.get("disposition") != contract.get("eligible_machine_disposition")
        or machine.get("attestation") != contract.get("clean_machine_attestation")
    ):
        errors.append("eligible-hardware attestation is invalid")
    gates = session.get("gates", [])
    expected_order = [gate["id"] for gate in contract["gates"]]
    observed_order = [
        gate.get("id") if isinstance(gate, dict) else None
        for gate in gates
    ] if isinstance(gates, list) else []
    if observed_order != expected_order:
        errors.append("gate set or order differs from the contract")
    artifact_ids: set[str] = set()
    for gate in gates if isinstance(gates, list) else []:
        if not isinstance(gate, dict):
            errors.append("session contains a non-object gate")
            continue
        gate_id = gate.get("id")
        required = definitions.get(gate_id, {}).get("required_evidence", 0)
        evidence = gate.get("evidence")
        if not isinstance(evidence, list):
            errors.append(f"{gate_id}: evidence must be a list")
            evidence = []
        if gate.get("outcome") != "passed":
            errors.append(f"{gate_id}: {gate.get('outcome')}")
        elif len(evidence) < required:
            errors.append(f"{gate_id}: under-evidenced")
        semantic_values = []
        for artifact in evidence:
            artifact_valid = True
            if not isinstance(artifact, dict):
                errors.append(f"{gate_id}: evidence item must be an object")
                continue
            artifact_id = artifact.get("artifact_id")
            relative = artifact.get("bundle_file")
            if (
                not isinstance(artifact_id, str)
                or artifact_id in artifact_ids
                or not artifact_id.startswith(f"{gate_id}-")
            ):
                errors.append(f"{gate_id}: invalid or duplicate artifact id")
                continue
            artifact_ids.add(artifact_id)
            if relative != f"evidence/{artifact_id}.json":
                errors.append(f"{artifact_id}: bundle path is invalid")
                continue
            if not re.fullmatch(r"[0-9a-f]{64}", str(artifact.get("source_sha256", ""))):
                errors.append(f"{artifact_id}: source SHA-256 is invalid")
                artifact_valid = False
            if not re.fullmatch(r"[0-9a-f]{64}", str(artifact.get("bundle_sha256", ""))):
                errors.append(f"{artifact_id}: bundle SHA-256 is invalid")
                artifact_valid = False
            artifact_path = (path.parent / relative).resolve()
            try:
                artifact_path.relative_to(path.parent.resolve())
            except ValueError:
                errors.append(f"{artifact_id}: bundle path escapes the session")
                continue
            if not artifact_path.is_file():
                errors.append(f"{artifact_id}: bundle file is missing")
                continue
            if artifact_path.stat().st_size != artifact.get("bundle_bytes"):
                errors.append(f"{artifact_id}: bundle size mismatch")
                artifact_valid = False
            if sha256_path(artifact_path) != artifact.get("bundle_sha256"):
                errors.append(f"{artifact_id}: bundle SHA-256 mismatch")
                artifact_valid = False
            if artifact_valid:
                try:
                    semantic_values.append(read_sanitized_evidence(artifact_path))
                except AcceptanceError as exc:
                    errors.append(f"{artifact_id}: cannot validate evidence: {exc}")
        if evidence and len(semantic_values) == len(evidence):
            try:
                validate_evidence_semantics(
                    definitions.get(gate_id, {"id": gate_id}),
                    semantic_values,
                    outcome=gate.get("outcome"),
                )
            except (AcceptanceError, KeyError, TypeError, ValueError) as exc:
                errors.append(f"{gate_id}: semantic evidence invalid: {exc}")
    if errors:
        raise AcceptanceError("acceptance gates are incomplete: " + ", ".join(errors))
    source = inspect_source(root=root, runner=runner)
    if source["commit"] != session.get("source", {}).get("commit"):
        raise AcceptanceError("source commit changed during acceptance")
    if contract_hash(contract_path) != session.get("source", {}).get("contract_sha256"):
        raise AcceptanceError("acceptance contract changed during the session")
    timestamp = now().isoformat()
    session.update(
        {
            "action_id": "clean-mac.finalize",
            "status": "accepted",
            "updated_at": timestamp,
            "finalized_at": timestamp,
            "final_source_readback": source,
            "publication_authorized": False,
        }
    )
    if write:
        atomic_write(path, session)
    return session


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    add_state_dir_argument(parser)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate tracked acceptance definitions")
    subparsers.add_parser("status", help="show tracked hardware-run status")
    template = subparsers.add_parser(
        "evidence-template",
        help="print the expected evidence shape for one gate",
    )
    template.add_argument("--gate", required=True)
    template.add_argument("--phase")

    initialize = subparsers.add_parser("init", help="initialize an eligible clean-Mac session")
    initialize.add_argument("--attest", required=True)
    initialize.add_argument("--session-dir", type=Path)
    initialize.add_argument("--apply", action="store_true")
    initialize.add_argument("--confirm", default="")

    record = subparsers.add_parser("record", help="record one acceptance gate")
    record.add_argument("session", type=Path)
    record.add_argument("--gate", required=True)
    record.add_argument("--outcome", choices=sorted(OUTCOMES), required=True)
    record.add_argument("--evidence", action="append", type=Path, default=[])
    record.add_argument("--note", default="")
    record.add_argument("--apply", action="store_true")
    record.add_argument("--confirm", default="")

    finalize = subparsers.add_parser("finalize", help="finalize a complete session")
    finalize.add_argument("session", type=Path)
    finalize.add_argument("--apply", action="store_true")
    finalize.add_argument("--confirm", default="")
    args = parser.parse_args()

    if args.command == "validate":
        result = validate_contract()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "passed" else 1
    if args.command == "status":
        print(json.dumps(load_json(STATUS_PATH), ensure_ascii=False, indent=2))
        return 0
    if args.command == "evidence-template":
        contract = load_json(CONTRACT_PATH)
        definitions = {gate["id"]: gate for gate in contract["gates"]}
        definition = definitions.get(args.gate)
        if not definition:
            parser.error(f"unknown acceptance gate: {args.gate}")
        phases = definition.get("required_phases", [])
        if args.phase and args.phase not in phases:
            parser.error(f"--phase must be one of: {', '.join(phases)}")
        if definition.get("evidence_kind") == "clean_mac_gate_evidence":
            result = evidence_template(definition, phase=args.phase)
        else:
            result = {
                "gate_id": definition["id"],
                "evidence_kind": definition["evidence_kind"],
                "capture_command": definition["command_hint"],
            }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.command in {"init", "record"}:
        if args.apply and args.confirm != SESSION_UPDATE_CONFIRMATION:
            parser.error(f'--apply requires --confirm "{SESSION_UPDATE_CONFIRMATION}"')
        action_id = "clean-mac.session-update"
    else:
        if args.apply and args.confirm != FINALIZE_CONFIRMATION:
            parser.error(f'--apply requires --confirm "{FINALIZE_CONFIRMATION}"')
        action_id = "clean-mac.finalize"

    if args.command == "init":
        state_dir = resolve_state_dir(args.state_dir)
        output = args.session_dir or (
            state_dir
            / (
                "clean-mac-acceptance-"
                + dt.datetime.now().strftime("%Y%m%d-%H%M%S")
                + "-"
                + uuid.uuid4().hex[:8]
            )
        )
        result = new_session(output, attestation=args.attest, write=args.apply)
        print(
            json.dumps(
                {
                    "session": str(output),
                    **result,
                    "record_status": "recorded" if args.apply else "planned",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.command == "record":
        result = record_gate(
            args.session,
            gate_id=args.gate,
            outcome=args.outcome,
            evidence_paths=args.evidence,
            note=args.note,
            write=args.apply,
        )
        print(
            json.dumps(
                {
                    **result,
                    "record_status": "recorded" if args.apply else "planned",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    result = finalize_session(args.session, write=args.apply)
    print(
        json.dumps(
            {
                **result,
                "record_status": "recorded" if args.apply else "planned",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except AcceptanceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
