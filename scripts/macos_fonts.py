#!/usr/bin/env python3
"""Read-only scan/check for the tracked font list in settings/fonts.yaml.

Keep FONTS below in sync with settings/fonts.yaml -- this repo has no YAML
parser dependency, so the tracked list is declared here in both places
deliberately, the same way ALLOWLIST constants are hardcoded in
macos_preferences.py rather than YAML-driven. This script never installs a
font; it only reports presence/absence and the documented install source.
"""

from __future__ import annotations

import json
from pathlib import Path

HOME = Path.home()
FONT_DIRECTORIES = [
    HOME / "Library/Fonts",
    Path("/Library/Fonts"),
    Path("/System/Library/Fonts"),
    Path("/System/Library/Fonts/Supplemental"),
]

# Mirror of settings/fonts.yaml's `fonts` list.
FONTS = [
    {
        "name": "JetBrains Mono",
        "required_by": "Ghostty",
        "brew_cask": "font-jetbrains-mono",
        "official_url": "https://www.jetbrains.com/lp/mono/",
    },
]


def _matches(directory: Path, needle: str) -> list[str]:
    if not directory.is_dir():
        return []
    normalized = needle.lower().replace(" ", "")
    hits = []
    for path in directory.iterdir():
        if normalized in path.name.lower().replace(" ", "").replace("-", ""):
            hits.append(str(path))
    return hits


def scan() -> dict[str, object]:
    results = []
    for font in FONTS:
        found_paths = []
        for directory in FONT_DIRECTORIES:
            found_paths.extend(_matches(directory, font["name"]))
        results.append({
            **font,
            "installed": bool(found_paths),
            "found_paths": found_paths,
        })
    return {"status": "verified", "fonts": results}


def main() -> int:
    print(json.dumps(scan(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
