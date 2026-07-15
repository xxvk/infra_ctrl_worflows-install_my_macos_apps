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

2. Create a plan. Use `auto` unless the user explicitly selects a capacity tier:

   ```sh
   python3 scripts/macos_apps.py plan --profile auto
   ```

   `portable` applies below 512 GB; `expanded` applies at 512 GB or above. The planner includes `core` apps in both tiers, while apps marked `heavy` are excluded from `portable` by default.

3. Review the plan with the user. Select one or two apps only. Identify required free space, account/permission tasks, and any source that is not Homebrew. Do not run installations before confirmation.

4. Execute only after explicit approval. Start with a dry run, then apply the recorded plan:

   ```sh
   python3 scripts/macos_apps.py install state/PLAN.json --only "App Name"
   python3 scripts/macos_apps.py install state/PLAN.json --only "App Name" --apply
   ```

   The script accepts at most two `--only` values per run. It bootstraps Homebrew only with `--apply` and asks interactively first. It installs only catalog entries with a verified Homebrew cask or formula identifier. It never supplies credentials, modifies privacy settings, or silently installs an unverified DMG/PKG.

5. Open each just-installed GUI app and confirm that it reaches its first window without a crash or macOS security warning. Then complete the plan's `follow_up` tasks and re-run `scan`. Add completed account, license, permission, or configuration notes to the plan's `completion_notes`; never store passwords, API keys, recovery codes, or license secrets.

## Browser download preflight

Use this only when an app needs an official website download or browser-managed download; it is not required for Homebrew or App Store items.

1. Check that Google Chrome is installed.
2. Use the `control-chrome` skill to connect to the Chrome Codex extension and read its browser documentation. A successful selection of the `extension` browser is the pass condition.
3. Record the result in the current plan's `completion_notes` as `Chrome Codex extension: verified YYYY-MM-DD` or `Chrome Codex extension: unavailable`. Do not claim that a failed connection is a macOS privacy-permission failure; it may be an extension state, browser-profile, or Codex connection issue.
4. If unavailable, ask the user to open/enable the Codex Chrome extension and retry. Do not use another browser to bypass this check when the user specifically requests Chrome control.
5. Before clicking a download button, verify the vendor domain and visible file details. Ask for confirmation immediately before any browser action that initiates a software download or install. Record the final vendor URL and downloaded version in `completion_notes`.

## Docker Desktop retirement

When OrbStack is installed, check for Docker Desktop during a new-Mac scan. If `/Applications/Docker.app` exists, offer a separate cleanup; never perform it implicitly as part of an app installation.

1. Preview only:

   ```sh
   python3 scripts/docker_desktop_cleanup.py inspect
   ```

   Review the reported Docker Desktop application, Docker disk image, container/image/volume storage, settings, logs, and reclaimable size. The cleanup targets only Docker Desktop-owned locations; it deliberately preserves `~/.docker` and every OrbStack location/context.

2. State the irreversible effect plainly: the Docker Desktop app and **all Docker Desktop-local** containers, images (including user-built images), volumes, build cache, Kubernetes data, and settings will be permanently removed. Volume data may contain databases or other persistent data. It does not delete remote registry images or OrbStack data.

3. Ask the user whether to proceed. On explicit confirmation, run the official Docker Desktop uninstaller followed by the narrowly scoped residual cleanup:

   ```sh
   python3 scripts/docker_desktop_cleanup.py remove --confirm "REMOVE DOCKER DESKTOP DATA"
   ```

4. Verify with another `inspect` call and record reclaimed space plus the Docker documentation source in the plan. If the official uninstaller fails, stop and report the error; do not manually delete arbitrary Docker CLI configuration or unknown paths.

Docker states that its Mac containers and images reside in a large disk image and documents inspecting their usage with `docker system df -v`. See https://docs.docker.com/desktop/troubleshoot-and-support/faqs/macfaqs/.

## Catalog maintenance

- Edit `references/app-catalog.json` when adding, removing, or recategorizing apps. Keep the official download URL, delivery method, capacity tier, estimated size, and post-install tasks current.
- Use `brew` only for a cask or formula whose identifier is present in `brew_cask` or `brew_formula`. If a package fails validation, leave it in the plan as a manual task and update the catalog after checking the vendor source.
- Use `check_command` for CLI tools so a binary already on `PATH` is correctly considered installed. Record ordered dependencies with `install_after`; for example, install `mole` after Ghostty so the user can run and review its terminal UI.
- Use `app_store_url` for App Store software. App Store sign-in and installation remain user actions.
- Prefer vendor URLs for apps without a verified cask. Add scripted direct downloads only when the vendor provides a stable, HTTPS URL and an integrity check; otherwise keep them manual.

## Persistent records

`state/` is created beside the skill on first run and is intended to sync through iCloud. It holds dated scans, plans, and installation logs. Keep it; it is the deployment history.

## Safety rules

- Treat Homebrew bootstrap, downloads, and `--apply` as external changes requiring explicit user approval.
- Never use the catalog to automate login, license entry, security/privacy permissions, device-management enrollment, or VPN connection.
- Before installing a `heavy` app on a portable profile, state the space impact and obtain an explicit override.
