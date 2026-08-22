---
component_id: "libimobiledevice"
name: "libimobiledevice"
category: "Developer tools"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-formula"
brew_cask: null
brew_formula: "libimobiledevice"
official_url: "https://www.libimobiledevice.org/"
check_command: "idevice_id -l"
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 50000000
download_estimate_method: "catalog_size_gb_planning_estimate"
cli_path: "/opt/homebrew/bin/idevice_id"
---
# libimobiledevice (iOS device tools)

Open-source library and CLI suite to communicate with iOS devices natively
over USB — without iTunes. Core component because it is the **authoritative
source for the installed-app list** (bundle IDs, display names, versions) used
by the iOS reconciliation workflow. It reads the system MobileInstallation
service, never private device databases or backups.

## Installation

```sh
brew install libimobiledevice
brew install ideviceinstaller      # companion: app list / install management
```

Verified: libimobiledevice 1.4.0 + ideviceinstaller 1.2.0 (2026-08-21).

## Pairing (first use)

1. Connect the iPhone over USB and unlock it.
2. Pair:
   ```sh
   idevicepair pair
   ```
   Accept the **Trust This Computer** dialog on the iPhone (this is the only
   interactive step; do not bypass it).
3. Confirm:
   ```sh
   idevice_id -l          # device UDID
   idevicepair validate   # SUCCESS / Valid pairing
   ```

## Command reference (all 21 tools)

Installed binaries under `/opt/homebrew/bin` (libimobiledevice 1.4.0 +
ideviceinstaller 1.2.0). Grouped by purpose:

### Device info & identification
| Command | Function |
|---|---|
| `idevice_id -l` | List connected device UDIDs; with a UDID, print the device name |
| `ideviceinfo` | Read all device properties (model, OS version, serial, disk usage, …) |
| `idevicename` | Get / set the device name |
| `idevicedate` | Show the device's current date/time |

### Pairing & security
| Command | Function |
|---|---|
| `idevicepair` | Pair / validate / unpair (the "Trust This Computer" flow) |
| `ideviceprovision` | Install / manage provisioning profiles (developer certificates) |

### App management (core for this component)
| Command | Function |
|---|---|
| `ideviceinstaller` | **List installed apps (bundle ID + version + display name) / install / uninstall** — used by the iOS reconciliation workflow |
| `idevicedevmodectl` | Manage Developer Mode on/off state |

### Debugging & development
| Command | Function |
|---|---|
| `idevicedebug` | Launch a bundle on the device and attach a debugger |
| `idevicedebugserverproxy` | Forward the debug-server port (for LLDB) |
| `idevicesyslog` | Stream the device system log in real time (incl. process list) |
| `idevicecrashreport` | Export crash reports |
| `idevicebtlogger` | Capture Bluetooth protocol logs |

### Backup & diagnostics
| Command | Function |
|---|---|
| `idevicebackup` / `idevicebackup2` | Backup / restore (newer protocol) |
| `idevicediagnostics` | Diagnostics (battery, crash state, …) |
| `ideviceimagemounter` | Mount the developer disk image (jailbreak / developer use) |
| `ideviceenterrecovery` | Force the device into recovery mode |
| `idevicescreenshot` | Save a device screenshot to the Mac |
| `idevicesetlocation` | Simulate GPS location (testing) |

### Network forwarding
| Command | Function |
|---|---|
| `iproxy` | Forward device ports to the Mac (e.g. 22 → SSH, 8080 → debug service) |
| `idevicenotificationproxy` | Listen for device notifications |

Most useful for macomrade: `ideviceinstaller list --user` (reconciliation),
`idevicepair` (trust flow), `idevicescreenshot` (mirror-free verification),
and `iproxy` (local debugging on the device).

## Enumerate installed apps (reconciliation)

```sh
ideviceinstaller -u <UDID> list --user   # CSV: bundleId, version, displayName
```

This is the machine-readable ground truth for `ios-app-catalog.json`
reconciliation (see `references/ios-application-workflow.md` and
`Private/ios-device-reconciliation-*.json`). Per-app metadata goes into
machine-local state; raw exports are never committed.

## Developer Mode & screenshot (know-how, verified 2026-08)

### Why "Developer Mode" does not appear in Settings

On iOS 16+, the **Developer Mode** toggle under *Settings → Privacy &
Security* is **hidden by default**. Apple gates it behind an initial pairing
with a Mac running Xcode: the option only appears after the device has been
connected to Xcode once. A device that has never been Xcode-paired shows no
Developer Mode entry at all — this is expected, not a UI miss.

### How to get Developer Mode visible

1. Connect the iPhone to a Mac with Xcode installed (any version; a full
   build/run is not required — connecting and letting Xcode recognize the
   device is enough).
2. The toggle appears under *Settings → Privacy & Security → Developer Mode*.
3. Turn it on; the iPhone prompts a restart. After reboot, confirm "Turn On"
   (passcode required).

`idevicedevmodectl` can print status (`list`), arm (`arm`), reveal the menu
(`reveal`), or enable (`enable`) — but **enable is rejected when the device
has a passcode** ("Device has a passcode set… enable it on the device itself").
Passcode-protected devices must always be enabled on-device.

### `idevicescreenshot` is broken on iOS 17+ (upstream issue)

`idevicescreenshot` requires the **Developer Disk Image** (`screenshotr`
service). **Apple stopped shipping DeveloperDiskImage with Xcode 15**
([libimobiledevice#1465](https://github.com/libimobiledevice/libimobiledevice/issues/1465),
open). Without a mounted image the tool fails with:

```text
Could not start screenshotr service: Invalid service / Password protected
Remember that you have to mount the Developer disk image...
```

Symptoms observed on iOS 27 (iPhone 15 Pro Max): error changed from
`Invalid service` (Developer Mode off) to `Password protected` (Developer Mode
on but image still absent) — the image is the missing piece in both cases.
**Conclusion: `idevicescreenshot` is not usable on iOS 17+; use iPhone
Mirroring (`screencapture -R<window region>`) instead.**

### `idevicesyslog` works without Developer Mode

Streaming device logs does not require the developer image:

```sh
python3 - <<'PY'
import subprocess, threading
proc = subprocess.Popen(["idevicesyslog", "-u", "<UDID>"], stdout=subprocess.PIPE, text=True)
threading.Timer(8, proc.kill).start()
print(proc.stdout.read())
PY
```

Verified: 8 s sample captured ~60k lines (apsd, locationd, bluetoothd,
identityservicesd activity; sensor readings). Most payloads are `<private>`
(iOS privacy redaction) but process names, timestamps, and non-private
diagnostics are readable.

### What Developer Mode actually unlocks (verified 2026-08, iOS 27)

With Developer Mode **enabled and the iPhone unlocked**, the lockdown
high-privilege services become reachable. Measured on PM15 (iPhone 15 Pro Max,
iOS 27.0):

| Tool | Before | After (DM on + unlocked) |
|---|---|---|
| `idevicedevmodectl reveal` | Password protected | ✅ menu revealed on device |
| `ideviceprovision list` | Password protected | ✅ 1 profile (com.gaussian.tool Team Store) |
| `idevicediagnostics All` | Password protected | ✅ battery GasGauge (CycleCount 611, FullChargeCapacity 100), HDMI, NAND |
| `idevicesyslog` | ✅ | ✅ (never required DM) |
| `ideviceinstaller` | ✅ | ✅ (never required DM) |
| `idevicescreenshot` | ❌ | ❌ still needs DeveloperDiskImage |
| `idevicedebug run/kill` | ❌ | ❌ still needs debugserver (from DM) |

Key facts:

- **"Password protected" errors mean the device screen is locked**, not that
  Developer Mode is off. Unlock the iPhone (screen on, passcode entered) and
  the lockdown services work — confirmed by
  [libimobiledevice#1273](https://github.com/libimobiledevice/libimobiledevice/issues/1273).
- Developer Mode's real value for libimobiledevice: `reveal`,
  `ideviceprovision`, and `idevicediagnostics` (battery health, NAND, WiFi).
- `screenshotr` and `debugserver` remain unavailable regardless of Developer
  Mode because Apple stopped shipping the Developer Disk Image with Xcode 15
  ([libimobiledevice#1465](https://github.com/libimobiledevice/libimobiledevice/issues/1465)).

## Troubleshooting

- `Pairing dialog response pending` → accept the trust dialog on the iPhone,
  or re-plug the USB cable to re-trigger it.
- No device found → confirm the cable is data-capable and the iPhone is
  unlocked; wireless pairing is not supported by `ideviceinstaller`.

## Cleanup

```sh
brew uninstall ideviceinstaller libimobiledevice   # only after explicit confirmation
```
