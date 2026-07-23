#!/usr/bin/env python3
"""Report legacy stray machine metadata; never move it into tracked YAML."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
findings = []
for path in ROOT.glob("components/*.md"):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("installed_measurement_method:"):
        continue
    findings.append(str(path.relative_to(ROOT)))
print(json.dumps({"tracked_files_written": False, "migration_required": findings}, indent=2))
raise SystemExit(1 if findings else 0)
