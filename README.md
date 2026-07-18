# Install My macOS Apps

A personal Codex Skill for setting up a new Mac from a persistent app catalog. It inventories installed apps, selects a storage profile, creates an installation plan, and records follow-up tasks such as account sign-in and permissions.

## Requirements

- macOS
- Python 3 (the scripts use the standard library only)
- Homebrew for automatic Homebrew cask/formula installs
- Codex Chrome extension only when managing an official website download in Chrome

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
