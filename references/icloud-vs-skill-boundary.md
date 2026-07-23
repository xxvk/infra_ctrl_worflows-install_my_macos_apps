# iCloud vs. this skill: who handles what

Documentation only. States the boundary explicitly so effort isn't
duplicated: some things already sync automatically via iCloud/the Apple
Account, and this skill should not re-implement them; other things
categorically do not sync via iCloud and are exactly what this skill exists
to handle.

## Already handled by iCloud (do not duplicate here)

- **Photos, Notes, Reminders, Calendar, Contacts** — sync via iCloud when
  enabled for the signed-in Apple Account. No script in this skill touches
  these.
- **Safari bookmarks, history, and tabs** — sync via iCloud Safari sync.
  (Chrome bookmarks are a separate, non-Apple sync boundary — see the
  "Not handled" section below.)
- **iCloud Keychain (passwords/passkeys)** — this is the authoritative
  secrets manager declared in
  [`settings/manual-actions.yaml`](../settings/manual-actions.yaml)
  (`secrets_manager.authoritative_source: system_keychain`); its sync is
  Apple's, not this skill's.
- **This repository itself** — synced via iCloud Drive (the working
  directory lives under `iCloud~md~obsidian/Documents/XVK_PM`), independent
  of the Git remote. Either channel can be used to retrieve it on a new Mac
  (see [disaster-recovery-runbook.md](disaster-recovery-runbook.md) Step 1).
- **iCloud Drive file contents in general** — any file actually stored
  under `~/Library/Mobile Documents/` syncs on its own; this skill's file
  scans (e.g. `developer_environment_profile`) only record shape/hashes,
  never re-upload or re-sync file contents.
- **Apple Account-level settings** (Family Sharing, Find My, Apple Pay
  device enrollment) — entirely out of scope; these are Apple Account
  settings, not per-Mac system preferences.

## Not handled by iCloud — this skill's actual scope

- **Installed applications and their sources** (Homebrew, App Store, direct
  download) — `references/app-catalog.json` + `scripts/macos_apps.py`.
- **App-specific/local preferences not tied to an Apple framework** — Dock
  order, keyboard/HID mappings, Finder view settings, screenshot location,
  notification authorization, Focus database *presence* — all in
  `scripts/macos_preferences.py` / `settings/system-preferences.yaml`.
  These are `defaults`-domain or LaunchServices state, which iCloud does
  not sync.
- **TCC/privacy permission grants** — always device-local by macOS design;
  see `scripts/macos_permissions.py` and `settings/privacy.yaml`. iCloud
  never carries these across Macs; each Mac must re-authorize.
- **Chrome profiles, bookmarks, extensions** — Chrome sync is a *Google*
  account boundary, not Apple's iCloud; entirely separate from anything
  Apple-managed. Handled by `scripts/chrome_profiles.py` (profile/account
  matching and extension inventory only; bookmarks themselves are still
  manual, see the CTO backlog item on browser bookmark migration).
- **Homebrew packages, dotfiles, SSH/GPG keys, developer environment shape**
  — `developer_environment_profile`, `dotfiles/`, and
  `references/ssh-gpg-provisioning.md`. None of this is Apple-account
  scoped.
- **Startup items, LaunchAgents, background tasks** —
  `scripts/macos_startup_items.py`. Per-machine launchd state, not synced
  by Apple.
- **Printers, network/Wi-Fi, security posture (Gatekeeper/FileVault/SIP)** —
  machine-local by definition; see `scripts/macos_printers.py`,
  `network_profile`, and `security_profile` in
  `scripts/macos_preferences.py`.
- **This skill's own installed footprint** (K240 LaunchAgent, drift-check
  LaunchAgent, its Application Support/Logs directories) —
  `scripts/skill_footprint_inventory.py` / `scripts/skill_uninstall.py`.
  None of this is Apple/iCloud content; it is this skill's own artifacts.

## The one overlap worth calling out explicitly

The repository's *files* sync via iCloud Drive, but the repository's *Git
history* does not — those are two different mechanisms carrying the same
working tree. A merge conflict from concurrent iCloud sync and a local
`git commit` on two Macs is possible and is a Git/iCloud interaction issue,
not automatically resolved by this skill. The repository remains in iCloud.
Before Git-dependent operations, run
[`scripts/icloud_git_guard.py`](../scripts/icloud_git_guard.py) and follow
[`icloud-git-integrity.md`](icloud-git-integrity.md) if File Provider has
evicted Git data. Treat Git as the history source of truth, finish one editing
session before beginning another Mac's session, allow iCloud to settle, and
never interpret a `dataless` object as deletion or corruption.
