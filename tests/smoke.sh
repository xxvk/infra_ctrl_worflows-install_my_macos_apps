#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

python3 -m json.tool references/app-catalog.json >/dev/null
PYTHONPYCACHEPREFIX="${TMPDIR:-/tmp}/install-macos-apps-pycache" \
  python3 -m py_compile scripts/macos_apps.py scripts/docker_desktop_cleanup.py

python3 scripts/macos_apps.py scan
python3 scripts/macos_apps.py plan --profile auto
python3 scripts/docker_desktop_cleanup.py inspect

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
