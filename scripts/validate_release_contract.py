#!/usr/bin/env python3
"""Validate the frozen 0.1.0 release-candidate acceptance contract."""

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
    roadmap_path = root / "references" / "release-roadmap.md"
    version = version_path.read_text(encoding="utf-8").strip() if version_path.is_file() else None
    roadmap = roadmap_path.read_text(encoding="utf-8") if roadmap_path.is_file() else ""
    match = re.search(
        r"## 0\.1\.0\b.*?^Status: \*\*([^*]+)\*\*",
        roadmap,
        flags=re.MULTILINE | re.DOTALL,
    )
    roadmap_status = match.group(1).strip() if match else None

    if matrix.get("schema_version") != 1:
        errors.append("matrix schema_version must be 1")
    if version != "0.1.0":
        errors.append(f"VERSION must remain 0.1.0, got {version!r}")
    if matrix.get("version") != version:
        errors.append("matrix version must match VERSION")
    if matrix.get("release_status") != "release_candidate":
        errors.append("matrix release_status must be release_candidate")
    if roadmap_status != "release_candidate":
        errors.append(
            f"0.1.0 roadmap status must be release_candidate, got {roadmap_status!r}"
        )

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
