#!/usr/bin/env python3
"""Validate the current version's release-candidate acceptance contract."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX = ROOT / "references" / "release-acceptance-matrix.json"
ALLOWED_CLASSIFICATIONS = {
    "supported",
    "interface_limited",
    "deferred",
    "excluded",
}
CURRENT_RELEASE_STATUSES = {"release_candidate", "shipped"}
SEMVER = re.compile(r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)")


def validate_contract(
    root: Path = ROOT,
    matrix_path: Path | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    matrix_path = (matrix_path or root / "references/release-acceptance-matrix.json").resolve()
    errors: list[str] = []

    try:
        matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "failed", "errors": [f"cannot read acceptance matrix: {exc}"]}

    version_path = root / "VERSION"
    readme_path = root / "README.md"
    roadmap_path = root / "references" / "release-roadmap.md"
    version = version_path.read_text(encoding="utf-8").strip() if version_path.is_file() else None
    readme = readme_path.read_text(encoding="utf-8") if readme_path.is_file() else ""
    readme_versions = re.findall(r"Current target version:\s*\*\*(\d+\.\d+\.\d+)\*\*", readme)
    roadmap = roadmap_path.read_text(encoding="utf-8") if roadmap_path.is_file() else ""
    match = (
        re.search(
            rf"## {re.escape(version)}\b.*?^Status: \*\*([^*]+)\*\*",
            roadmap,
            flags=re.MULTILINE | re.DOTALL,
        )
        if isinstance(version, str) and SEMVER.fullmatch(version)
        else None
    )
    roadmap_status = match.group(1).strip() if match else None

    if matrix.get("schema_version") != 1:
        errors.append("matrix schema_version must be 1")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        errors.append(f"VERSION must be a three-part Semantic Version, got {version!r}")
    if matrix.get("version") != version:
        errors.append("matrix version must match VERSION")
    if not readme_versions:
        errors.append("README must declare at least one Current target version")
    elif any(readme_version != version for readme_version in readme_versions):
        errors.append("every README Current target version must match VERSION")
    if roadmap_status not in CURRENT_RELEASE_STATUSES:
        errors.append(f"current roadmap status must be release_candidate or shipped, got {roadmap_status!r}")
    if matrix.get("release_status") != roadmap_status:
        errors.append("matrix release_status must match the current VERSION roadmap status")

    definitions = matrix.get("classifications")
    if not isinstance(definitions, dict) or set(definitions) != ALLOWED_CLASSIFICATIONS:
        errors.append("matrix must define exactly the four accepted classifications")

    items = matrix.get("items")
    if not isinstance(items, list):
        errors.append("matrix items must be a list")
        items = []
    seen_ids: set[str] = set()
    seen_classes: set[str] = set()
    supported_count = 0
    for index, item in enumerate(items):
        prefix = f"item[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        item_id = item.get("id")
        classification = item.get("classification")
        capability = item.get("capability")
        if not isinstance(item_id, str) or not item_id:
            errors.append(f"{prefix} requires a non-empty id")
        elif item_id in seen_ids:
            errors.append(f"duplicate matrix id: {item_id}")
        else:
            seen_ids.add(item_id)
        if classification not in ALLOWED_CLASSIFICATIONS:
            errors.append(f"{prefix} has invalid classification: {classification!r}")
        else:
            seen_classes.add(classification)
        if not isinstance(capability, str) or not capability:
            errors.append(f"{prefix} requires a capability")
        evidence = item.get("evidence")
        if classification == "supported":
            supported_count += 1
            if not isinstance(evidence, list) or not evidence:
                errors.append(f"{item_id or prefix} supported capability requires evidence")
        if isinstance(evidence, list):
            for relative in evidence:
                if not isinstance(relative, str) or not relative:
                    errors.append(f"{item_id or prefix} contains invalid evidence path")
                    continue
                candidate = (root / relative).resolve()
                try:
                    candidate.relative_to(root)
                except ValueError:
                    errors.append(f"{item_id or prefix} evidence escapes repository: {relative}")
                    continue
                if not candidate.exists():
                    errors.append(f"{item_id or prefix} evidence not found: {relative}")

    missing_classes = sorted(ALLOWED_CLASSIFICATIONS - seen_classes)
    if missing_classes:
        errors.append("matrix has no items for: " + ", ".join(missing_classes))

    return {
        "status": "passed" if not errors else "failed",
        "version": version,
        "release_status": roadmap_status,
        "matrix_items": len(items),
        "supported_items": supported_count,
        "classifications": sorted(seen_classes),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--matrix", type=Path)
    args = parser.parse_args()
    result = validate_contract(args.root, args.matrix)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
