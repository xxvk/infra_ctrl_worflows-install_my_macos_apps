#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 -m json.tool references/app-catalog.json >/dev/null
python3 scripts/validate_app_catalog.py >/dev/null
# Compile-check every tracked script, not a hand-maintained subset --
# a script added later is covered automatically instead of silently skipped.
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/install-macos-apps-pycache" \
python3 -m py_compile scripts/*.py
python3 -m json.tool settings/system-preferences-values.json >/dev/null

# Every LaunchAgent plist template must be well-formed XML before it is ever
# rendered and installed -- this is exactly the class of bug (a stray
# backslash, an unescaped &) that has twice slipped through manual review.
for template in templates/*.launchagent.plist; do
  plutil -lint "$template" >/dev/null
done
# The K240 template has no placeholder substitution to verify beyond the
# raw file. The drift-check template substitutes a shell command that must
# still be valid XML after rendering -- lint the actual rendered output too.
python3 -c "
import sys
sys.path.insert(0, 'scripts')
from drift_check_schedule import render_plist
open('/tmp/install-macos-apps-drift-check-rendered.plist', 'w').write(render_plist())
"
plutil -lint /tmp/install-macos-apps-drift-check-rendered.plist >/dev/null

python3 scripts/macos_apps.py scan
python3 scripts/macos_apps.py plan --profile auto
python3 scripts/docker_desktop_cleanup.py inspect
python3 scripts/claude_vm_cleanup.py inspect
python3 scripts/macos_startup_items.py scan >/dev/null
python3 scripts/macos_dock.py >/dev/null

# Read-only / dry-run paths for the CTO gap-audit backlog scripts. None of
# these accept --apply here, so nothing is written outside /dev/null or
# left loaded as a LaunchAgent.
python3 scripts/backup_precondition_check.py >/dev/null
python3 scripts/dotfiles_sync.py status >/dev/null
python3 scripts/dotfiles_sync.py link >/dev/null   # dry-run: no --apply
python3 scripts/drift_check_schedule.py status >/dev/null
python3 scripts/drift_check_schedule.py install >/dev/null   # dry-run: no --apply
python3 scripts/drift_check_schedule.py uninstall >/dev/null # dry-run: no --apply
python3 scripts/skill_footprint_inventory.py >/dev/null
python3 scripts/skill_uninstall.py >/dev/null                # dry-run: no --apply
python3 scripts/macos_fonts.py >/dev/null
python3 scripts/macos_printers.py >/dev/null

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
