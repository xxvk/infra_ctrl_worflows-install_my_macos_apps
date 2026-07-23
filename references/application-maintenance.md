# Application maintenance and verification

Load this reference only when the current task uses this domain. Its rules were moved verbatim from the original skill entry point during RC-05.

## Contents

- GUI app and CLI workflow
- Duplicate bundle cleanup
- Complete removal and embedded helper cleanup
- Browser download preflight
- Chrome multi-profile workflow
- GitHub CLI preflight
- Docker Desktop retirement
- Catalog maintenance

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
4. Record the current `cli_status`, `cli_path`, and `cli_version` in
   machine-local state. Keep only the reusable CLI delivery and verification contract in
   the component guide; never mark the GUI install incomplete merely because
   an optional CLI does not exist.

For App Store apps without a documented CLI, record `cli_status: not_provided`.
For GUI apps with a separate Homebrew formula, install and verify that formula
independently. This rule applies globally, not only to MQTT Explorer.

An App Store GUI and a Homebrew CLI are separate catalog capabilities. If a
vendor provides both, add `cli_command`, `cli_formula`, and
`cli_link_policy: separate_formula` to the GUI entry, then install/verify the
formula independently. Only create a PATH/symlink link when the vendor or
formula documents the target; never infer one from an App Store bundle. Record
the current CLI path/version in machine-local state, not the component guide. A
GUI App Store receipt alone does not prove that a CLI exists.

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
   results to a machine-local `remove-*.json` record. Do not put current
   machine paths or measurements in reusable component Markdown.
5. For catalog components, set the guide and catalog `lifecycle_status` to
   `retired` and document what was removed and what data was preserved. For an
   unlisted nested helper, keep the reusable procedure here and record
   machine-specific evidence only in machine-local state.

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
  --expected Private/chrome-profiles.json \
  --output "$(python3 scripts/state_paths.py path)/chrome-profiles-inventory.json"
```

The `display_name` in `Private/chrome-profiles.json` is the canonical naming
registry, matched to each account by `account_email`. Read the current mapping
from that tracked Private file; do not duplicate its personal identifiers in
this public procedure.

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

For a new Mac, treat `Private/chrome-profiles.json` as the synced desired
seven-profile registry. Compare it with a fresh machine-local
`chrome-profiles-inventory.json`
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



