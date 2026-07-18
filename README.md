# Install My macOS Apps

A personal Codex Skill for setting up a new Mac from a persistent app catalog. It inventories installed apps, selects a storage profile, creates an installation plan, and records follow-up tasks such as account sign-in and permissions.

## Requirements

- macOS
- Python 3 (the scripts use the standard library only)
- Homebrew for automatic Homebrew cask/formula installs
- Codex Chrome extension only when managing an official website download in Chrome

## Keyboard configuration entry

Keyboard settings are managed from [`settings/keyboard.yaml`](settings/keyboard.yaml).
The device-specific K240 profile is:

[`settings/keyboards/logitech-k240-japanese-dictation.yaml`](settings/keyboards/logitech-k240-japanese-dictation.yaml)

The current Logitech K240 Japanese-keyboard policy is:

| Key | Action |
| --- | --- |
| F1 | Open ChatGPT.app |
| F2 | Open Claude.app |
| F3 | Open Perplexity.app |
| F4 | Mission Control |
| F5 | Open Apple Music |
| F6 | Previous Track |
| F7 | Play/Pause |
| F8 | Next Track |
| F9 | Mute |
| F10 | Volume Down |
| F11 | Volume Up |
| F12 | Open macOS Screenshot.app toolbar |

The K240 is identified from the Logitech USB receiver (`VID 0x046d`,
`PID 0xc534`) plus physical confirmation of the K240 model and Japanese
layout. The receiver ID alone does not uniquely identify the paired keyboard.

### K240 implementation and test flow

1. Verify the receiver and keyboard layout:

   ```sh
   hidutil list
   defaults read -g AppleSelectedInputSources
   ```

2. Apply F6–F11 with native `hidutil` usage mappings. These mappings are
   local to the current macOS session and may need to be reapplied after a
   restart or receiver reconnect.

3. F1–F3, F5, and F12 are handled by the native listener source at
   [`scripts/keyboard-config-logi-k240.swift`](scripts/keyboard-config-logi-k240.swift). It matches
   the Logitech receiver and the relevant HID usages (`usage page 0x07`): F1
   `0x3a`, F2 `0x3b`, F3 `0x3c`, F5 `0x3e`, and F12 `0x45`. It opens
   ChatGPT.app, Claude.app, Perplexity.app, Apple Music, or
   `/System/Applications/Utilities/Screenshot.app` respectively. F4 is
   configured by the native macOS Mission Control shortcut (symbolic hotkey
   ID 32), not by Swift. F12 opens
   full screenshot toolbar, equivalent to `Command-Shift-5`; it does not
   immediately force an area selection.

4. Compile and run the listener in the foreground for a first test:

   ```sh
   swiftc scripts/keyboard-config-logi-k240.swift -o /tmp/keyboard-config-logi-k240
   /tmp/keyboard-config-logi-k240
   ```

   Press F1 and F2 and confirm that ChatGPT and Claude open. Press F4 and
   confirm Mission Control opens through the macOS shortcut. Press F12 and
   confirm that the Screenshot toolbar appears. Press F5 and
   confirm that Apple Music opens. Test left Command twice in a text field to
   confirm that Dictation starts or stops. Stop the
   foreground process after testing. The listener writes diagnostics to
   `~/Library/Logs/install_my_macos_apps/keyboard-config-logi-k240.log`.

5. If a function key is captured in the log but its action does not appear,
   verify that the relevant system app exists. For F3, verify that
   `/Applications/Perplexity.app` exists. For F12, verify that
   `/System/Applications/Utilities/Screenshot.app` exists and that macOS
   allows the Screenshot app to use the required Screen Recording capability.
   If the listener cannot open the receiver, grant the terminal or installed
   listener **Privacy & Security → Input Monitoring** permission and retry.

### Automatic startup

The listener can run automatically after login through the LaunchAgent template
[`templates/keyboard-config-logi-k240.launchagent.plist`](templates/keyboard-config-logi-k240.launchagent.plist).
It is receiver-scoped, not a universal keyboard remapper: another brand or
another receiver will not match the Swift HID filter. The receiver identifier
does not uniquely prove that the paired physical keyboard is K240.

The `defaults` entries for system shortcut IDs are not the authoritative
implementation for K240. They can be written successfully while having no
effect on an external keyboard, so the HID listener is the supported F1–F3,
F5, and F12 path. F4 is a native macOS shortcut and should not be duplicated
in the listener. Dictation remains a separate system shortcut: verify left
Command twice rather than treating F5 as a Dictation key.

These keyboard settings are machine-local. They are not treated as iCloud
synced configuration. Durable policy belongs in `settings/`; current device
facts and test logs belong in ignored `state/` or the local log directory.

## Start safely

Run every command from this directory. These commands only inspect the Mac and write local records under `state/`:

```sh
python3 scripts/macos_apps.py scan
python3 scripts/macos_apps.py plan --profile auto
```

To audit shared application data that may remain after an app is removed, run
the read-only Group Container scan:

```sh
python3 scripts/scan_group_containers.py
python3 scripts/scan_group_containers.py --json
```

The scan reports container size, the metadata creator, whether a matching app
bundle is currently installed, and `likely_orphan`. That flag is only a review
signal: shared containers such as Microsoft Office's
`UBF8T346G9.Office` must not be deleted as a whole. Removal is a separate,
explicit, app-specific operation after reviewing what data is preserved.

To inspect and explicitly remove standalone OpenClaw leftovers:

```sh
python3 scripts/openclaw_cleanup.py inspect
python3 scripts/openclaw_cleanup.py remove --confirm "REMOVE OPENCLAW"
```

This targets only `~/.openclaw` and the known Kimi Desktop OpenClaw shim. It
preserves Hermes source/test files, Kimi Desktop, and unrelated application data.

The scan also records installation-source evidence. It recognizes an App Store
receipt, a matching installed Homebrew cask, or a system bundle; website/DMG/ZIP
installs are reported as `manual_or_unknown`. Review `source_mismatches` in the
plan before reinstalling. For example, Slack and Telegram must have an App Store
receipt; a mismatch only produces a prompt and never deletes the existing app.

`portable` applies below 512 GB; `expanded` applies at 512 GB or more. Review the generated plan before choosing one or two apps to install.

```sh
python3 scripts/macos_apps.py install state/PLAN.json --only "App Name"
python3 scripts/macos_apps.py install state/PLAN.json --only "App Name" --apply
```

The first command is a dry run. `--apply` makes external changes and must be used only after explicit review. GUI apps must be opened and checked after installation.

Approved Homebrew CLI recommendations may be installed in batches of up to five. GUI apps and App Store/website installs remain one at a time so each can be opened, authenticated, and verified separately.

Catalog entries may include a `minimum_version` and `preferred_account`. The
plan reports versions below the recorded floor as `version_issues`; account
values are prompts only and never include passwords, tokens, or recovery codes.

GUI installation and CLI installation are tracked separately. When a GUI app
has a CLI, the skill verifies `command -v` and the declared version, and only
creates a documented link after explicit confirmation. It never guesses a
symlink from an app bundle.

Every Core component guide must record measured `download_bytes` and
`installed_bytes`; `size_gb` in the catalog is only a planning estimate. Run
`python3 scripts/audit_core_catalog.py` to find missing guides, measurements,
or App Store/CLI metadata.

LM Studio Bionic is the active Core application for this Mac. Classic LM Studio
is retired because both applications use the same `llmster` daemon and cannot
run their local backends concurrently. Keep shared `~/.lmstudio` model data
until Bionic has been verified; retirement does not imply deleting that data.

## App Store apps

For entries with an `app_store_url`, sign in to the same Apple Account used on
the other Macs, verify that the listing supports macOS, and install from the
App Store or Purchased list. The user must click Get/Download and handle any
password, two-factor authentication, license, or permission prompts. Afterward,
the skill verifies the App Store receipt during the next scan. Apple Configurator
is reserved for iPhone, iPad, and Apple TV preparation; it is not used to deploy
Mac apps. The skill opens the matching App Store page and pauses immediately
before Get/Download/Redownload so the user can confirm the installation action.

## Docker Desktop retirement

Inspect Docker Desktop before removing it:

```sh
python3 scripts/docker_desktop_cleanup.py inspect
```

Install and verify OrbStack as the default local container backend on every developer Mac, including a new Mac with no Docker Desktop. If Docker Desktop is present, only remove it after OrbStack is verified. Removal permanently deletes Docker Desktop-local containers, images, volumes, build cache, Kubernetes data, and settings. It preserves OrbStack and `~/.docker`.

```sh
python3 scripts/docker_desktop_cleanup.py remove --confirm "REMOVE DOCKER DESKTOP DATA"
```

## Local records

`state/` is intentionally ignored by Git. It contains machine-specific app paths, storage information, and deployment history; keep it locally for continuity but do not commit it.

The expected Chrome Profile mapping is intentionally tracked in
[`config/chrome-profiles.json`](config/chrome-profiles.json), so a new Mac can
compare its local inventory with the seven expected Profile directories and
account emails. It contains account identifiers only; never add passwords,
tokens, recovery codes, or Passkey data.

See [SKILL.md](SKILL.md) for the complete Codex workflow and safety rules.
