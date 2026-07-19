#!/usr/bin/env python3
"""Read-only printer/scanner inventory.

Unlike fonts or Dock order, a printer list is not meaningfully "portable"
across machines -- it reflects whatever network/USB printer is physically
reachable from this Mac, often identified by a LAN IP address. Per this
skill's data classification (see SKILL.md), that is a machine-local
observation, not tracked policy: this script only writes a dated
state/printers-*.json record. It never adds, removes, or configures a
printer.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"


def _run(args: list[str]) -> str:
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    return (result.stdout or result.stderr).strip()


def scan() -> dict[str, object]:
    printers_raw = _run(["lpstat", "-p"])
    default_raw = _run(["lpstat", "-d"])
    printers = []
    for line in printers_raw.splitlines():
        if line.startswith("printer "):
            parts = line.split()
            printers.append({"name": parts[1], "raw_status": line})
    profiler = subprocess.run(
        ["system_profiler", "SPPrintersDataType", "-json"], capture_output=True, text=True, check=False,
    )
    scanning_support = {}
    if profiler.returncode == 0:
        try:
            data = json.loads(profiler.stdout)
            for entry in data.get("SPPrintersDataType", []):
                scanning_support[entry.get("_name")] = entry.get("scanning_support")
        except json.JSONDecodeError:
            pass
    return {
        "schema_version": 1,
        "captured_at": dt.datetime.now().astimezone().isoformat(),
        "printers": printers,
        "default_destination_raw": default_raw,
        "scanning_support_by_device": scanning_support,
        "note": "Machine-local observation only; not a tracked cross-machine policy.",
    }


def main() -> int:
    result = scan()
    STATE.mkdir(exist_ok=True)
    output = STATE / f"printers-{dt.datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"state_file": str(output), **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
