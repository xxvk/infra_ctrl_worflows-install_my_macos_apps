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

5. Open each just-installed GUI app and confirm that it reaches its first window without a crash or macOS security warning. Then complete the plan's `follow_up` tasks and re-run `scan`. Add completed account, license, permission, or configuration notes to the plan's `completion_notes`; never store passwords, API keys, recovery codes, or license secrets.

   Installation logs record download bytes and installed bytes separately for each Homebrew item. A cached or resumed download may report the final artifact size rather than bytes transferred during the current attempt.

   For Ghostty, after the app is installed, create or update `~/.config/ghostty/config` with the skill defaults below, preserving unrelated user settings:

   ```ini
   theme = Cyberpunk Scarlet Protocol
   font-family = JetBrains Mono
   font-size = 20
   ```

   Treat this as a post-install configuration step, not part of the Homebrew installation. Verify the theme name with `ghostty +list-themes --plain` and open Ghostty once after writing the config.

6. For every install, update or create the matching `components/<component_id>.md`, add or update its row in `components/README.md`, and ensure the catalog entry has the relative `guide` path. For every uninstall or removal, update that guide's frontmatter to `status: retired`, document what was removed and what data was preserved, and keep the historical install/removal evidence. A component operation is not complete until its guide and index are synchronized.

## Browser download preflight

Use this only when an app needs an official website download or browser-managed download; it is not required for Homebrew or App Store items.

1. Check that Google Chrome is installed.
2. Use the `control-chrome` skill to connect to the Chrome Codex extension and read its browser documentation. A successful selection of the `extension` browser is the pass condition.
3. Record the result in the current plan's `completion_notes` as `Chrome Codex extension: verified YYYY-MM-DD` or `Chrome Codex extension: unavailable`. Do not claim that a failed connection is a macOS privacy-permission failure; it may be an extension state, browser-profile, or Codex connection issue.
4. If unavailable, ask the user to open/enable the Codex Chrome extension and retry. Do not use another browser to bypass this check when the user specifically requests Chrome control.
5. Before clicking a download button, verify the vendor domain and visible file details. Ask for confirmation immediately before any browser action that initiates a software download or install. Record the final vendor URL and downloaded version in `completion_notes`.

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
