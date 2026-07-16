#!/usr/bin/env python3
"""Move stray optional-guide metadata inside YAML frontmatter."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
fixed = 0
for path in ROOT.glob("components/*.md"):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("installed_measurement_method:"):
        continue
    first = text.find("---\n")
    if first < 0:
        continue
    stray, rest = text[:first], text[first:]
    line = stray.strip()
    text = rest.replace("---\n", f"---\n{line}\n", 1)
    path.write_text(text, encoding="utf-8")
    fixed += 1
print(f"Repaired {fixed} optional frontmatter files")
