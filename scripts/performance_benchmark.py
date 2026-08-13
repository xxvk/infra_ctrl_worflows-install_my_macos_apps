#!/usr/bin/env python3
"""Measure repeatable local command cost without changing Mac configuration."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import resource
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

from schema_contract import SchemaContractError, load_and_validate
from state_paths import add_state_dir_argument, resolve_state_dir


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "settings" / "performance-budgets.json"
REQUIRED_OPERATIONS = ("inventory", "plan", "validate", "drift", "migration")


class BenchmarkError(RuntimeError):
    """Raised when a benchmark cannot meet its bounded contract."""


def load_policy(path: Path = POLICY_PATH) -> dict[str, Any]:
    try:
        return load_and_validate(path, "performance-budget")
    except SchemaContractError as exc:
        raise BenchmarkError(str(exc)) from exc


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("kind") != "macomrade_performance_budget":
        raise BenchmarkError("performance budget kind is invalid")
    if set(policy.get("operations", {})) != set(REQUIRED_OPERATIONS):
        raise BenchmarkError("performance budget must cover inventory, plan, validate, drift, and migration")
    for name, budget in policy["operations"].items():
        if budget["warm_max_ms"] > budget["cold_max_ms"]:
            raise BenchmarkError(f"{name}: warm budget may not exceed cold budget")
    if policy["regression"]["max_percent"] > 100:
        raise BenchmarkError("regression max_percent must be at most 100")


def validate() -> dict[str, Any]:
    try:
        policy = load_policy()
        validate_policy(policy)
    except BenchmarkError as exc:
        return {"schema_version": 1, "status": "failed", "errors": [str(exc)]}
    return {"schema_version": 1, "status": "passed", "operations": sorted(policy["operations"]), "errors": []}


def directory_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for parent, directories, files in os.walk(path, followlinks=False):
        directories[:] = [name for name in directories if not (Path(parent) / name).is_symlink()]
        for name in files:
            try:
                total += (Path(parent) / name).stat(follow_symlinks=False).st_blocks * 512
            except OSError:
                continue
    return total


def command_for(operation: str, state_dir: Path) -> list[str]:
    py = sys.executable
    commands = {
        "inventory": [py, "scripts/macos_apps.py", "--state-dir", str(state_dir), "scan"],
        "plan": [py, "scripts/macos_apps.py", "--state-dir", str(state_dir), "plan", "--profile", "auto"],
        "validate": [py, "scripts/release_check.py"],
        "drift": [py, "scripts/bootstrap_verify.py", "--state-dir", str(state_dir)],
        "migration": [py, "scripts/migrate_state.py", "inspect"],
    }
    if operation not in commands:
        raise BenchmarkError(f"unknown benchmark operation: {operation}")
    return commands[operation]


def _peak_rss_bytes(_completed: subprocess.CompletedProcess[str]) -> int | None:
    """Read the standard-library child-process high-water mark without sysctl."""
    value = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss
    # Darwin reports ru_maxrss in bytes; Linux reports KiB. This runner targets
    # macOS but keeps its value portable for deterministic fixture tests.
    return int(value) if sys.platform == "darwin" else int(value) * 1024 if value else None


def _summary(samples: list[dict[str, Any]]) -> dict[str, int | None]:
    warm = samples[1:] or samples
    rss_values = [item["peak_rss_bytes"] for item in samples if isinstance(item["peak_rss_bytes"], int)]
    return {
        "cold_elapsed_ms": samples[0]["elapsed_ms"],
        "warm_elapsed_ms": max(item["elapsed_ms"] for item in warm),
        "peak_rss_bytes": max(rss_values) if rss_values else None,
        "output_bytes": max(item["output_bytes"] for item in samples),
        "state_growth_bytes": sum(item["state_growth_bytes"] for item in samples),
    }


def run_suite(
    operations: list[str],
    *,
    iterations: int,
    state_dir: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    clock: Callable[[], float] = time.monotonic,
    peak_reader: Callable[[subprocess.CompletedProcess[str]], int | None] = _peak_rss_bytes,
) -> dict[str, Any]:
    if iterations < 2:
        raise BenchmarkError("iterations must be at least 2 for cold/warm measurement")
    rows = {}
    for operation in operations:
        samples = []
        for index in range(iterations):
            before = directory_bytes(state_dir)
            started = clock()
            completed = runner(command_for(operation, state_dir), cwd=ROOT, capture_output=True, text=True, check=False)
            elapsed = int(round((clock() - started) * 1000))
            after = directory_bytes(state_dir)
            samples.append({
                "mode": "cold" if index == 0 else "warm",
                "returncode": completed.returncode,
                "elapsed_ms": elapsed,
                "peak_rss_bytes": peak_reader(completed),
                "output_bytes": len(completed.stdout.encode("utf-8")) + len(completed.stderr.encode("utf-8")),
                "state_growth_bytes": max(0, after - before),
            })
        rows[operation] = {"samples": samples, "summary": _summary(samples)}
    return {"schema_version": 1, "kind": "performance_benchmark", "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(), "iterations": iterations, "operations": rows}


def compare_budgets(current: dict[str, Any], policy: dict[str, Any], baseline: dict[str, Any] | None) -> dict[str, Any]:
    violations = []
    metric_map = {"cold_elapsed_ms": "cold_max_ms", "warm_elapsed_ms": "warm_max_ms", "peak_rss_bytes": "peak_rss_max_bytes", "output_bytes": "output_max_bytes", "state_growth_bytes": "state_growth_max_bytes"}
    for operation, values in current["operations"].items():
        summary = values["summary"]
        allowed_returncodes = {0, 1} if operation == "drift" else {0}
        if any(sample.get("returncode") not in allowed_returncodes for sample in values.get("samples", [])):
            violations.append({"operation": operation, "metric": "returncode", "reason": "command_failed"})
        for metric, budget_key in metric_map.items():
            value = summary.get(metric)
            if isinstance(value, int) and value > policy["operations"][operation][budget_key]:
                violations.append({"operation": operation, "metric": metric, "reason": "absolute_budget", "observed": value, "budget": policy["operations"][operation][budget_key]})
        if baseline and operation in baseline.get("operations", {}):
            previous = baseline["operations"][operation].get("summary", {})
            for metric in ("cold_elapsed_ms", "warm_elapsed_ms"):
                old, new = previous.get(metric), summary.get(metric)
                delta = int(new or 0) - int(old or 0)
                if isinstance(old, int) and old > 0 and delta >= policy["regression"]["min_absolute_delta_ms"] and (delta * 100 / old) > policy["regression"]["max_percent"]:
                    violations.append({"operation": operation, "metric": metric, "reason": "regression_budget", "observed": new, "baseline": old})
    return {"status": "review_required" if violations else "passed", "baseline_present": baseline is not None, "violations": violations}


def _load_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def _write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate", help="validate benchmark coverage and budgets")
    run_parser = subparsers.add_parser("run", help="run bounded cold/warm measurements")
    run_parser.add_argument("--operation", action="append", choices=REQUIRED_OPERATIONS)
    run_parser.add_argument("--iterations", type=int, default=2)
    run_parser.add_argument("--set-baseline", action="store_true", help="replace only this machine's benchmark baseline")
    add_state_dir_argument(run_parser)
    args = parser.parse_args()
    if args.command == "validate":
        result = validate()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "passed" else 1
    try:
        policy = load_policy()
        validate_policy(policy)
        state_dir = resolve_state_dir(args.state_dir) / "benchmarks"
        baseline_path = state_dir / "benchmark-baseline.json"
        baseline = _load_json(baseline_path)
        result = run_suite(args.operation or list(REQUIRED_OPERATIONS), iterations=args.iterations, state_dir=state_dir)
        result["comparison"] = compare_budgets(result, policy, baseline)
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        output = state_dir / f"benchmark-{stamp}.json"
        _write_json(output, result)
        if args.set_baseline:
            _write_json(baseline_path, result)
        print(json.dumps({"record": str(output), "baseline_written": args.set_baseline, "comparison": result["comparison"]}, ensure_ascii=False, indent=2))
        return 0
    except BenchmarkError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
