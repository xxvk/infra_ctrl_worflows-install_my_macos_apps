# macomrade

**Safety-first, reproducible macOS setup and lifecycle automation for apps, permissions, preferences, and machine drift.**

Current target version: **0.2.0** (`release_candidate`)

`macomrade` is a personal Codex Skill and repository-local Python CLI for making a new Mac ready to use from a reviewable configuration. It keeps reusable policy in Git while protecting secrets, private overlays, and machine-local observations.

## What it does

- Inventories installed apps and their available installation-source evidence.
- Builds reviewable app plans for portable or expanded Mac storage profiles.
- Defines reusable permission and preference policy without copying protected grants or credentials.
- Detects configuration drift and records machine-local verification evidence.
- Routes scan, plan, apply, verify, drift, diagnostics, and migration workflows through one CLI.

## Quick Start

Evaluate the public workflow without Homebrew, an Apple ID, administrator access, protected macOS permissions, or application changes:

```sh
git clone https://github.com/xxvk/macomrade.git
cd macomrade
export MACOMRADE_PUBLIC_ONLY=1
export INSTALL_MY_MACOS_APPS_STATE_DIR=/tmp/macomrade-public-quickstart

./bin/macomrade validate
./bin/macomrade scan apps
./bin/macomrade plan apps --profile auto
```

Read the [public onboarding guide](references/public-onboarding.md) for prerequisites, output review, limitations, private-overlay setup, and rollback guidance. The plan is advice, not authorization; `macomrade` never adds an apply flag on the user's behalf.

## Release status

Current target version: **0.1.0** (`release_candidate`). The source repository is public, but no stable tag, GitHub Release, packaged global CLI, or completed genuine Clean-Mac acceptance run is implied.

`VERSION` is the version source of truth. The cumulative 0.2.0
release-candidate capability baseline, committed 0.3.0–0.9.0 scope, and
1.0 native macOS product vision are defined in
[`references/release-roadmap.md`](references/release-roadmap.md). Product-level
candidates are kept separately in
[`references/product-ideas.md`](references/product-ideas.md).
The cumulative current-version behavior boundary is
[`references/release-acceptance-matrix.json`](references/release-acceptance-matrix.json);
validate it locally with `python3 scripts/validate_release_contract.py`.

The app catalog is only one part of the baseline. Tracked `settings/` define
portable public policy. The local `Private/` overlay is reserved for
user-approved personal configuration, remains synchronized through iCloud
Drive, and is ignored by Git. Sanitized templates live under
[`examples/private/`](examples/private/). Runtime state now lives in machine-local Application Support storage;
the tracked `state/` directory is only a compatibility locator. Privacy
grants, passwords, tokens, private keys, session material, and private document
contents are never copied as configuration; each new Mac must visibly
authorize protected access and then be verified.

See [`references/configuration-layers.md`](references/configuration-layers.md)
for merge precedence, migration rules, and the boundary between local Private
configuration and secrets.
The registered versioned JSON contracts, Draft 2020-12 registry, validation-before-use
boundaries, and non-destructive migration procedure are documented in
[`references/schema-and-migration.md`](references/schema-and-migration.md).
Support diagnostics use an allowlisted, bounded, preview-first ZIP workflow;
see
[`references/redacted-diagnostic-bundle.md`](references/redacted-diagnostic-bundle.md).
Before opening an issue or sharing any artifact, follow the
[`public support and safety contract`](references/public-support-safety.md).

## Usage

The stable 0.2.0 repository-local entry point is `macomrade`:

```sh
./bin/macomrade routes
./bin/macomrade scan apps
./bin/macomrade plan apps --profile auto
./bin/macomrade scan storage --mode quick
./bin/macomrade plan storage --target auto
./bin/macomrade verify schemas
./bin/macomrade verify release
./bin/macomrade diagnostics release-manifest
./bin/macomrade diagnostics public-clone
```

It routes the supported workflow families—scan, review, plan, apply, verify,
history, drift, diagnostics, and migration—to the existing scripts without duplicating
their behavior. `./bin/macomrade --explain ...` prints the exact compatibility
command without executing it. The dispatcher never adds `--apply`, so the
underlying dry-run, confirmation, verification, and rollback contract remains
authoritative.

The launcher stays repository-local for 0.2.0; no global symlink, Homebrew
formula, npm package, or publication is implied. See
[`references/macomrade-cli.md`](references/macomrade-cli.md) for the complete
route and compatibility contract and
[`references/cli-identity.json`](references/cli-identity.json) for the
point-in-time name-collision audit.

The locally accepted 0.2.0 storage release-candidate implementation is
available through the same launcher. It separates logical, allocated,
estimated, staged, and measured bytes; remembers
reviewed decisions; imports Mole history as evidence only; surfaces bounded
read-only OS/Home/App handoff facts; and requires a frozen plan plus exact
confirmation for every storage mutation. See
[`references/storage-lifecycle.md`](references/storage-lifecycle.md).

All supported mutations are registered in
[`references/mutation-contracts.json`](references/mutation-contracts.json) and
validated through the shared
[`mutation transaction contract`](references/mutation-transaction-contract.md).
Tracked component guides are protected by the
[`component documentation state boundary`](references/component-state-boundary.md);
detected versions, paths, timestamps, measurements, grants, and completion
results stay in machine-local state.

`SKILL.md` is the concise execution and safety entry point. Detailed procedures
are split into six directly linked domain references and loaded only when the
current task needs them. `python3 scripts/validate_skill_structure.py` enforces
the entry-point size limit, required routes, preserved domain sections, and
local-link integrity.

## Requirements

- macOS
- Python 3 (the scripts use the standard library only)
- Homebrew for automatic Homebrew cask/formula installs
- Codex Chrome extension only when managing an official website download in Chrome

## Governance

This project is licensed under [Apache License 2.0](LICENSE). Before
contributing or reporting a problem, read the
[contribution guide](CONTRIBUTING.md), [security policy](SECURITY.md), and
[code of conduct](CODE_OF_CONDUCT.md). Release-facing changes are summarized
in the [changelog](CHANGELOG.md); bundled third-party material and notice
requirements are tracked in [third-party notices](THIRD_PARTY_NOTICES.md).

The presence of an open-source license and public repository does not imply
that the 0.2.0 release candidate has been tagged, packaged, or declared stable.

## Local validation policy

The 0.2.0 release candidate uses local macOS validation, not GitHub Actions, as
its default quality gate:

```sh
python3 scripts/icloud_git_guard.py inspect --repo .
python3 scripts/schema_contract.py validate-tracked
python3 scripts/release_check.py
```

The release check is hermetic by default and uses fixture responses for
Homebrew, App Store receipts, TCC, defaults, filesystem state, formal JSON
contracts/migrations, and macomrade route validation. Run
`python3 scripts/release_check.py --include-live-smoke` only when the current
Mac integration check is needed.

`tests/smoke.sh` validates the catalog and Python scripts, lints LaunchAgent
templates, and exercises read-only or dry-run paths against the current Mac.
It never authorizes an install, changes TCC permissions, or replaces a genuine
clean-Mac acceptance run. The previous automatically triggered
`macos-latest` workflow was removed because an ephemeral GitHub runner cannot
represent this repository's real application, account, hardware, permission,
Dock, or system-preference state and adds private-repository runner cost
without becoming release evidence.

Do not add a push, pull-request, or scheduled GitHub Actions workflow for this
skill unless the user explicitly changes this policy. See
[`references/testing-contract.md`](references/testing-contract.md) for the
hermetic/live boundary and required negative contracts.

## iCloud-backed Git preflight

This repository intentionally remains in iCloud Drive. Before `git status`,
`git diff`, `git fsck`, commit preparation, submodule operations, or other
Git-dependent work, run:

```sh
python3 scripts/icloud_git_guard.py inspect --repo .
```

The command understands this skill's submodule `.git` pointer and stops before
Git opens an evicted object. If materialization is required, use the plan-first
workflow in
[`references/icloud-git-integrity.md`](references/icloud-git-integrity.md).
Never interpret `dataless` as deletion or corruption, never repair Git before
materialization, and never relocate the repository as a workaround.

## Keyboard configuration entry

Keyboard settings are managed from the local, Git-ignored
`Private/keyboard.yaml`. The historical `settings/keyboard.yaml` path is a
compatibility locator. Start from the public
[`keyboard overlay example`](examples/private/keyboard.yaml) and
[`device profile example`](examples/private/keyboards/example-keyboard.yaml).
The active device-specific profile remains under `Private/keyboards/` and is
never required by a public clone.

The current Logitech K240 Japanese-keyboard policy is:

| Key | Action |
| --- | --- |
| F1 | Open ChatGPT.app |
| F2 | Open Claude.app |
| F3 | Open Perplexity.app |
| F4 | Mission Control |
| F5 | Open YouTube.app (including PlayCover); otherwise Apple Music |
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
   restart or receiver reconnect. The portable mapping command is:

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

3. F1–F3, F5, and F12 are handled by the native listener source at
   [`scripts/keyboard-config-logi-k240.swift`](scripts/keyboard-config-logi-k240.swift). It matches
   the Logitech receiver and the relevant HID usages (`usage page 0x07`): F1
   `0x3a`, F2 `0x3b`, F3 `0x3c`, F5 `0x3e`, and F12 `0x45`. It opens
   ChatGPT.app, Claude.app, Perplexity.app, YouTube.app when present (including
   `~/Applications/PlayCover/YouTube.app`; otherwise Apple Music), or
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
   confirm that YouTube opens when installed, otherwise Apple Music opens. Test left Command twice in a text field to
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

The installed user-level locations are:

```text
Binary:       ~/Library/Application Support/install_my_macos_apps/bin/keyboard-config-logi-k240
LaunchAgent:  ~/Library/LaunchAgents/com.xvk.install-my-macos-apps.keyboard-config-logi-k240.plist
Logs:         ~/Library/Logs/install_my_macos_apps/keyboard-config-logi-k240.log
```

The `~/Library` directory is hidden in Finder. Locate the binary with:

```sh
open -R "$HOME/Library/Application Support/install_my_macos_apps/bin/keyboard-config-logi-k240"
```

Input Monitoring is protected by macOS TCC. CLI can open the settings page but
cannot silently grant this permission; `tccutil` can reset it but cannot
authorize a new executable. Replacing or recompiling the binary may require
authorization again. Every time the binary is replaced, the skill must
automatically locate the new binary and open both Finder and the Input
Monitoring page before asking the user to enable it:

```sh
open -R "$HOME/Library/Application Support/install_my_macos_apps/bin/keyboard-config-logi-k240"
open 'x-apple.systempreferences:com.apple.settings.PrivacySecurity.extension?Privacy_ListenEvent'
```

After authorization, reload the agent with:

```sh
launchctl bootstrap gui/$(id -u) \
  "$HOME/Library/LaunchAgents/com.xvk.install-my-macos-apps.keyboard-config-logi-k240.plist"
```

F4 is intentionally excluded from the listener. Its Mission Control binding
is a native macOS shortcut (symbolic hotkey ID 32). F5 checks standard
`/Applications/YouTube.app`, then the PlayCover executable
`~/Applications/PlayCover/YouTube.app/YouTube`, and falls back to
`/System/Applications/Music.app`. PlayCover's flat bundle must be launched
through its inner executable, not with `open -a`. If the PlayCover YouTube
process is already running, the listener activates the existing instance
instead of starting another process. When that instance was minimized with the
yellow button, the listener also clears the window's minimized state before
activating it. This restoration uses macOS Accessibility window attributes;
grant the installed listener Accessibility permission if activation works but
the minimized window does not return.

The current PlayCover YouTube profile does not provide reliable login-session
persistence: PlayTools must remain removed for startup compatibility, and
enabling PlayChain did not preserve the tested YouTube login across a full quit
and relaunch. The documented operating rule is therefore to log in again when
YouTube is reopened. This is a known compatibility limitation, not an F5 or
LaunchAgent failure.

The `defaults` entries for system shortcut IDs are not the authoritative
implementation for K240. They can be written successfully while having no
effect on an external keyboard, so the HID listener is the supported F1–F3,
F5, and F12 path. F4 is a native macOS shortcut and should not be duplicated
in the listener. Dictation remains a separate system shortcut: verify left
Command twice rather than treating F5 as a Dictation key.

These keyboard settings are machine-local. They are not treated as iCloud
synced configuration. Durable policy belongs in `settings/`; current device
facts and test logs belong in the resolved machine-local state directory or
the local log directory.

### Logitech K240/M212 battery status

The K240 keyboard and M212 mouse share the Logitech receiver `046d:c534`.
macOS's native HID and power commands do not expose their battery values.
Logi Options+ and OpenLogi may not recognize this legacy pairing. Solaar is the
optional next test; its macOS support is limited and its device-reported battery
values must be confirmed from each selected device's details pane. See
[`components/solaar.md`](components/solaar.md) for the GitHub-based installation
flow. Keep current readings in machine-local state, not in this durable README.

### Audit and selectively disable startup items

To see what macOS starts at login, including apps and helper components:

```sh
python3 scripts/macos_startup_items.py scan
```

For an interactive numbered selection:

```sh
python3 scripts/macos_startup_items.py review
```

The review flow asks for an explicit `DISABLE` confirmation. It only removes
selected user Login Items or disables user LaunchAgents. It preserves the
application and its data; system components and Background Task Management
records are reported for review rather than deleted automatically.

## Start safely

Run every command from this directory. These commands only inspect the Mac and
write records under the directory returned by
`python3 scripts/state_paths.py path`:

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

Before applying an installation, validate
[`references/source-policy.md`](references/source-policy.md):

```sh
python3 scripts/supply_chain.py validate
python3 scripts/supply_chain.py inspect
```

The installer refuses mutable network-to-shell Homebrew bootstrap, unpinned npm
globals, and third-party tap drift. Decrypted IPA sources require separate
Private approval and per-file verification.

The 0.1.0 Clean-Mac harness is ready, but its real hardware run remains
`blocked_external`. Validate the harness on any Mac; initialize a session only
on unused or newly purchased hardware:

```sh
python3 scripts/clean_mac_acceptance.py validate
python3 scripts/clean_mac_acceptance.py status
```

See
[`references/clean-mac-release-acceptance.md`](references/clean-mac-release-acceptance.md)
for the 13-gate workflow. Previously configured Macs cannot satisfy CM-01.

`portable` applies below 512 GB; `expanded` applies at 512 GB or more. Review the generated plan before choosing one or two apps to install.

```sh
STATE_DIR="$(python3 scripts/state_paths.py path)"
python3 scripts/macos_apps.py install "$STATE_DIR/PLAN.json" --only "App Name"
python3 scripts/macos_apps.py install "$STATE_DIR/PLAN.json" --only "App Name" --apply
```

The first command is a dry run. `--apply` makes external changes and must be used only after explicit review. GUI apps must be opened and checked after installation.

Approved Homebrew CLI recommendations may be installed in batches of up to five. GUI apps and App Store/website installs remain one at a time so each can be opened, authenticated, and verified separately.

Merged catalog entries may include a `minimum_version` and a
`preferred_account` from `Private/app-catalog-overlay.json`. The plan reports
versions below the recorded floor as `version_issues`; account values are
prompts only and never include passwords, tokens, or recovery codes.

GUI installation and CLI installation are tracked separately. When a GUI app
has a CLI, the skill verifies `command -v` and the declared version, and only
creates a documented link after explicit confirmation. It never guesses a
symlink from an app bundle.

Every Core component guide keeps only planning estimates and reusable
installation know-how; `size_gb` in the catalog is only a planning estimate.
Measured `download_bytes` and `installed_bytes` belong in machine-local install
records. Run `python3 scripts/audit_core_catalog.py` and
`python3 scripts/audit_component_frontmatter.py` to find missing guides,
metadata, or state-boundary violations.

LM Studio Bionic is the desired Core application. Classic LM Studio
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

Runtime records are stored under
`~/Library/Application Support/install-macos-apps/state/<hashed-machine-id>/`.
Resolve the exact path with `python3 scripts/state_paths.py path`. The tracked
`state/README.md` and `state/locator.json` contain no machine observations.
See
[`references/machine-local-state.md`](references/machine-local-state.md) for
override, migration, verification, and source-cleanup rules.

The expected Chrome Profile mapping belongs in the Git-ignored local
`Private/chrome-profiles.json`, initialized from the fictional
[`public Chrome profile example`](examples/private/chrome-profiles.json). A new
Mac can compare its local inventory with the user-approved account mapping
without publishing those identifiers. Never add passwords, tokens, recovery
codes, or Passkey data.
The historical `config/chrome-profiles.json` path is a compatibility locator
and remains accepted by `scripts/chrome_profiles.py`.

See [SKILL.md](SKILL.md) for the complete Codex workflow and safety rules.
