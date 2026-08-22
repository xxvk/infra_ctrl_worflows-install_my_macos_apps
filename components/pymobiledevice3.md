---
component_id: "pymobiledevice3"
name: "pymobiledevice3"
category: "Developer tools"
tier: "core"
lifecycle_status: "active"
source: "python_core"
delivery_method: "uv-shared-core"
official_url: "https://github.com/doronz88/pymobiledevice3"
check_command: "test -x \"$HOME/.local/share/python/core/.venv/bin/pymobiledevice3\""
install_after: ["libimobiledevice", "go-ios"]
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 50000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# pymobiledevice3 (iOS automation, Python)

Cross-platform iOS automation library + CLI (Python). Core component because
its SpringBoard service exposes **more layout detail than go-ios**:
widget **kind** (`widgetIdentifier`) and **size** (`gridSize`) are resolved,
which go-ios marks only as `custom`.

## Installation in the shared Python Core

```sh
cd references/python-core
UV_PROJECT_ENVIRONMENT="$HOME/.local/share/python/core/.venv" \\
  uv sync --locked --all-groups
```

The package is part of the shared Python Core manifest and lockfile. Do not
create a second venv or install it with system pip. The shared environment also
pulls in `developer_disk_image`, used for iOS 17+ Developer Image handling.
Verify with:

```sh
"$HOME/.local/share/python/core/.venv/bin/pymobiledevice3" --help
```

## Home-screen layout export (preferred path)

```sh
python3 scripts/ios-layout-export-pymd3.py \
  --udid <UDID> --pymd3 "$HOME/.local/share/python/core/.venv/bin/pymobiledevice3" \
  --output Private/device-layouts/iphone-<name>-home-layout.md
```

Output: per-screen Markdown with dock folders (contents expanded), app bundle
ids, and widgets as `Widget(小/中/大)` + `widgetIdentifier` (e.g.
`com.apple.CalendarWidget.CalendarUpNextWidget`, `GrokComposeWidget`).

## Other useful commands

```sh
pymobiledevice3 springboard state get              # full icon layout JSON
pymobiledevice3 springboard homescreen-icon-metrics  # grid size, dock max, folder dims
pymobiledevice3 springboard icon <bundle> <out.png>  # export an app icon PNG
pymobiledevice3 springboard wallpaper-home-screen <out.png>  # home wallpaper
pymobiledevice3 lockdown info --udid <UDID>          # device info
```

## Know-how (verified 2026-08, iOS 27)

- Widget payload: `gridSize` ∈ small/medium/large; `widgetIdentifier` names
  the specific widget kind; `containerBundleIdentifier` = hosting app.
- Widget **configuration** (e.g. which city a weather widget displays) is not
  exposed by SpringBoard — screenshots are the only archive for that.
- `springboard` subcommands ignore `--udid` (auto-select single device);
  top-level commands like `lockdown info` take `--udid` after the command.
- Folders arrive as `iconLists` (per-page app arrays) — fully expandable;
  `scripts/ios-layout-export-pymd3.py` renders them into Markdown `<details>`.
- `developer screenshot` is **removed on iOS 27** (deprecated API). No CLI
  screenshot path works on iOS 17+; use iPhone Mirroring
  (`screencapture -R<x,y,w,h>` per page) for visual archives. Wallpaper export
  (`wallpaper-home-screen`) also failed with a dropped connection — treat it
  as unreliable.
- Archives: `Private/device-layouts/` (gitignored, iCloud-synced) — layout is
  observed device state, not public desired-state config.

## Cleanup

```sh
The package is removed or changed through the shared Core manifest and
lockfile; do not delete the shared `.venv` just to retire this component.
```
