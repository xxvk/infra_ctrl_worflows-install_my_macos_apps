# iOS home-screen layout export

Export the iPhone home-screen layout (icons, folders, dock, widgets) to
Markdown, archived under `Private/device-layouts/` (gitignored, iCloud-synced —
**never** under `references/`, which is public Git).

## Two exporters (prefer pymobiledevice3)

| Tool | Data quality | Notes |
|---|---|---|
| `ios-layout-export-pymd3.py` | **Full** — widget kind (`widgetIdentifier`) + size (`gridSize`), folder contents, app bundle ids | **Preferred.** Needs `pymobiledevice3` (venv) |
| `ios-layout-export/` (Go, go-ios) | Partial — widgets only as `custom`, folders as count summary | Fallback; `brew install go` + `go build` |

pymobiledevice3 wins because SpringBoard's `getIconState` exposes
`widgetIdentifier` and `gridSize` for widgets — the Go client does not.

## Requirements

- iPhone connected over USB, **unlocked**, Developer Mode enabled
  (see `components/libimobiledevice.md`, `components/go-ios.md`)
- Python exporter: `pymobiledevice3` CLI reachable (venv)

## Run (Python, preferred)

```sh
python3 scripts/ios-layout-export-pymd3.py \
  --udid <UDID> \
  --pymd3 <venv>/bin/pymobiledevice3 \
  --output Private/device-layouts/iphone-<name>-home-layout.md
```

## Run (Go fallback)

```sh
cd scripts/ios-layout-export && go build -o ios-layout .
./ios-layout --udid=<UDID> --output=Private/device-layouts/iphone-<name>-home-layout.md
```

## Output

- Screen 0 = dock (folders incl. per-folder icon/pages)
- Widgets show `Widget(小/中/大)` + `widgetIdentifier` (e.g.
  `com.google.gemini.WidgetKitExtension`)
- Apps show bundle id; folders expand their contents

## Screenshot archive (visual reference) — user screenshots

Widget **configuration** (e.g. which city a weather widget shows) and the
final look are not in the SpringBoard payload. **Rule (2026-08-22): the user
captures native iPhone screenshots** (full resolution, in page order, named
by sequence) and uploads them; the agent only archives them under
`Private/device-layouts/screenshots/` as `iphone-<name>-screen-NN-widgets.png`
and updates the layout Markdown index.

All automated screenshot paths are broken on iOS 17+ (`idevicescreenshot`,
`ios screenshot`, `pymobiledevice3 developer screenshot` — Apple stopped
shipping the DeveloperDiskImage). iPhone Mirroring window captures
(`screencapture -R<x,y,w,h>`) work but are lower resolution and may mismatch
page order — fallback only.

## Verified

2026-08-21: PM15 (iPhone 15 Pro Max, iOS 27.0) → 10 screens, dock folders,
7 widget screens with kind+size resolved, 2 app screens.

## Known limits

- Read-only (SpringBoard `setIconState` unreliable; see go-ios guide).
- Widget config details not exposed by protocol — screenshot required.
