---
component_id: "go-ios"
name: "go-ios"
category: "Developer tools"
tier: "core"
lifecycle_status: "active"
source: "npm_global"
delivery_method: "npm-global"
npm_package: "go-ios"
npm_version: "1.3.2"
npm_runtime_manager: "fnm"
npm_runtime_version: "24"
official_url: "https://github.com/danielpaulus/go-ios"
check_command: "ios version"
install_after: ["node", "@deepseek-ai/dsh"]
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 100000000
download_estimate_method: "catalog_size_gb_planning_estimate"
cli_path: "/opt/homebrew/bin/ios"
---
# go-ios (iOS automation CLI)

Cross-platform iOS automation toolchain (Go). Core component because it is the
**richest iOS control surface** beyond libimobiledevice: JSON output everywhere,
app install/uninstall, XCTest, accessibility, WebDriverAgent, file containers,
and — via its Go module — the **SpringBoard home-screen layout reader**
(`getIconState`).

## Installation

```sh
npm install -g go-ios          # under fnm Node 24
npm install -g --allow-scripts=go-ios   # if postinstall (agent) was skipped
```

Verified: go-ios 1.3.2 (2026-08-21). Binary: `/opt/homebrew/bin/ios`.

## Core read commands (work without tunnel / Developer Image)

```sh
ios list                                 # enumerate devices
ios apps --udid=<UDID>                   # installed apps as JSON (display name, bundle id, icons)
ios devicename --udid=<UDID>             # device name
ios date --udid=<UDID>                   # device date/time
ios batterycheck --udid=<UDID>           # battery status
ios syslog --udid=<UDID>                 # stream device logs
ios file ls --udid=<UDID> --bundle-id=<bundleID>   # app container files
```

`ios apps` JSON is a good cross-check against `ideviceinstaller list --user`.

## iOS 17+ gated features (tunnel + Developer Image)

```sh
ios tunnel start --userspace             # userspace tunnel (no sudo) for iOS 17+
ios image auto                           # attempt to install Developer Disk Image automatically
ios screenshot --udid=<UDID> --output=out.png   # capture screenshot
ios debug --udid=<UDID> <bundleID>       # LLDB debug session
```

On iOS 27 the screenshot/instruments services report
`InvalidService … Have you mounted the Developer Image?` — same limitation as
`idevicescreenshot`: Apple stopped shipping DeveloperDiskImage with Xcode 15
(see `components/libimobiledevice.md`). Read ops above remain available.

## SpringBoard home-screen layout (know-how, verified 2026-08)

The Go module `ios/springboard` connects to `com.apple.springboardservices`
and issues `getIconState`:

```go
client, _ := springboard.NewClient(device)
screens, _ := client.ListIcons()   // per-page []Icon + dock (index 0)
```

- Returns per page: `AppIcon` (bundle id + version), `Folder` (nested pages),
  `WebClip` (Safari bookmark / PWA), `Custom` (widget placeholder — the API
  reports only `iconType: custom`, **no widget kind/size**).
- **Read = fully supported** → ideal for exporting the home screen to
  Markdown/JSON for versioning.
- **Write = not in go-ios** (no `setIconState` in the client). The underlying
  protocol has `setIconState` and `pymobiledevice3` implements it, but
  [pymobiledevice3#993](https://github.com/doronz88/pymobiledevice3/issues/993)
  reports it is rejected on some iOS versions — treat layout writes as
  unreliable.

Practical use for macomrade: dump `getIconState` → Markdown table per page
(apps + folders + dock), store under `references/` as desired-state home-screen
layout; note widgets manually (screenshot-based) since the API omits them.

**Ready-made exporter:** `scripts/ios-layout-export/` builds a small Go CLI
(`go build` then `./ios-layout --udid=… --output=…`) that runs this exact flow
and writes a Markdown layout. Verified on iOS 27: 10 screens, dock folders,
widget bundle IDs (e.g. `com.google.gemini.WidgetKitExtension`) resolved.

**Prefer the pymobiledevice3 exporter instead**
(`scripts/ios-layout-export-pymd3.py`): it reads the same `getIconState` but
additionally resolves widget **kind** (`widgetIdentifier`) and **size**
(`gridSize`) — go-ios marks widgets only as `custom`. Archives live in
`Private/device-layouts/` (gitignored, iCloud-synced), never under
`references/`. Widget *configuration* (e.g. which city a weather widget shows)
is not in the payload — screenshot alongside when needed.

## Troubleshooting

- `go-ios agent is not running … ios tunnel start` → warning only; most read
  commands still work. Start `ios tunnel start --userspace` for gated ones.
- `InvalidService … Developer Image` → mount/install the developer image
  (`ios image auto`) or accept the Xcode-15+ limitation.
- Device locked → unlock the iPhone (same lockdown rule as libimobiledevice).

## Cleanup

```sh
npm uninstall -g go-ios   # only after explicit confirmation
```
