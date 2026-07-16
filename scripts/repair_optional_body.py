#!/usr/bin/env python3
"""Correct generated size wording after local measurements are added."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
old = "- Actual download and installed footprint remain `null` until installation is performed and measured."
new = "- Installed footprint above is measured locally; download bytes remain `null` unless a package transfer log is available."
changed = 0
for path in ROOT.glob("components/*.md"):
    text = path.read_text(encoding="utf-8")
    if "tier: optional" in text and "status: \"installed\"" in text and old in text:
        path.write_text(text.replace(old, new), encoding="utf-8")
        changed += 1
print(f"Repaired {changed} optional guide size notes")
