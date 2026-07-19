#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 -m json.tool references/app-catalog.json >/dev/null
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/install-macos-apps-pycache" \
python3 -m py_compile scripts/bootstrap_macos.py scripts/bootstrap_validate.py scripts/bootstrap_verify.py scripts/capacities_migration_inventory.py scripts/capacities_cleanup.py scripts/macos_apps.py scripts/macos_permissions.py scripts/macos_permissions_cleanup.py scripts/macos_preferences.py scripts/docker_desktop_cleanup.py scripts/claude_vm_cleanup.py
python3 -m json.tool settings/system-preferences-values.json >/dev/null

python3 scripts/macos_apps.py scan
python3 scripts/macos_apps.py plan --profile auto
python3 scripts/docker_desktop_cleanup.py inspect
python3 scripts/claude_vm_cleanup.py inspect

python3 - <<'PY'
import json
from pathlib import Path

scan = json.loads(sorted(Path("state").glob("scan-*.json"))[-1].read_text())
plan = json.loads(sorted(Path("state").glob("plan-*.json"))[-1].read_text())
assert all("source" in app for app in scan["applications"]), "scan lacks source evidence"
assert "source_mismatches" in plan, "plan lacks source mismatch report"
PY

PLAN="$(ls -t state/plan-*.json | head -n 1)"
APP="$(python3 - "$PLAN" <<'PY'
import json
import sys

for app in json.load(open(sys.argv[1]))["missing"]:
    if app.get("brew_cask") or app.get("brew_formula"):
        print(app["name"])
        break
PY
)"

if [[ -n "$APP" ]]; then
  python3 scripts/macos_apps.py install "$PLAN" --only "$APP"
else
  echo "No missing Homebrew package in this plan; install dry-run skipped."
fi

echo "Smoke test passed. No --apply or Docker removal command was run."
