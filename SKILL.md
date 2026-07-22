---
name: install-macos-apps
description: Scan a Mac for installed applications, compare it with a persistent personal macOS app catalog, and create or execute a capacity-aware installation plan. Use when setting up a new Mac, auditing missing apps, maintaining a personal app inventory, installing selected apps with Homebrew, or documenting download sources, accounts, licenses, privacy permissions, and post-install tasks.
---

# Install My macOS Apps

Use this skill from its synced source folder. Treat the catalog as the source of truth; never infer that an app is installed merely because its installer or receipt exists.

## Mission: one-sync, ready-to-use Mac

The purpose of this repository is reproducible Mac bootstrap: after one
successful sync, a new Mac should reach the user's intended working state
through a bounded sequence of scan, install, authorize, configure, and verify
steps. This is more than an app list; it is the durable definition of the
machine's reusable operating baseline.

Keep the baseline in three layers:

- Tracked policy and desired configuration: `components/`, `references/`,
  `settings/`, `scripts/`, and this skill.
- Ignored machine observations: `state/`, including detected versions, paths,
  current permission observations, install logs, and cleanup measurements.
- User-controlled secrets and grants: never export passwords, tokens, raw TCC
  databases, or private documents. Record the required permission, reason,
  user action, and verification result instead; the user approves the actual
  grant on each Mac.

Portable expected operational state belongs in
[`settings/bootstrap-operational-baseline.yaml`](settings/bootstrap-operational-baseline.yaml).
This includes permission requirements, desired Login Item/LaunchAgent intent,
DNS/SmartDNS/VPN topology, and service verification contracts. It does not
make a current TCC grant portable, copy a startup database, or copy network
credentials. Each new Mac must apply or authorize the intent locally and then
write its own ignored `state/` observation for drift comparison.

The bootstrap order is staged: establish the machine baseline; inventory
required permissions; export and review allowlisted user preferences; install
Core components; request sign-ins, licenses, and device pairing; apply
approved policies; then run a final drift audit. Do not turn a broad `defaults`
dump or the TCC database into configuration. Every new preference or
permission needs a named purpose, read/check method, apply method, and
verification method.

### Shared Python Core policy

Python packages are managed as one tracked package set, not as individual
macOS catalog applications. The current shared environment is:

```text
~/.local/share/python/core/.venv
```

Its source of truth is:

```text
references/python-core/pyproject.toml
references/python-core/uv.lock
```

The runtime is Python 3.14 and the package manager is Homebrew `uv`. Keep the
default Core small and use uv dependency groups for `audio`, `data`, `llm`,
`agent`, and `dev`. The shared environment saves duplicate wheels across
repos, but it is not permission to install every ML framework into one
environment.

Install or refresh only from the reviewed manifest:

```sh
cd references/python-core
UV_PROJECT_ENVIRONMENT="$HOME/.local/share/python/core/.venv" \
  uv sync --locked --all-groups
```

Use `--group <name>` when a workflow needs only part of the package set. Do
not use `pip install --system` or `--break-system-packages` for this baseline.
Do not add large optional frameworks such as `whisperx`, `pyannote.audio`,
`ray`, `mlflow`, `llama-cpp-python`, vector databases, or multiple Agent
frameworks to the shared environment without a separate compatibility and
storage review. They may downgrade or replace MLX/data dependencies and should
normally receive their own uv environment.

The shared `.venv` and model caches are machine-local state, not tracked
policy. Record package versions, download/install measurements, and timestamps
under ignored `state/`; never record tokens, credentials, personal audio, or
model contents. Mole or other cleanup tools must not receive
`~/.local/share/python` as a purge path.

### Android developer environment

Android command-line tools, platform-tools/ADB, Java, and the Emulator are
Core developer dependencies. Follow [`references/environment.md`](references/environment.md)
for architecture-specific SDK packages and AVD setup. Derive all SDK paths
from `$(brew --prefix)`; Apple Silicon uses `arm64-v8a`, Intel uses `x86_64`.
QEMU arrives with the Android Emulator package and is not a separate Core
Homebrew install. `sdkmanager` is the sole owner of platform-tools/ADB for
this workflow; if a legacy `android-platform-tools` cask is present, verify
the SDK-managed binaries before removing only that duplicate cask. Treat
Java/cmdline-tools cask receipts as prerequisites only:
the environment is incomplete until `sdkmanager`, `adb`, `emulator`, and
`avdmanager` resolve in a fresh login shell and the selected AVD is listed.

### Whisper model selection

The `audio` group provides `mlx-whisper`; model weights are downloaded
separately into the user Hugging Face cache and must not be placed in the
repository or the shared venv. Choose models by the target Mac's available
resources:

| Profile | Model | Approximate cache size | Use |
| --- | --- | ---: | --- |
| Resource-constrained | `mlx-community/whisper-large-v3-turbo` | 1.61 GB | Fast everyday transcription |
| Large-RAM Mac | `mlx-community/whisper-large-v3-mlx` | 3.08 GB | Highest transcription accuracy and translation workflows |
| Ample disk/RAM | Download both models | 4.69 GB | Keep Turbo for speed and large-v3 for quality/translation |

Turbo is the default when memory is limited; large-v3 is preferred when RAM
is ample. The two models can coexist without changing Python dependencies.
Record model IDs, cache paths, measured sizes, and download timestamps in
ignored `state/`. Do not download model weights automatically when only the
Python package is requested; model download is a separate, size-visible step.
Treat `~/.cache/huggingface/hub` as a model-asset directory, not disposable
application cache. Mole and other automatic cleanup workflows must not delete
or purge it. Scans should report its total size and model subdirectories, but
deletion requires an explicit model-removal action. If a cleanup tool supports
a whitelist, protect `~/.cache/huggingface` there as defense in depth.

For Mole, this protection is part of the cross-device baseline. After Mole is
installed or detected, preserve existing entries and ensure this line exists:

```sh
mkdir -p "$HOME/.config/mole"
touch "$HOME/.config/mole/whitelist"
grep -qxF '~/.cache/huggingface' "$HOME/.config/mole/whitelist" || \
  printf '%s\n' '~/.cache/huggingface' >> "$HOME/.config/mole/whitelist"
```

Verify the resulting file before cleanup. This is local per-device
configuration and should be recreated during deployment rather than stored in
tracked `state/`.

### Optional audio model catalog

The tracked [`references/audio-model-catalog.yaml`](references/audio-model-catalog.yaml)
contains optional ASR weights. These are not macOS `.app` bundles and must not
be mixed into the App Store/Homebrew application catalog. Every such entry has
the `audio` tag, an explicit model ID, source URL, precision, approximate
download size, RAM envelope, and a verification command. Download at most one
large audio model at a time on a 16 GB Mac, and keep the existing Whisper
models as the comparison baseline until a user-owned Japanese meeting sample
has been evaluated.

For the current 16 GB M4 profile:

- Prefer **8-bit** for `Qwen3-ASR-1.7B` as the quality-first default. Its MLX
  conversion is about 2.46 GB and is the safest balance for long Japanese
  meetings. Use the MLX 4-bit conversion (about 1.5 GB) only as a fallback when
  memory pressure or swap is observed; do not silently replace the 8-bit model.
- `Kotoba-Whisper-v2.2` remains the latest Kotoba v2.x release found in the
  catalog. It is F32 and the official model is kept unquantized by default
  because its main value is Japanese transcription plus punctuation and
  diarization. Quantized community conversions may be used only after checking
  their provenance and measuring Japanese accuracy; diarization dependencies
  add a separate RAM and license review.
- Granite 4.0 1B Speech MLX 8-bit, Cohere Transcribe 03-2026 MLX 8-bit, and
  ReazonSpeech-k2-v2 INT8 are optional `audio` models. They are not Core app
  installations and are never downloaded as part of a normal app bootstrap.

## Required macOS permission preflight

Before running any workflow that checks Chrome profiles, verify that the
Codex/ChatGPT process can read:

```text
~/Library/Application Support/Google/Chrome/Local State
```

This requires macOS permission at **System Settings → Privacy & Security →
Full Disk Access** for the app hosting Codex/ChatGPT (or the terminal process
running the skill). If the read is denied, stop the Chrome-profile check and
ask the user to grant that permission, then retry. Never report all expected
profiles as missing when the underlying error is `Operation not permitted`.
The preflight reads only profile directories and account identifiers exposed in
Local State; it must never read cookies, passwords, tokens, or Keychain data.

### Permission inventory and bootstrap rule

Before extracting protected system configuration, inventory the permissions
needed by the current workflow. At minimum distinguish Full Disk Access,
Accessibility, Input Monitoring, Screen Recording, Automation, Files and
Folders, microphone, and camera. A requirement must state its target, purpose,
required/optional status, System Settings path, and verification method.
Reusable requirements belong in [`settings/privacy.yaml`](settings/privacy.yaml);
current results belong only in ignored `state/`.

The complete permission category registry is the
`permission_category_matrix` in `settings/privacy.yaml`. It includes both
TCC categories and capability-only observations such as network access. A
matrix row is not an instruction to grant permission: authorize only the
target and workflow named in that row, then verify the workflow visibly.

Run the read-only inventory with:

```sh
python3 scripts/macos_permissions.py
```

The script verifies the Chrome `Local State` read directly and labels other
TCC categories for manual verification. It never changes permissions.

For the full machine inventory, run:

```sh
python3 scripts/macos_permissions.py
```

The resulting ignored state record contains four separate evidence layers:

1. Every detected app bundle from `/Applications`, `~/Applications`, system
   applications, WebCatalog, and PlayCover, including Bundle ID, version,
   path, source, code-signing identity, and entitlement **keys**.
2. Read-only TCC rows matched to Bundle IDs, with
   `verified_granted`, `verified_denied`, `tcc_records_present`, and
   `no_record` kept distinct. A missing row is not a denial.
3. An App × observed-service matrix and entitlement/TCC reconciliation. An
   entitlement indicates declared capability, never user authorization.
4. Non-App components: Homebrew formulae/casks, LaunchAgents, LaunchDaemons,
   privileged helper tools, network services, VPN connections, System
   Extensions, and Background Task Management output.

The scanner may report `unavailable` for `systemextensionsctl` or
`sfltool dumpbtm`. Preserve the exact interface error; do not interpret it as
an empty inventory. It must not use `sudo` or silently elevate.

Entitlement values, notification contents, Focus rules, cookies, passwords,
tokens, TCC database bytes, and private document contents are never persisted.

macOS privacy grants are device-local TCC state. The skill may check them and
open System Settings, but must not pretend that a raw TCC database copy,
`tccutil` reset, or stored authorization token is a portable grant. On a new
Mac, repeat visible authorization and then record the verification result
locally.

### User-preference extraction rule

Extract preferences by an allowlist, one domain at a time. Start with the
tracked Dock order and keyboard policy, then add input sources, Finder,
appearance, default applications, login items, and other explicitly selected
domains only when their values are understood and reproducible. Desired values
belong in tracked `settings/`; raw current readings and comparisons belong in
`state/`. Never persist recent-document lists, private paths, serial numbers,
or secrets unless the user explicitly declares them portable.

Capture the first allowlisted baseline with:

```sh
python3 scripts/macos_preferences.py
```

This is an export/check operation only. Applying a preference requires a
separate reviewed policy entry and an explicit verification step.
After the desired values have been reviewed, compare them with the current
Mac using `python3 scripts/macos_preferences.py --check`.
Applying the reviewed values requires an explicit confirmation:

```sh
python3 scripts/macos_preferences.py --apply
python3 scripts/macos_preferences.py --check
```

The apply path is limited to the tracked allowlist and restarts Finder and
Dock so their settings reload; it does not apply permissions, login items,
default applications, or input-source changes.

The preference scanner currently captures an allowlisted baseline for machine
profile, locale/input sources, keyboard/HID mappings, text-input settings,
Dock/Finder, desktop/window management, screenshots, displays, sound/power
interfaces, notifications, Control Center, Focus database presence, and
screensaver fields. It also records a redacted LaunchServices association
slice and the developer environment shape: Shell, startup-file hashes, PATH
shape, Git key names, SSH config metadata, and CLI versions. Redact private
paths and text-substitution contents; never persist Git identity values, SSH
contents, or credentials. `--check` compares only tracked desired values;
unavailable interfaces remain unavailable rather than being converted to
defaults.

For hardware/network interfaces that return `AuthorizationCreate() failed:
-60008` or incomplete data in a non-admin shell, an explicitly requested
read-only baseline may use the macOS administrator authorization dialog for
`system_profiler`, `networksetup`, `scutil`, and `fdesetup`. Store only the
redacted result under ignored `state/`; omit display serial numbers, Wi-Fi
passwords, VPN credentials, certificates, and private keys. Do not use this
path to change DNS, proxy, firewall, FileVault, or VPN settings.

### Application workstyle baseline

Portable application behavior is defined in
[`settings/app-workstyle.yaml`](settings/app-workstyle.yaml). It separates
desired policy from current machine observations and manual authorization.
Use read-only checks first, then apply one app policy at a time. Account
identifiers, session databases, Keychain entries, app containers, IPA files,
private paths, and device telemetry are never portable configuration. The
current verification set covers K240, Solaar, Claude Developer Mode,
PlayCover YouTube, SmartDNS, Dock order, and startup listeners. GUI Login Items
remain incomplete until Automation permission is available.

### Bootstrap entry point

Use the ordered, read-only assessment before any new-Mac changes:

```sh
python3 scripts/bootstrap_macos.py --profile auto
```

It runs app scan, capacity-aware app plan, permission inventory, and
preference baseline/check in order. It never installs apps, grants TCC
permissions, enters accounts, or applies preferences. Review its generated
`state/bootstrap-*.json` record before separately authorizing any change.

Manual account, license, privacy, browser-profile, VPN, and app-configuration
checkpoints live in [`settings/manual-actions.yaml`](settings/manual-actions.yaml).
They are instructions and verification contracts only; never turn them into
credential storage or automatic login.

For Capacities, the app and its app-specific data are retired and may be
removed after the user explicitly requests cleanup:

```sh
python3 scripts/capacities_migration_inventory.py
```

It records only candidate locations, sizes, counts, and extensions. It does
not read document contents. After the user's cleanup confirmation, remove the
app bundle and its Capacities-owned support data with the auditable cleanup
script:

```sh
python3 scripts/capacities_cleanup.py --apply --confirm
```

The cleanup includes Capacities Application Support, preferences, HTTP storage,
and logs, and records measured reclaimed space in `state/`. Do not remove
unrelated browser profiles or other application data.

Chrome profile identity is matched by account email. Profile directory names
such as `Profile 5`, `Profile 7`, or `Profile 9` are machine-local allocation
details and are informational only; they must not cause a missing-account
result or be used as the cross-machine identity key. Display names are checked
separately against the tracked registry.

Run the final read-only drift/recovery report with:

```sh
python3 scripts/bootstrap_verify.py
```

It records missing Core apps, source mismatches, permission drift,
preference-check results, and safe rerun commands. It never applies the
recovery commands automatically.

Login Items have two separate sources. User `LaunchAgents` can be inventoried
read-only from `~/Library/LaunchAgents`. The GUI Login Items list is queried
through Apple Events and may require an explicit Automation permission. If
that query fails, record the error and the LaunchAgents subset; never call a
partial result a complete Login Items baseline.

### Stale TCC authorization cleanup

Use [`scripts/macos_permissions_cleanup.py`](scripts/macos_permissions_cleanup.py)
for permissions belonging to apps that were deliberately removed. Its default
mode is dry-run:

```sh
python3 scripts/macos_permissions_cleanup.py
```

The script includes only classified legacy/removed clients by default. Add
`--include-manual-review` only after confirming an unlisted client is no longer
needed. Applying a reset requires `--apply` and typing `CLEAN TCC`; it calls
`tccutil reset` for exact service/client pairs and never removes application
data. Re-run the permission inventory afterward. Never reset current ChatGPT,
CUA, Perplexity, Logi Options+, or other active helper identities as part of a
generic cleanup.

The cleanup script uses the latest permission state and includes only clients
classified as legacy/removed by default. Manual-review clients require
`--include-manual-review`. It never deletes app data or repairs an incomplete
uninstall; Homebrew cask cleanup and data migration are separate tasks.

System Extension and Background Task discovery may be restricted by macOS:
`systemextensionsctl list` can return an OSSystemExtensionError, while
`sfltool dumpbtm` may require an administrator authorization context. Record
those exact interface states as unavailable or authorization_required; do not
interpret them as evidence that no extension or background task exists.

When a complete inventory is explicitly requested, the read-only commands may
be retried through the macOS administrator authorization dialog:

```sh
osascript -e 'do shell script "/usr/bin/systemextensionsctl list" with administrator privileges'
osascript -e 'do shell script "/usr/bin/sfltool dumpbtm" with administrator privileges'
```

Store the resulting raw observation only under ignored `state/` and record the
exact authorization context. In the current M4B result, System Extensions
reported `0 extension(s)` and Background Task Management returned real records;
these are observations, not portable grants or enable/disable instructions.

## Keyboard settings workflow

Keyboard configuration has a dedicated entry point and must not be scattered
through app component guides:

- Main policy: `settings/keyboard.yaml`
- Device profile: `settings/keyboards/logitech-k240-japanese-dictation.yaml`
- Native K240 listener: `scripts/keyboard-config-logi-k240.swift`
- Machine-specific observations: ignored `state/` and
  `~/Library/Logs/install_my_macos_apps/`

### Logitech K240 profile

The K240 Japanese keyboard uses a Logitech USB receiver. Confirm all of the
following before applying its profile:

```sh
hidutil list
defaults read -g AppleSelectedInputSources
```

The expected receiver is Logitech `VID 0x046d`, `PID 0xc534`; the physical
keyboard model must also be confirmed as K240, and the active input layout must
be Japanese. The receiver identifier alone is not enough to distinguish every
keyboard paired to that receiver.

### Logitech MX Keys Mac profile

When a Logitech MX Keys Mac is detected, prefer Logitech Options+ hardware
remapping for F1/F2 and other function keys. It works at the device layer and
avoids a custom HID listener, Fn-layer ambiguity, and Input Monitoring grants.
Use a native Swift listener only for hardware without a reliable vendor
configuration tool, such as the documented K240 fallback profile.

The current target mapping is:

```text
F1  Open ChatGPT.app
F2  Open Claude.app
F3  Open Perplexity.app
F4  Mission Control
F5  Open YouTube.app if present (including PlayCover), otherwise Apple Music
F6  Previous Track
F7  Play/Pause
F8  Next Track
F9  Mute
F10 Volume Down
F11 Volume Up
F12 Open macOS Screenshot.app toolbar
```

Use native `hidutil` consumer usages for F6–F11. These mappings are local HID
state, not iCloud settings, and can disappear after restart, logout, or a
receiver reconnect. Reapply and verify them rather than assuming persistence:

```sh
hidutil property --set '{"UserKeyMapping":[
  {"HIDKeyboardModifierMappingSrc":30064771135,"HIDKeyboardModifierMappingDst":3221225654},
  {"HIDKeyboardModifierMappingSrc":30064771136,"HIDKeyboardModifierMappingDst":3221225677},
  {"HIDKeyboardModifierMappingSrc":30064771137,"HIDKeyboardModifierMappingDst":3221225653},
  {"HIDKeyboardModifierMappingSrc":30064771138,"HIDKeyboardModifierMappingDst":3221225698},
  {"HIDKeyboardModifierMappingSrc":30064771139,"HIDKeyboardModifierMappingDst":3221225706},
  {"HIDKeyboardModifierMappingSrc":30064771140,"HIDKeyboardModifierMappingDst":3221225705}
]}'
hidutil property --get UserKeyMapping
```

### F1–F3, F5, and F12 native listener implementation

Do not rely on editing `com.apple.symbolichotkeys` IDs for this profile. Those
preferences may read back as successfully changed while an external K240 key
still does nothing. macOS's standard `Command-Shift-4` is area capture;
`Command-Shift-5` opens the Screenshot toolbar. The intended K240 behavior is
F12 opening the latter.

The supported implementation is the small native Swift HID listener:

```sh
swiftc scripts/keyboard-config-logi-k240.swift -o /tmp/keyboard-config-logi-k240
/tmp/keyboard-config-logi-k240
```

The listener handles F1, F2, F3, F5, and F12. F4 is handled by macOS's
native Mission Control shortcut configuration and is intentionally excluded
from the listener:

1. Matches only Logitech receiver `0x046d:0xc534`.
2. Filters the USB HID keyboard page `0x07`: F1 `0x3a`, F2 `0x3b`, F3
   `0x3c`, F5 `0x3e`, and F12 `0x45`.
3. Debounces duplicate reports from the receiver.
4. Opens ChatGPT.app, Claude.app, Perplexity.app, YouTube.app when present
   (including `~/Applications/PlayCover/YouTube.app`), otherwise Apple Music,
   or Screenshot.app.
5. Writes operational diagnostics to
   `~/Library/Logs/install_my_macos_apps/keyboard-config-logi-k240.log`.

The first validation must run in the foreground. Press F1, F2, F3, F5, and
F12 one at a time and confirm ChatGPT, Claude, Perplexity, YouTube or Apple Music, and the
Screenshot toolbar respectively. Separately verify left Command twice for
Dictation. If the listener cannot open the receiver, grant
**Privacy & Security → Input Monitoring** to the terminal or installed
listener does not need Accessibility for the direct application launches.
Screenshot capture permissions remain
controlled by the native Screenshot app and macOS Screen Recording settings.

The listener source is the reusable implementation; an always-on LaunchAgent
is a separate installation step. When persistence is requested, install the
template `templates/keyboard-config-logi-k240.launchagent.plist` as
`~/Library/LaunchAgents/com.xvk.install-my-macos-apps.keyboard-config-logi-k240.plist`.
The LaunchAgent is receiver-scoped: the Swift filter matches only Logitech
`0x046d:0xc534`, so another brand or another receiver will not activate these
actions. The receiver ID does not uniquely prove the paired physical keyboard
is K240. Verify the loaded agent and record its current status in ignored
`state/`.

The installed user-level paths are:

```text
Binary:       ~/Library/Application Support/install_my_macos_apps/bin/keyboard-config-logi-k240
LaunchAgent:  ~/Library/LaunchAgents/com.xvk.install-my-macos-apps.keyboard-config-logi-k240.plist
Logs:         ~/Library/Logs/install_my_macos_apps/keyboard-config-logi-k240.log
```

The `~/Library` directory is hidden. Use `open -R` to locate the binary. Input
Monitoring is macOS TCC-protected: CLI can open the settings page, but cannot
silently grant the permission. `tccutil` resets permissions; it does not grant
Input Monitoring to a new executable. Recompiling/replacing the binary may
invalidate the previous grant. Every replacement of the Swift binary must
automatically run the following two commands before asking the user to grant
the permission:

```sh
open -R "$HOME/Library/Application Support/install_my_macos_apps/bin/keyboard-config-logi-k240"
open 'x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_ListenEvent'
```

If the log says `Unable to open Logitech receiver`, stop the `KeepAlive` agent,
authorize the exact binary in Input Monitoring, and reload it:

```sh
open -R "$HOME/Library/Application Support/install_my_macos_apps/bin/keyboard-config-logi-k240"
open 'x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_ListenEvent'
launchctl bootstrap gui/$(id -u) \
  "$HOME/Library/LaunchAgents/com.xvk.install-my-macos-apps.keyboard-config-logi-k240.plist"
```

F4 remains a native macOS Mission Control shortcut (symbolic hotkey ID 32) and
must not be duplicated in Swift. F5 chooses YouTube in this order:

1. `/Applications/YouTube.app`
2. `~/Applications/PlayCover/YouTube.app/YouTube` (direct executable)
3. `/System/Applications/Music.app`

PlayCover's YouTube bundle is not a conventional macOS `.app` bundle: its
`Info.plist` is at the bundle root rather than under `Contents/`. Therefore
`open -a ~/Applications/PlayCover/YouTube.app` can fail with Launch Services
error `-10670`; launch the inner `YouTube` executable instead.
Before starting it, query the running application by bundle identifier
`com.google.ios.youtube`; if it is already running, activate its existing
windows rather than creating another process. The listener must also clear
the macOS Accessibility `AXMinimized` attribute before activation, because
`activate(.activateAllWindows)` alone does not reliably restore a window
minimized with the yellow button. If the app activates but remains minimized,
grant the installed listener Accessibility permission and retry. This preserves
the normal single-instance behavior expected from ChatGPT and Claude.

### Known keyboard limitations

The native listener is scoped to the Logitech receiver identifiers, but the
listener must still be foreground-tested after macOS updates or receiver
changes. Do not install Karabiner-Elements as an implicit dependency.

### Logitech K240/M212 battery telemetry

The current hardware pairing is a Logitech K240 keyboard and M212 mouse using
the shared receiver `VID 0x046d`, `PID 0xc534`. The receiver identifier alone
does not prove the physical device models. macOS `hidutil`, `ioreg`, and
`pmset` do not expose their battery values as native macOS battery devices.

Logi Options+ and OpenLogi may install successfully while still failing to
detect these legacy devices. Do not interpret that as an installation failure.
Use the optional Solaar workflow in `components/solaar.md` as the next
macOS-native experiment; Solaar has explicit Nano receiver support but only
limited macOS support.

Solaar battery values are device-reported and may be approximate. The details
pane must be selected for each device before assigning a value to keyboard or
mouse. A label such as `next reported 5%` is a future reporting threshold, not
the current battery level. Never infer the second device's identity from its
row alone; confirm the right-hand details pane.

Solaar has no official Homebrew cask. The supported macOS setup installs its
dependencies with Homebrew, installs Solaar through `pipx`, and creates a local
`/Applications/Solaar.app` wrapper from the official GitHub script:

```sh
brew install hidapi gtk+3 pygobject3 pipx
pipx install --system-site-packages solaar
bash <(curl -fsSL https://raw.githubusercontent.com/pwr-Solaar/Solaar/refs/heads/master/tools/create-macos-app.sh)
```

Quit Logi Options+ and OpenLogi before Solaar accesses the receiver. Keep
current battery readings, detected names, versions, and permission results in
ignored `state/`, not synced catalog or policy Markdown. Do not send unknown
write commands to the receiver; battery investigation must remain read-only.

Keyboard policy is machine-local. Do not claim that `defaults`, `hidutil`, or
the Swift listener synchronizes through iCloud. Keep reusable policy in
`settings/`; keep current device detection, permissions, versions, and test
results out of synced policy files.

## Startup item and login component audit

Use `scripts/macos_startup_items.py` when the user asks what launches at login
or wants to remove selected startup applications/components:

```sh
python3 scripts/macos_startup_items.py scan
python3 scripts/macos_startup_items.py review
```

The scan reports three sources: macOS Login Items, the current user's
`~/Library/LaunchAgents`, and Background Task Management entries from
`sfltool dumpbtm`. The numbered `review` flow requires an explicit `DISABLE`
confirmation for each selected batch. It can remove a Login Item or disable a
user LaunchAgent; it does not automatically modify system LaunchDaemons,
delete applications, delete caches, or remove Background Task Management
records directly. Background-task entries are report-only and must be handled
through their corresponding Login Item or vendor setting.

Disabling a user LaunchAgent unloads it and renames its plist from `.plist` to
`.plist.disabled`, preserving a reversible copy. Never infer that an installed
app should launch merely because its bundle appears in the scan. After a
change, run `scan` again and record the result in ignored `state/` when a
machine-specific audit is needed.

## Dock configuration and order audit

The desired persistent Dock applications and their left-to-right order are
reusable skill configuration. The current machine's existence checks and scan
metadata are machine-local state. Scan and save both with:

```sh
python3 scripts/macos_dock.py
python3 scripts/macos_dock.py --save-config
```

The scan JSON in `state/` preserves the ordered application list, bundle
identifier, path, existence check, and a `kind` classification. The reusable
configuration is stored in `settings/dock-order.json` without machine scan
timestamps or `exists` values. `kind` distinguishes
`system`, native third-party `native`, PlayCover `playcover`, and WebCatalog
wrappers `webcatalog`. A Dock entry is not evidence that an application is in
the reusable catalog or that it is installed from the same source.

In particular, the current Dock entries for **Notion** and **X** are
WebCatalog applications under `~/Applications/WebCatalog Apps/`, not native
Notion or X macOS applications. Preserve that distinction in audits and do not
replace their paths with `/Applications/Notion.app` or `/Applications/X.app`.

`settings/dock-order.json` is the desired baseline and is persisted with the
skill. It does not automatically reorder the Dock; any future apply workflow
must compare it with a fresh scan and explicitly request the user's approval.
Keep only current machine observations in ignored `state/`.

Dock appearance and behavior are tracked separately in
`settings/system-preferences-values.json`. The baseline currently requires:

- Dock on the left, 128 px tile size, and no Recent Applications section;
- launch animation enabled and running-app indicators enabled;
- minimize windows into their owning App icon (`minimize-to-application=true`),
  so minimized-window thumbnails are not shown as separate Dock items;
- no persistent directory stacks, including the “最近下载”/Downloads stack;
- unspecified Dock keys remain macOS defaults unless explicitly added to the
  baseline after review (for example, auto-hide, magnification, and minimize
  effect are not silently inferred).

Run `scripts/macos_preferences.py --check` to compare these values. Apply them
only through the normal explicit-confirmation preference workflow, then restart
the Dock if macOS does not reload the values immediately.

## Developer-machine Gatekeeper policy

This skill is primarily used for development Macs. The default developer
profile therefore records the following optional system policy in the plan:

```sh
sudo spctl --global-disable
```

This changes Gatekeeper from its normal assessment policy to the broader
“Anywhere” mode, making it easier to install trusted developer tools that are
not from the App Store or an identified/notarized developer. It is a deliberate
security trade-off: never run it silently. Before the first execution on a Mac,
show the user the exact command and obtain explicit confirmation. On recent
macOS releases, keep **System Settings → Privacy & Security** open, run the
command from a visible Terminal, then close and reopen that settings pane; the
“Anywhere” choice is hidden until this confirmation flow has been triggered.
If an automated administrator prompt is used, it may return “needs to be
confirmed in System Settings” rather than changing the policy. Verify the
result with `spctl --status` (expected output: `assessments disabled`) and
record only the policy state and timestamp in the ignored `state/` record; do
not put machine state in a component guide.

The matching rollback command is:

```sh
sudo spctl --global-enable
```

If the user declines the global policy, continue with the safer per-application
workflow: use macOS Privacy & Security → **Open Anyway** for a trusted app, or
use a narrowly scoped Homebrew cask install option when appropriate. Never
disable Gatekeeper merely to bypass an unverified or suspicious download.

## Workflow

1. Inspect the current Mac and write a dated scan:

   ```sh
   python3 scripts/macos_apps.py scan
   ```

   The scan records source evidence for catalog apps. An App Store receipt is
   checked at `Contents/_MASReceipt/receipt`; Homebrew casks are checked against
   `brew list --cask`; other bundles are reported as `manual_or_unknown`. A
   source mismatch is a review item, not proof of malicious software. A cask
   receipt alone is not proof that a usable `.app` bundle exists: some casks
   install a privileged vendor installer and place the real app under a system
   support directory until reboot. The final check must find the expected app
   bundle (or the component's documented post-reboot service) and launch/verify
   it; do not close a missing-app item merely because `brew list --cask` lists it.

2. Create a plan. Use `auto` unless the user explicitly selects a capacity tier:

   ```sh
   python3 scripts/macos_apps.py plan --profile auto
   ```

   `portable` applies below 512 GB; `expanded` applies at 512 GB or above. The planner includes `core` apps in both tiers, while apps marked `heavy` are excluded from `portable` by default. Large games and other entertainment packages should remain outside the compact-memory Mac profile; install them only on a separately designated expanded-memory gaming machine.

3. Review the plan with the user. Select one or two apps only. Identify required free space, account/permission tasks, and any source that is not Homebrew. Do not run installations before confirmation.

   Homebrew CLI-only entries marked as approved recommendations may be
   installed in batches of up to five after one confirmation. GUI applications,
   App Store applications, official website downloads, and any item requiring
   account or permission decisions remain strictly one at a time.

   Review `source_mismatches` before installing. For example, Slack and Telegram
   are cataloged as `app_store`; if their bundles have no App Store receipt, tell
   the user they appear to come from a website or another installer and offer a
   reinstall from the App Store. Never delete or replace the existing bundle
   automatically. The user must explicitly approve any reinstall and decide
   whether to remove the old copy first.

   **Perplexity source rule:** Perplexity is website-only. If a detected bundle
   contains `Contents/_MASReceipt/receipt`, it is a legacy Mac App Store build
   and must be removed **before** downloading or installing the website build.
   This is an explicit source-replacement exception to the general
   “never-delete-during-scan” rule. After removal, install and verify the
   website bundle (version, Bundle ID, launch, and permissions). Delete only
   the old App bundle; never delete Perplexity support data or login state.

   **X source rule:** X is WebCatalog-only. Native and Mac App Store X bundles
   are rejected even when they launch. Create and verify the `https://x.com/`
   WebCatalog wrapper under `~/Applications/WebCatalog Apps/`; only after that
   verification may the user approve removal of `/Applications/X.app`. Never
   remove browser or account data during this source replacement.

   **Notion source rule:** Notion is WebCatalog-only. Reject native, Homebrew,
   and Mac App Store Notion bundles even when they launch. Create and verify
   the `https://www.notion.so/` WebCatalog wrapper under `~/Applications/WebCatalog Apps/`,
   then move the old `/Applications/Notion.app` to Trash. The old native
   Notion app's support data, caches, containers, and offline data are
   disposable under this user's baseline and should be removed after the
   WebCatalog replacement is verified. Do not delete browser profiles or
   unrelated WebCatalog data.

   **X/Notion cleanup rule:** For either WebCatalog source replacement, app
   bundles, app-specific support data, caches, containers, and offline data for
   the retired copy are disposable and must be removed after the replacement
   is verified. Measure and record them in `state/`; never remove browser
   profiles or unrelated application data.

   **Privileged Homebrew cask rule (Logi Options+ and similar installers):**
   Some Homebrew casks are installer wrappers rather than drag-and-drop `.app`
   bundles. Run them from a visible Terminal when the installer requests
   administrator authorization; Codex must not collect or persist the password.
   If an old bundle is owned by `root:admin`, stop and hand off to the user for
   the visible `sudo` password prompt before removing it. After installation,
   inspect the expected app path and vendor support/service path, then reboot
   when the cask caveat requires it. Only after reboot run `scan` and `plan`
   again. A completed Homebrew transaction with no app bundle is an incomplete
   installation, not a successful source repair. Record the cask version,
   reboot requirement, and post-reboot scan under ignored `state/`; never store
   the password or raw privileged logs.

   **Logi Options+ residue rule:** After Logi Options+ has installed and passed
   its post-reboot check, `/Applications/logioptionsplus_installer.app` is
   removable installer residue. Keep `logioptionsplus.app`,
   `Utilities/LogiPluginService.app`, the Driver Installer bundle, and Logi
   support directories; they are runtime components. Record the removed path
   and measured size under ignored `state/`.

4. Execute only after explicit approval. Start with a dry run, then apply the recorded plan:

   ```sh
   python3 scripts/macos_apps.py install state/PLAN.json --only "App Name"
   python3 scripts/macos_apps.py install state/PLAN.json --only "App Name" --apply

   Components marked `retired_pending_cleanup` remain installed while the
   user completes data export or migration. Do not delete their app, support
   data, or caches during a generic scan; require a separate explicit cleanup
   request after the data handoff is verified.
   ```

   The script accepts at most two `--only` values per run. It bootstraps Homebrew only with `--apply` and asks interactively first. It installs only catalog entries with a verified Homebrew cask or formula identifier. It never supplies credentials, modifies privacy settings, or silently installs an unverified DMG/PKG.

   **Homebrew dependency-upgrade guard:** Homebrew may otherwise upgrade an
   existing formula while installing a new one. This skill's installer invokes
   `brew install` with `HOMEBREW_NO_AUTO_UPDATE=1` and
   `HOMEBREW_NO_INSTALL_UPGRADE=1`, so an install does not silently upgrade
   unrelated packages such as an existing FFmpeg. Before an apply, record
   relevant installed versions; if the transaction still needs a dependency
   upgrade, stop and present the old/new versions, reason, download size, and
   disk impact for confirmation. Run that upgrade separately only after
   approval. Do not use a global same-major-version assumption. Read
   [references/homebrew-install-policy.md](references/homebrew-install-policy.md)
   for the detailed policy and temporary pin guidance.

   **IPATool authentication and IPA workflow:** IPATool is a Core Homebrew
   formula, but it is not a prerequisite for PlayCover. M4a and M4b verified
   that its Apple account/authentication workflow is not usable for the
   required IPA packages. Install it only as a general developer utility with
   `brew install ipatool` and verify with
   `ipatool --version`. Before downloading an App Store package, identify the
   intended App Store purchase account; the current iCloud account is only a
   candidate because iCloud and App Store purchase accounts may differ. Start
   `ipatool auth login --email "<APPLE_ID>"` from a visible Terminal so the
   user can enter the password and six-digit two-factor code. Never collect,
   display, log, or persist these secrets in Markdown, `state/`, Obsidian, or
   Git. Verify with `ipatool auth info`; the CLI does not provide a native
   macOS Passkey/Touch ID login prompt. For YouTube, search/download using
   bundle ID `com.google.ios.youtube`. IPATool downloads an App Store package
   that may be encrypted; it is not automatically a PlayCover-compatible IPA
   and must not gate the YouTube workflow.
   PlayCover requires a decrypted IPA, so do not claim success until import
   and launch are tested. Keep the downloaded IPA and authentication result in
   ignored machine-local state only, and use `ipatool auth revoke` when the
   account should no longer remain authenticated. See
   [components/ipatool.md](components/ipatool.md).

   **YouTube through PlayCover:** treat YouTube as a separate Core capability
   installed after PlayCover. Use the current decrypted YouTube entry from the
   configured `approved-private-source.invalid` IPA Library (or another explicitly approved,
   reputable decrypted-IPA source); do not persist a version-specific
   direct IPA URL in the catalog. For the validated YouTube 21.28.3 profile,
   after importing, open the app's Settings → Misc and explicitly click
   **Remove PlayTools**; PlayCover may install PlayTools automatically during
   import, but it must be removed before the first launch.
   PlayTools must remain removed. Keep PlayChain off, Jailbreak Bypass on,
   Introspection libraries off, and Force Insert iOS Frameworks on. Use the
   iPad Pro 13-inch (7th generation) M4 8 GB device profile, 1080p, 4:3, and
   Resolution Scaler 2.0. If YouTube crashes with `PlayKeychain.copyMatching`,
   `igdrms`, or a PlayTools frame in the crash report, do not change DNS,
   Full Disk Access, or SIP; first verify that PlayTools was not reinjected.
   See [components/youtube-playcover.md](components/youtube-playcover.md).
   **Login persistence limitation:** PlayChain was tested for this validated
   YouTube installation but did not reliably preserve the login session, while
   PlayTools cannot be reintroduced because it causes the tested build to crash
   during PlayKeychain/DRM initialization. The supported workflow is to expect
   a fresh YouTube login after the app is fully quit and reopened. Do not keep
   changing PlayTools/PlayChain or delete Keychain entries and PlayCover data
   automatically; persistent login is a future compatibility investigation.

   **Claude pre-install storage gate:** before installing or replacing Claude,
   run `python3 scripts/claude_vm_cleanup.py inspect`. The VM review and any
   cleanup are separate actions from the Claude installation. **Analyze Disk is
   mandatory completion work for every Claude install or replacement:** if
   `claudevm.bundle` exists, report its total size and obtain explicit approval
   to remove the complete bundle with `remove-bundle --confirm "REMOVE CLAUDE VM BUNDLE"`.
   Only after the user explicitly confirms, and only after Claude is fully quit, may the skill
   run `remove --confirm "REMOVE CLAUDE VM IMAGES"` or the complete-bundle removal.
   Optional directory locking
   is a second confirmation using `lock --confirm "LOCK CLAUDE VM DIRECTORY"`;
   it disables Cowork/local-agent VM recreation and is never implicit. See
   [components/claude.md](components/claude.md).

   **Claude Desktop Developer settings:** after Claude Desktop opens and the
   intended account is verified, automatically inspect the Help menu. If it
   shows `Help → Troubleshooting → Enable Developer Mode`, the skill must click
   that menu item, accept the app's non-binding warning, and wait for Claude to
   restart. This is a local application preference and does not enter
   credentials or change macOS privacy permissions. Verify that the top-level
   `Developer` menu appears; if it already shows `Disable Developer Mode`, the
   check passes. Then inspect `Developer → Configure Third-party Inference…`.
   Verify required Local MCP servers separately. Never
   enter, display, log, or sync API keys through the skill, and never store them
   in the catalog, `state/`, Obsidian, or Git. If the build exposes the
   third-party inference page, the user may manually configure the Gateway base
   URL, credential kind, custom headers, model discovery, and model list. Test
   each provider with a non-sensitive prompt and record only provider name,
   endpoint type, model name, and pass/fail. If the menu is absent, mark the
   feature blocked and report the build version. Use the GUI for this workflow;
   do not edit Claude's local configuration files directly.

   **Claude Desktop model compatibility guard:** a Gateway endpoint being
   Anthropic-protocol-compatible does not mean the Desktop model list accepts
   the provider's native model IDs. Current builds validate model entries as
   Anthropic-family routes. In particular, adding an OpenRouter ID such as
   `deepseek/deepseek-v4-pro` can produce the warning `Doesn't look like an
   Anthropic model` and can leave Claude Desktop in a `provider setup needs a
   fix` state after relaunch. Before applying a non-Anthropic model, run the
   real GUI validation; if that warning appears, remove the entry, save and
   apply the restored list, relaunch, and verify the setup warning is gone.
   Do not treat community alias/proxy workarounds as native support. Use
   Claude Code CLI, OpenCode, or a separately tested Anthropic-compatible
   proxy/router for DeepSeek instead.

   Claude Desktop's model-list editor is not a general OpenRouter model
   switcher. It validates entries as Anthropic-family gateway routes. A
   non-Anthropic OpenRouter ID such as `deepseek/deepseek-v4-pro` can be
   accepted by the form but leave the provider setup malformed after relaunch.
   Before applying any manual entry, check the validation message; if it says
   the route is not an Anthropic model, discard/remove the entry, save and
   apply the restored list, relaunch Claude, and verify that the setup warning
   is gone. Use a separate tested Anthropic-compatible router/client when a
   non-Anthropic model is required.

   **Restore the original Claude subscription:** Developer Mode may remain
   enabled; it is independent of the inference mode. When Claude Desktop is
   in `Gateway` / 3P mode and the user wants the original Claude subscription,
   use the current Gateway account menu's `Sign out`/`Logout` action. After
   Claude relaunches, sign in again at `claude.ai` with the original Claude
   account. Verify the URL is `claude.ai/new`, the Gateway indicator is gone,
   and the model picker shows the subscription model. Do not remove Developer
   Mode as part of this switch. If sign-out does not restore the login flow,
   stop before deleting local state and report that 3P recovery requires a
   backed-up state reset.

   **LM Studio and multi-provider Gateway settings:** LM Studio is a local
   model server, not a general-purpose cloud API key proxy. Its current
   official server supports OpenAI-compatible endpoints and
   Anthropic-compatible `/v1/messages`; use it as a local backend for models
   loaded into LM Studio. Do not assume that a DeepSeek official API key can
   be stored in LM Studio and transparently forwarded to
   `api.deepseek.com`. For OpenRouter, DeepSeek, Google, and LM Studio behind
   one Claude Desktop Gateway, use a separate routing layer such as a tested
   Anthropic-compatible router, and keep provider keys in that router's secret
   store rather than in the catalog or component guides. Test model discovery,
   tool calls, streaming, and the exact model ID separately; compatibility at
   the HTTP endpoint does not guarantee agent compatibility.

   **LM Studio Bionic:** Bionic is the active `core` application for this Mac
   for code, documents, voice, and open-model agent workflows. Verify the
   official Bionic download page and macOS build before installing; do not
   substitute an unofficial similarly named download. Classic LM Studio is
   retired in this catalog. Bionic and classic LM Studio use the same `llmster`
   daemon, so do not run both local backends concurrently. Preserve shared
   model data unless the user explicitly requests cleanup.

   After installing Bionic, rename the application bundle in `/Applications`
   to `LM Bionic.app` for local organization. Do not change the bundle
   identifier or internal metadata. Open the renamed app once and verify launch
   success before marking installation complete.

   If classic LM Studio is installed, treat it as `retirement_pending`: quit
   both applications, verify Bionic's local/cloud workflows, then remove only
   the classic app bundle if requested. Do not delete `~/.lmstudio` as part of
   routine retirement.

   **Bionic capability verification:** treat the current Bionic build as an
   initial preview and verify these surfaces after installation:

   - Work Projects: research, writing, analysis, document editing, and
     generation of documents, presentations, spreadsheets, and other files in
     a managed workspace.
   - Code Projects: a selected local working directory with file search,
     code explanation, edits, Git visibility, shell tools, test execution, and
     documentation updates.
   - Sessions and tabs: separate task conversations, background sessions,
     side-by-side sessions, project files, and response forking.
   - Model routing: local models, remote models through LM Link, and hosted
     open models through LM Studio Secure Cloud.
   - Local model management: discover/download models and use models that fit
     the Mac's available memory and runtime support.
   - Web Search: optional fresh web context for Work Projects; verify that
     billing is enabled before treating it as available.
   - Account and billing: local and LM Link models do not require an account;
     Secure Cloud models require sign-in, credits, and network access.

   Record whether each test used local, remote, or cloud inference. Never
   assume that a feature works with every model: check tool support, image
   input, reasoning controls, streaming, and filesystem/shell permissions.

## App Store workflow

Use this workflow for every catalog entry with `app_store_url`. It is the
default deployment method for a personal user with several Macs; Apple
Configurator is not a Mac application deployment tool in this workflow.

1. Confirm that the target Mac is signed in to the same Apple Account used for
   the user's App Store purchases. Never enter the account password, approve
   two-factor authentication, or accept a purchase on the user's behalf.
2. Open the catalog's App Store URL, verify that the page offers a Mac build,
   and check the user's Purchased list if the direct page is unavailable. A
   page that lists only iPhone/iPad/Apple TV is not a valid Mac installation
   source, even if the app has the same name.
3. The skill must actively open the catalog's App Store URL for the user,
   one application at a time, inside the native App Store whenever possible.
   Do not send a normal `https://apps.apple.com/...` link to the default
   browser as the first attempt: that commonly opens a web page without
   handing off to App Store. Use this escalation order:

   ```sh
   open -a "App Store" "<app_store_url>"
   open "macappstore://itunes.apple.com/app/id< numeric_app_id >"
   ```

   The second form is a deep-link fallback constructed only from the numeric
   App Store ID already present in the catalog URL. Confirm that the foreground
   window is App Store and that the product title matches before proceeding.
   Only if both native routes fail may the skill open the HTTPS page in a
   browser, and it must record that fallback in `completion_notes`. The user
   must not be asked to search for or open the page manually. Search for the
   exact app if needed, select `Mac Apps`, and report whether the button says
   `Get`, `Download`, `Redownload`, `Update`, or `Open`. Stop immediately
   before any `Get`/`Download`/`Redownload` action and ask for confirmation.
   After the user confirms, the skill may click that button, but the user must
   complete any Apple Account password, Touch ID, purchase, or two-factor
   prompt. App Store installation must not be automated with Apple
   Configurator, undocumented store APIs, or credential entry.
4. After installation, open the app and confirm its first window. Re-run
   `scan` and verify the App Store evidence: the traditional
   `Contents/_MASReceipt/receipt`, or for some Mac Catalyst/wrapper packages
   `Wrapper/iTunesMetadata.plist`. Record version and any sign-in, license,
   notification, microphone, camera, VPN, or accessibility follow-up tasks.
   If replacing a direct-download copy with an App Store copy, do not assume
   that its login session will migrate: signing, sandbox containers, and
   Keychain access groups can differ even when the Bundle ID is identical.
   Have the user sign in to the new copy and verify the required workspace
   before retiring the old bundle.
5. If the App Store page is unavailable, not Mac-compatible, region-restricted,
   or the app is absent from Purchased, mark the item as `store_unavailable`
   in the plan and offer the catalog's official website or Web App only when
   that alternative is explicitly recorded. Do not silently substitute a
   website download for an App Store-required entry.

Apple Configurator may remain in the catalog for iPhone, iPad, and Apple TV
backup, restore, supervision, and preparation. It must not be used as the
normal way to install Mac apps or to bypass Apple Account authorization.

5. Open each just-installed GUI app and confirm that it reaches its first window without a crash or macOS security warning. Then complete the plan's `follow_up` tasks and re-run `scan`. Add completed account, license, permission, or configuration notes to the plan's `completion_notes`; never store passwords, API keys, recovery codes, or license secrets.

   When a catalog entry has `preferred_account`, prompt the user to verify that
   account in the app before proceeding. For example, ChatGPT should use
   `xxvk@outlook.com` and Claude should use the Google account
   `example.user@example.invalid`; never automate account selection or login. Open the
   app's account/avatar menu and read the displayed email, then record only
   `account_verified: true/false` and the verification date. If the displayed
   account differs, stop and ask the user whether to switch accounts; never
   click Log out, change accounts, or enter credentials automatically.

   When an entry has `minimum_version`, treat it as a lower bound for every
   future install. The planner reports an installed app below that bound in
   `version_issues`; do not downgrade an app or silently replace it.

   Installation logs record download bytes and installed bytes separately for each Homebrew item. A cached or resumed download may report the final artifact size rather than bytes transferred during the current attempt.

   For Ghostty, after the app is installed, create or update `~/.config/ghostty/config` with the skill defaults below, preserving unrelated user settings:

   ```ini
   theme = Cyberpunk Scarlet Protocol
   font-family = JetBrains Mono
   font-size = 20
   ```

   Treat this as a post-install configuration step, not part of the Homebrew installation. Verify the theme name with `ghostty +list-themes --plain` and open Ghostty once after writing the config.

6. For a first install or a material deployment change, create or update the
   matching `components/<component_id>.md`, add or update its row in
   `components/README.md`, and ensure the catalog entry has the relative
   `guide` path. Material changes include a changed delivery source, changed
   installation or verification procedure, new permission/configuration
   requirement, changed account/license workflow, or changed lifecycle status.
   Routine reinstalls, upgrades, and repeated scans should write evidence to
   `state/` records without rewriting the guide merely to refresh a version,
   timestamp, formatting, or unchanged measurement. For every uninstall or
   removal, update that guide's reusable `lifecycle_status: retired`, document
   what was removed and what data was preserved, and keep machine-specific
   evidence in the ignored `state/` record.
   A component operation is complete when catalog, guide, and state evidence
   are synchronized at the appropriate level of change.

   **Effective SmartDNS requirement:** SmartDNS is opt-in, not the default DNS
   path. Keep the Homebrew service stopped after installation and configure the
   active macOS network service with resilient public DNS (`1.1.1.1` and
   `8.8.8.8`) by default. Only after explicit user approval for China-network
   access may the skill start SmartDNS and switch DNS to its local listeners
   (`127.0.0.1` and `::1` when both are bound). Flush the macOS resolver cache,
   verify `scutil --dns`, and run a real `dig` query after either switch. Record
   the previous DNS servers, changed service, listener addresses, service
   status, and rollback command in the ignored `state/` record. If SmartDNS or
   its local listener is unavailable, automatically restore the public DNS
   pair and stop the service; never leave macOS pointed at an unavailable
   `127.0.0.1` resolver across reboot.

   **Shell environment requirement:** When a component needs `PATH`,
   `JAVA_HOME`, `ANDROID_HOME`, `ANDROID_SDK_ROOT`, or a manager initializer,
   installation is incomplete until the environment is configured in the
   user's active shell startup file. Detect the active shell and prefer
   `~/.zshrc` for zsh or `~/.bashrc`/`~/.bash_profile` for bash. Preserve
   unrelated content, create a timestamped backup before editing an existing
   file, and add an idempotent clearly labelled block only when the lines are
   absent. Start a fresh login shell, verify `command -v` plus version output,
   and write the exact file, variables, and verification results to `state/`.
   Never overwrite shell files, duplicate initialization blocks, or place
   credentials in them. PATH changes that point into a vendor app bundle or
   `/usr/local/bin` still require separate explicit confirmation.

   Every Core installation must record delivery and storage measurements in the
   ignored `state/` install record: `download_bytes` (actual bytes transferred),
   `installed_bytes` (measured footprint), `installed_version`, and
   `installed_at`. The catalog's `size_gb` remains an estimate used for
   planning and must never be presented as the measured footprint. Component
   Markdown contains no current-machine installation measurements. Audit the
   complete Core set with:

   ```sh
   python3 scripts/audit_core_catalog.py
   ```

   Estimate download size in this order: (a) a cached Homebrew artifact or
   vendor-provided installer size, (b) the Mac App Store listing size for a
   verified Mac build, (c) a vendor download page/API, and only then (d) the
   catalog `size_gb` planning estimate. Label the method and timestamp; never
   present an estimate as transferred bytes. After first installation or a
   material packaging change, measure the actual bundle or Homebrew prefix with
   `du` and record it in the dated state installation log. Do not rewrite an
   unchanged guide on every routine upgrade; preserve detailed version and byte
   evidence only in the state installation log.

## Documentation churn policy

The skill is deployment-oriented, not a live changelog generator. Before
editing a component Markdown file, confirm that the source, procedure,
verification, permissions, configuration, lifecycle status, or operating
knowledge changed. If not, leave the Markdown file untouched and record only
the operation in `state/`. Do not run enrichment or normalization scripts as a
routine post-install step when they would rewrite unchanged guides.

## Component frontmatter integrity

Every generated or catalog-linked `components/*.md` file must contain the
complete frontmatter contract from `templates/app-component.md`, including
`component_id`, `name`, `category`, `tier`, `lifecycle_status`, `source`,
`delivery_method`, source identifiers, account/permission fields, and
`secrets_policy`. Missing values must be explicit `null`, `[]`, or `false`; never
omit a template field and never use a placeholder such as `X`.

Machine-specific observations do not belong in component Markdown: do not
persist `status: installed`, installed version/size/timestamps, or verification
results there. Write those observations to ignored `state/` scan, plan, and
install records. `lifecycle_status` describes the reusable catalog lifecycle,
not whether this Mac currently has the component installed.

After creating or materially rewriting guides, run:

```sh
python3 scripts/audit_component_frontmatter.py
```

The audit must pass for every catalog-linked guide and every other Markdown
file under `components/` except `README.md`. A failed audit blocks the
workflow until the frontmatter is repaired. Routine scans and upgrades must
not rewrite frontmatter or body text.

## GUI app and CLI workflow

Treat a graphical app and its command-line tool as separate deliverables. A
Mac App Store install does not automatically guarantee that a CLI is available
on `PATH`, and a Homebrew cask's app bundle must not be treated as a formula.
For every catalog entry that declares a CLI, the post-install check must:

1. Run the declared `check_command` (for example `code --version` or
   `cursor --version`) and record the resolved path with `command -v`.
2. Prefer the vendor's documented CLI installation or the catalog's explicit
   Homebrew formula. Do not create arbitrary symlinks from inside an app bundle.
3. If a documented app-provided CLI needs linking, show the exact source and
   destination and ask for confirmation before changing `PATH`, `/usr/local`,
   `/opt/homebrew/bin`, or shell startup files.
4. Record `cli_status`, `cli_path`, and `cli_version` in the component guide;
   never mark the GUI install incomplete merely because an optional CLI does
   not exist.

For App Store apps without a documented CLI, record `cli_status: not_provided`.
For GUI apps with a separate Homebrew formula, install and verify that formula
independently. This rule applies globally, not only to MQTT Explorer.

An App Store GUI and a Homebrew CLI are separate catalog capabilities. If a
vendor provides both, add `cli_command`, `cli_formula`, and
`cli_link_policy: separate_formula` to the GUI entry, then install/verify the
formula independently. Only create a PATH/symlink link when the vendor or
formula documents the target; never infer one from an App Store bundle. Record
the CLI path/version in the same component guide. A GUI App Store receipt alone
does not prove that a CLI exists.

## Duplicate bundle cleanup

If multiple `.app` bundles map to the same catalog entry or Bundle ID, keep the
copy that matches the catalog's preferred source. Mark the other copy as
`retirement_pending`; do not delete it automatically. First open and verify the
preferred copy, complete any required login or license activation, and confirm
that needed data is available. Only after explicit user confirmation may the
skill move the old `.app` to Trash or remove it. Preserve shared Application
Support, Container, and Group Container data unless the user separately asks
for data cleanup. Record both paths, versions, source evidence, and the final
single-copy result in the component guide.

## Complete removal and embedded helper cleanup

When the user explicitly requests an app's complete removal, deleting only the
top-level `.app` is not sufficient. Search `/Applications`, `~/Applications`,
Application Support, Caches, Preferences, Containers, Saved Application State,
LaunchAgents, and Homebrew cask records for the app name, bundle identifier,
and known aliases. Inspect nested `.app` bundles inside another host
application; a helper can remain launchable after a top-level alias is gone.

For a nested helper, identify its bundle identifier and host app before
deletion. Explain any host-app impact and obtain explicit confirmation before
removing a helper embedded in another application. If confirmed, remove the
host app too when the user names the host (as with Cici), or otherwise remove
only the helper and its clearly matching support data. Never delete unrelated
shared data merely because it contains a similar word.

The removal sequence is:

1. Quit matching applications and helpers.
2. Remove application bundles, nested helpers, matching Homebrew casks, and
   only app-specific support, cache, preference, container, and recent-document
   records.
3. Verify absence with filesystem checks, `brew list --cask`, and a fresh app
   scan. A stale Launch Services or Recent Documents entry is not an installed
   app; clear it only when explicitly tied to the removed bundle.
4. Write measured removed paths, byte counts, preserved data, and verification
   results to an ignored `state/remove-*.json` record. Do not put current
   machine paths or measurements in reusable component Markdown.
5. For catalog components, set the guide and catalog `lifecycle_status` to
   `retired` and document what was removed and what data was preserved. For an
   unlisted nested helper, keep the reusable procedure here and record
   machine-specific evidence only in `state/`.

If administrator authorization is required, use a visible Terminal so the
user can enter the password. Never pass or store the password in the skill.

## Browser download preflight

Use this only when an app needs an official website download or browser-managed download; it is not required for Homebrew or App Store items.

1. Check that Google Chrome is installed.
2. Use the `control-chrome` skill to connect to the Chrome Codex extension and read its browser documentation. A successful selection of the `extension` browser is the pass condition.
3. Record the result in the current plan's `completion_notes` as `Chrome Codex extension: verified YYYY-MM-DD` or `Chrome Codex extension: unavailable`. Do not claim that a failed connection is a macOS privacy-permission failure; it may be an extension state, browser-profile, or Codex connection issue.
4. If unavailable, ask the user to open/enable the Codex Chrome extension and retry. Do not use another browser to bypass this check when the user specifically requests Chrome control.
5. Before clicking a download button, verify the vendor domain and visible file details. Ask for confirmation immediately before any browser action that initiates a software download or install. Record the final vendor URL and downloaded version in `completion_notes`.

## Chrome multi-profile workflow

Chrome profiles are separate Google sessions. Use the read-only inventory script
to discover local profiles and the account email exposed by Chrome's Local
State. It never reads cookies, passwords, tokens, or Keychain data:

```sh
python3 scripts/chrome_profiles.py \
  --expected config/chrome-profiles.json \
  --output state/chrome-profiles-inventory.json
```

The `display_name` in `config/chrome-profiles.json` is the canonical naming
registry, matched to each account by `account_email`. The current naming policy
is:

- `example.user@example.invalid`: `Example Profile 12`
- `example.user@example.invalid`: `Example Profile 9`
- `example.user@example.invalid`: `Example Profile 3`
- `example.user@example.invalid`: `UDI Dev robot`
- `example.user@example.invalid`: `GS Dev robot`

Chrome does not expose a supported command-line operation for changing a
profile's display name. For a new-Mac deployment, the skill may normalize names
through the local `Local State` file only under this controlled sequence:

1. Confirm Chrome is fully quit; do not edit while Chrome is running.
2. Read the file and match profiles by `account_email`, never by
   `profile_directory` alone.
3. Create a timestamped backup beside the file before editing.
4. Change only the matched profile's `display_name` field. Do not change
   account emails, profile directories, cookies, passwords, tokens, or other
   Chrome settings.
5. Re-run `chrome_profiles.py --expected ...` and require zero
   `name_mismatches`; preserve any directory mismatches as informational.
6. Only after verification may Chrome be launched again. If the file cannot be
   parsed or the backup fails, stop without editing.

This controlled file-edit workflow is the approved automation path for profile
name normalization; the UI remains the fallback when Chrome is running or the
file structure is not recognized.

For a new Mac, treat `config/chrome-profiles.json` as the synced desired
seven-profile registry. Compare it with a fresh `state/chrome-profiles-inventory.json`
using `account_email` as the primary identity key. Treat `profile_directory` as
a local implementation detail, not identity. Report missing or extra email
accounts, directory changes, and display-name mismatches separately. If an
email matches but its directory differs, do not call it a missing account.
When an email matches, propose normalizing the Chrome display name to the
expected name; never silently rename a profile and never use a directory name
alone to map accounts. Restore genuinely missing emails one at a time by
creating/opening a new Chrome profile, then let the user complete Google sign-in,
Passkey selection, and Touch ID/other second-factor prompts:

```sh
open -na "/Applications/Google Chrome.app" --args --profile-directory="Profile 1"
```

Do not silently delete or rename an existing profile. If fewer than seven
profiles exist, create only the missing profile through Chrome's `Add profile`
flow, then verify the expected email before marking it complete. If the email
differs, stop and ask the user; never log out or switch accounts automatically.
Maintain `account_verified` and `verified_at` in the local inventory or a
separate private deployment note; do not overwrite the synced expected account
mapping with machine-specific paths. The
skill may automate opening windows and checking the visible profile name or
avatar, but must never enter credentials, select a Passkey, approve Touch ID,
or bypass 2FA. Never store passwords, tokens, recovery codes, or Passkey data.

## GitHub CLI preflight

Use this when the workflow needs a private GitHub repository, a Git submodule, or a GitHub CLI action.

1. Check that `gh` is installed with `command -v gh` and `gh --version`. Install it from the catalog/Homebrew formula if missing.
2. Run `gh auth status` before any private-repository command. Treat a listed active account and `repo` scope as the pass condition.
3. If a sandboxed `gh auth status` reports an invalid token, repeat the same read-only check with access to the system keychain before treating the login as invalid. If authentication is still absent or invalid, ask the user to complete the interactive `gh auth login` flow. Do not automate browser sign-in, paste tokens, or store tokens in the catalog, plans, or logs.
4. After the user reports completion, run `gh auth status` again. Only then use an HTTPS private repository URL with `git`, including `git submodule add`.

## Docker Desktop retirement

For every developer Mac, ensure OrbStack is installed and verified as the default local container backend. Check for Docker Desktop during the same scan. If `/Applications/Docker.app` exists, offer a separate cleanup; never perform that cleanup implicitly as part of an app installation.

1. Preview only:

   ```sh
   python3 scripts/docker_desktop_cleanup.py inspect
   ```

   Review the reported Docker Desktop application, Docker disk image, container/image/volume storage, settings, logs, and reclaimable size. The cleanup targets only Docker Desktop-owned locations; it deliberately preserves `~/.docker` and every OrbStack location/context.

2. If OrbStack is absent, offer it as the default lightweight local container backend, including on a new Mac with no Docker Desktop. Install and open OrbStack first, then verify it. Do not run Docker Desktop and OrbStack as concurrent default Docker backends.

   Verification requires all of: `/Applications/OrbStack.app` exists, `orbctl status` is `Running`, `docker` is on PATH, `docker context show` is `orbstack`, and `docker version` returns a server version. `command -v docker` alone is insufficient because it identifies only the CLI binary, not its active backend. The inspection script reports all five checks.

   If the Docker CLI is absent, offer to add `~/.orbstack/bin` to the user's shell PATH and start a new shell, then re-run `inspect`. Do not use `orbctl doctor --fix` or create the optional `/usr/local/bin/docker` JetBrains compatibility symlink without explicit confirmation because they modify the local environment.

3. State the irreversible effect plainly: the Docker Desktop app and **all Docker Desktop-local** containers, images (including user-built images), volumes, build cache, Kubernetes data, and settings will be permanently removed. Volume data may contain databases or other persistent data. It does not delete remote registry images or OrbStack data.

4. Ask the user whether to proceed. On explicit confirmation, run the official Docker Desktop uninstaller followed by the narrowly scoped residual cleanup:

   ```sh
   python3 scripts/docker_desktop_cleanup.py remove --confirm "REMOVE DOCKER DESKTOP DATA"
   ```

5. Verify with another `inspect` call and record reclaimed space plus the Docker documentation source in the plan. If the official uninstaller fails, stop and report the error; do not manually delete arbitrary Docker CLI configuration or unknown paths.

Docker states that its Mac containers and images reside in a large disk image and documents inspecting their usage with `docker system df -v`. See https://docs.docker.com/desktop/troubleshoot-and-support/faqs/macfaqs/.

## Catalog maintenance

- Edit `references/app-catalog.json` when adding, removing, or recategorizing apps. Keep the official download URL, delivery method, capacity tier, estimated size, and post-install tasks current.
- Keep every catalog entry linked to a component guide. To scaffold missing non-Core guides without installing anything, run `python3 scripts/generate_optional_guides.py`; review the generated source and size estimate before using it.
- Use `brew` only for a cask or formula whose identifier is present in `brew_cask` or `brew_formula`. If a package fails validation, leave it in the plan as a manual task and update the catalog after checking the vendor source.
- Use `check_command` for CLI tools so a binary already on `PATH` is correctly considered installed. Record ordered dependencies with `install_after`; for example, install `mole` after Ghostty so the user can run and review its terminal UI.
- Use `app_store_url` for App Store software. App Store sign-in and installation remain user actions.
- For macOS App Store installation, store `app_store_url` as a direct
  `macappstore://itunes.apple.com/app/id<APP_ID>` URL so the workflow opens the
  App Store application rather than a browser. Keep an HTTPS App Store URL
  only when it is a reference page for a non-Mac target, such as a PlayCover
  IPA source; never treat that URL as the installation path.
- Source policy is explicit: `app_store_url` means `app_store`, `brew_cask` or
  `brew_formula` means `homebrew`, `official_url` alone means `official_web`,
  and `system_app: true` means `system`. Keep source mismatches visible in plans;
  do not silently accept a website download for an App Store-required app.
- Prefer vendor URLs for apps without a verified cask. Add scripted direct downloads only when the vendor provides a stable, HTTPS URL and an integrity check; otherwise keep them manual.
- Browser extensions require target-specific checks. Use the extension ID for
  Chrome profile detection and an App Store bundle/path check for Safari
  extensions; do not classify a browser extension as missing merely because it
  has no top-level `.app` in `/Applications`.

## Persistent records

`state/` is created beside the skill on first run and is ignored machine-local
state. It holds dated scans, plans, installation logs, current versions,
permissions, paths, and cleanup measurements. Do not sync it through Git or
use it as reusable catalog configuration. Persistent policies and desired
configuration belong in tracked `settings/`, `references/`, or component
guides.

For explicit macOS local-account retirement, read
[references/account-removal.md](references/account-removal.md). It covers the
preflight, visible-Terminal authorization, `sysadminctl` deletion, and
post-delete verification. Keep account names and machine-specific results in
ignored `state/` records only.

Detailed per-component instructions live in `components/README.md` and the linked Markdown guides. Keep the catalog as the install metadata source of truth, and link each detailed guide from its catalog entry with a relative `guide` path.

## Safety rules

- Treat Homebrew bootstrap, downloads, and `--apply` as external changes requiring explicit user approval.
- Never use the catalog to automate login, license entry, security/privacy permissions, device-management enrollment, or VPN connection.
- Before installing a `heavy` app on a portable profile, state the space impact and obtain an explicit override.
- Never run `git commit` in this repository or its submodule on your own initiative, no matter how small or reversible the change looks. Edit and stage files as needed, then stop and report what changed; the user runs every commit themselves. This applies identically to this skill's own repository and to the parent repository that carries it as a submodule — a submodule-pointer bump is still a commit. Only commit when the user explicitly says to (e.g. "commit this", "提交").
