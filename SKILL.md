---
name: install-macos-apps
description: Scan a Mac for installed applications, compare it with a persistent personal macOS app catalog, and create or execute a capacity-aware installation plan. Use when setting up a new Mac, auditing missing apps, maintaining a personal app inventory, installing selected apps with Homebrew, or documenting download sources, accounts, licenses, privacy permissions, and post-install tasks.
---

# Install My macOS Apps

Use this skill from its synced source folder. Treat the catalog as the source of truth; never infer that an app is installed merely because its installer or receipt exists.

## Workflow

1. Inspect the current Mac and write a dated scan:

   ```sh
   python3 scripts/macos_apps.py scan
   ```

   The scan records source evidence for catalog apps. An App Store receipt is
   checked at `Contents/_MASReceipt/receipt`; Homebrew casks are checked against
   `brew list --cask`; other bundles are reported as `manual_or_unknown`. A
   source mismatch is a review item, not proof of malicious software.

2. Create a plan. Use `auto` unless the user explicitly selects a capacity tier:

   ```sh
   python3 scripts/macos_apps.py plan --profile auto
   ```

   `portable` applies below 512 GB; `expanded` applies at 512 GB or above. The planner includes `core` apps in both tiers, while apps marked `heavy` are excluded from `portable` by default.

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

4. Execute only after explicit approval. Start with a dry run, then apply the recorded plan:

   ```sh
   python3 scripts/macos_apps.py install state/PLAN.json --only "App Name"
   python3 scripts/macos_apps.py install state/PLAN.json --only "App Name" --apply
   ```

   The script accepts at most two `--only` values per run. It bootstraps Homebrew only with `--apply` and asks interactively first. It installs only catalog entries with a verified Homebrew cask or formula identifier. It never supplies credentials, modifies privacy settings, or silently installs an unverified DMG/PKG.

   **Claude pre-install storage gate:** before installing or replacing Claude,
   run `python3 scripts/claude_vm_cleanup.py inspect`. The VM review and any
   cleanup are separate actions from the Claude installation. Only after the
   user explicitly confirms, and only after Claude is fully quit, may the skill
   run `remove --confirm "REMOVE CLAUDE VM IMAGES"`. Optional directory locking
   is a second confirmation using `lock --confirm "LOCK CLAUDE VM DIRECTORY"`;
   it disables Cowork/local-agent VM recreation and is never implicit. See
   [components/claude.md](components/claude.md).

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
3. The skill must open the catalog's App Store URL for the user (using the
   App Store UI when available), search for the exact app if needed, select
   `Mac Apps`, and report whether the button says `Get`, `Download`,
   `Redownload`, `Update`, or `Open`. Stop immediately before any
   `Get`/`Download`/`Redownload` action and ask for confirmation. After the
   user confirms, the skill may click that button, but the user must complete
   any Apple Account password, Touch ID, purchase, or two-factor prompt.
   App Store installation must not be automated with Apple Configurator,
   undocumented store APIs, or credential entry.
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

6. For every install, update or create the matching `components/<component_id>.md`, add or update its row in `components/README.md`, and ensure the catalog entry has the relative `guide` path. For every uninstall or removal, update that guide's frontmatter to `status: retired`, document what was removed and what data was preserved, and keep the historical install/removal evidence. A component operation is not complete until its guide and index are synchronized.

   Every Core guide must persist both delivery and storage measurements:
   `download_bytes` (actual bytes transferred for the install),
   `installed_bytes` (measured on-disk footprint after installation),
   `installed_version`, and `installed_at`. The catalog's `size_gb` remains an
   estimate used for planning and must never be presented as the measured
   footprint. For a not-yet-installed Core app, use `null`/`pending` rather
   than inventing measurements. Audit the complete Core set with:

   ```sh
   python3 scripts/audit_core_catalog.py
   ```

   Estimate download size in this order: (a) a cached Homebrew artifact or
   vendor-provided installer size, (b) the Mac App Store listing size for a
   verified Mac build, (c) a vendor download page/API, and only then (d) the
   catalog `size_gb` planning estimate. Label the method and timestamp; never
   present an estimate as transferred bytes. After installation, measure the
   actual bundle or Homebrew prefix with `du` and record `installed_bytes`.

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

For a new Mac, treat `config/chrome-profiles.json` as the synced desired
seven-profile registry. Compare it with a fresh `state/chrome-profiles-inventory.json`
by
`profile_directory` and `account_email`; report missing, extra, or mismatched
profiles. Restore missing profiles one at a time by creating/opening the exact
profile directory with Chrome, then let the user complete Google sign-in,
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
- Source policy is explicit: `app_store_url` means `app_store`, `brew_cask` or
  `brew_formula` means `homebrew`, `official_url` alone means `official_web`,
  and `system_app: true` means `system`. Keep source mismatches visible in plans;
  do not silently accept a website download for an App Store-required app.
- Prefer vendor URLs for apps without a verified cask. Add scripted direct downloads only when the vendor provides a stable, HTTPS URL and an integrity check; otherwise keep them manual.

## Persistent records

`state/` is created beside the skill on first run and is intended to sync through iCloud. It holds dated scans, plans, and installation logs. Keep it; it is the deployment history.

Detailed per-component instructions live in `components/README.md` and the linked Markdown guides. Keep the catalog as the install metadata source of truth, and link each detailed guide from its catalog entry with a relative `guide` path.

## Safety rules

- Treat Homebrew bootstrap, downloads, and `--apply` as external changes requiring explicit user approval.
- Never use the catalog to automate login, license entry, security/privacy permissions, device-management enrollment, or VPN connection.
- Before installing a `heavy` app on a portable profile, state the space impact and obtain an explicit override.
