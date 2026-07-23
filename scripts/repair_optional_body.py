#!/usr/bin/env python3
"""Report optional guides that still use legacy machine-state wording."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
old = "- Actual download and installed footprint remain `null` until installation is performed and measured."
findings = []
for path in ROOT.glob("components/*.md"):
    text = path.read_text(encoding="utf-8")
    if "tier: optional" in text and "status: \"installed\"" in text and old in text:
        findings.append(str(path.relative_to(ROOT)))
print(json.dumps({"tracked_files_written": False, "migration_required": findings}, indent=2))
raise SystemExit(1 if findings else 0)
