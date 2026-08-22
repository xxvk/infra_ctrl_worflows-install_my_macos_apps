# iOS application workflow

Lifecycle rules for iPhone/iPad applications, parallel to the macOS
application workflow. The iOS catalog is `references/ios-app-catalog.json`
(schema `ios-app-catalog-v1`); this reference covers inventory and install.

## Purchase-history entry point (know-how, verified 2026-08)

Apple's web purchase-history list is **`https://reportaproblem.apple.com`**
(log in with the Apple account). `apps.apple.com/us/iphone/apps` is only a
store browse page — it does **not** show the purchased list. The page lists
orders (date, order ID, total, app name, developer, price). It includes
subscriptions (e.g. iCloud+) and in-app purchases, which are not standalone
apps; filter those out. It does **not** tell you what is currently installed
on the device — combine it with device enumeration for installed state.

## Device enumeration via libimobiledevice (know-how, verified 2026-08-21)

**iPhone Mirroring is a pure video stream** (AVFoundation) with no
accessibility/meta bridge — the macOS AX tree exposes only one canvas group,
so UI-tree string extraction is impossible; only OCR works, which is too
fragile for full inventories. Use **libimobiledevice** instead (official
MobileInstallation API over usbmuxd):

```sh
brew install libimobiledevice ideviceinstaller
idevice_id -l                  # USB-attached devices (UDID)
idevice_id -n                  # network (Wi-Fi sync) devices
idevicepair validate           # pairing status
ideviceinstaller -u <UDID> list --user    # all user apps: bundle id, version, display name
ideviceinstaller -n -u <UDID> list --user # same over Wi-Fi
```

- First use requires **USB attach + "Trust this computer"** on the iPhone
  (user handoff; pairing is stored by usbmuxd, `~/.lockdown/` may not exist).
- **Wi-Fi sync**: the toggle lives in **macOS Finder, not iPhone Settings**
  (iOS 15+ removed the in-device path): USB-connect → Finder → sidebar device
  → *General* tab → check **"Show this iPhone when on Wi-Fi"** → Apply. After
  that, `idevice_id -n` and `-n` flags work without USB.
- Uninstall is supported (`ideviceinstaller uninstall <bundle_id>`) but is a
  destructive, irreversible operation — requires explicit user confirmation
  per macomrade contract. System apps cannot be uninstalled.
- Keep the raw device list machine-local (`Private/ios-device-reconciliation-*.json`).

## Reconciliation (know-how, verified 2026-08-21)

Comparing the device list against `ios-app-catalog.json` reveals both missing
installs and **wrong bundle IDs**. Real-world fixes from device data:

| Catalog name | Wrong bundle id | Device-correct id |
|---|---|---|
| Tailscale | `io.tailscale.ipn.macos` | `io.tailscale.ipn.ios` |
| iAEON | `com.aeonmy.myaeon` | `jp.co.aeonst.app.myaeon` |
| PayPay | `com.smart.paypay` | `jp.pay2.app.ios` |
| TRAE | `com.stone.solo.cn` | `com.stone.solo.i18n` |
| Mercari | `com.mercariapp.ios.mercari` | `com.kouzoh.ios.mercari` |
| Microsoft Copilot | `com.microsoft.officemobile` | `com.microsoft.copilot` |
| 三菱UFJ銀行 | `jp.mufg.bk.openaccount.app` | `jp.mufg.bk.applisp.01` |

Always re-check bundle IDs against device data before trusting purchase-history
extraction; iOS system apps (Apple Music `com.apple.Music`, Apple TV
`com.apple.tv`, Google Photos, Google Translate) may not appear in
`list --user` even when present.

## Home-screen layout export (know-how, verified 2026-08-21)

The SpringBoard `getIconState` payload gives the full layout: dock folders,
per-screen icons, and widgets. **pymobiledevice3 resolves widget kind and size;
go-ios does not** (widgets degrade to `custom`). Exporter:
`scripts/ios-layout-export-pymd3.py` (preferred) or the Go fallback under
`scripts/ios-layout-export/`.

Key facts learned:

- **Archives go to `Private/device-layouts/`** (gitignored, iCloud-synced) —
  never `references/`, which is public Git. Home-screen layout is observed
  device state, like `ios-device-reconciliation-*.json`.
- Widget payload: `widgetIdentifier` (kind, e.g. `GrokComposeWidget`),
  `gridSize` (small/medium/large), `containerBundleIdentifier` (host app).
  Widget **configuration** (e.g. which city a weather widget shows) is NOT
  exposed by SpringBoard — only screenshots capture it.
- Folders arrive as `iconLists` (per-page arrays of apps) — fully expandable
  into Markdown; the exporter renders them inside `<details>` blocks.
- `pymobiledevice3 springboard` subcommands ignore `--udid` (single device);
  top-level commands (`lockdown info`) take `--udid` after the command.
- Deleting icons changes screen count immediately (observed 10 → 8 screens);
  re-run the exporter to refresh the archive.

### Screenshot archive (visual reference) — user screenshots are the rule

**Rule (decided 2026-08-22): iOS screenshots are taken manually by the user
and handed over; the agent only archives them.** The user captures native
iPhone screenshots (460×878, full resolution) in page order, names them by
sequence (e.g. `02.png`, `03.png` …), and uploads them. The agent:

1. Places them under `Private/device-layouts/screenshots/` as
   `iphone-<name>-screen-NN-widgets.png`, keeping the user's sequence.
2. Updates the screenshot index in the layout Markdown (provenance note:
   user-captured native screenshots; content description inferred from layout
   data — user confirms correctness).
3. Treats widget configuration and final look as screenshot-only; the
   Markdown carries machine-readable data (bundle IDs, widget kinds, folder
   contents).

Why: every automated path is broken on iOS 17+ — `idevicescreenshot`
(libimobiledevice), `ios screenshot` (go-ios) and
`pymobiledevice3 developer screenshot` all fail (Apple stopped shipping the
DeveloperDiskImage with Xcode 15; the deprecated API is removed on iOS 27).
iPhone Mirroring window captures work but are lower resolution (348×766) and
can mismatch page order — user native screenshots are the reliable source.

Fallback if the user cannot screenshot: iPhone Mirroring (lock the iPhone →
auto-reconnects → `screencapture -R<x,y,w,h>` per page, swipe via CGEvent
drag). Mark such captures as mirror-derived.

Vision OCR cannot reliably read small dock folder labels; the screenshots are
archived for visual reference, while the Markdown carries the machine-readable
data (bundle IDs, widget kinds, folder contents).

## Inventory (statistics)

- Enumerate the installed iPhone inventory read-only via libimobiledevice
  (above) — the MobileInstallation API is authoritative. iPhone Mirroring
  remains a visual fallback only (OCR-based, no meta data).
- Record per-app metadata: display name, bundle identifier, App Store ID,
  version. Keep raw device dumps and reconciliation reports machine-local.
- The iOS catalog is desired state; a device list entry is not proof that an
  installation is complete or that the account is authorized.

## Install (App Store)

- Open the canonical `macappstore://itunes.apple.com/app/id<app_store_id>`
  URL and continue serially (same rule as macOS App Store workflow). Opening
  a page is not installation evidence.
- Never automate Apple ID login, purchases, or security confirmations. These
  are visible user handoffs.
- Only the user's approved Apple Account may be used; verify the visible
  account before any install.

## Catalog contract

Each `ios-app-catalog.json` entry requires:

- `name`, `category`, `tier` (core/optional/retired)
- `ios_bundle_id` (e.g. `com.tencent.xin`)
- `app_store_id` and optional `app_store_url`
- `guide` (component path, e.g. `components/ios-guides/<app>.md`)
- Optional: region availability, minimum iOS version, size, account scope,
  sync note, follow-up steps

Source enum: `app_store`, `testflight`, `enterprise`, `manual_or_unknown`.

## Verification

- After install, verify by launching the app on the iPhone and checking the
  visible version/account, or by a user-confirmed App Store receipt read.
- Record unavailable interfaces as unavailable, never as success.

## Cross-platform sync to Android (know-how, verified 2026-08-22)

When the iOS catalog grows new core entries, reconcile them with the Android
catalog and the Pixel:

- `references/cross-platform-app-map.json` maps `ios_bundle_id` →
  `play_store_package`. iOS-only apps (Apple system apps such as
  TestFlight/Pages/Numbers/Keynote/iMovie, or no-Android products) have no
  entry and are skipped.
- Verify candidate Play packages with `apkeep -l` (Play API), not HTTP 200
  checks (Cloudflare blocking gives false 404s). The user's manual installs
  on the Pixel are authoritative for real package names — reconcile those
  into the catalog (`adb shell pm list packages | grep <fragment>`).
- Sync result: new Android core entries + guides + README rows + map entries;
  then install on the Pixel or mark `not_installed` if region-locked.

## Safety rules

- Never copy raw device data, TCC databases, or private account sessions into
  tracked configuration.
- Never automate purchases, Apple ID credentials, or security confirmations.
- Home Screen organization is 0.9.0 scope and is not implied by installation.
