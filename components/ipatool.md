---
component_id: "ipatool"
name: "IPATool"
category: "Developer CLI"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-formula"
brew_cask: null
brew_formula: "ipatool"
official_url: "https://github.com/majd/ipatool"
check_command: "ipatool"
install_after: []
account_required: true
permissions_required: []
secrets_policy: "Never store Apple passwords, two-factor codes, App Store tokens, or downloaded IPA files in the catalog, state/, Obsidian, or Git."
download_estimate_bytes: 30000000
download_estimate_method: "catalog_size_gb_planning_estimate"
recommended_for_playcover_ipa: false
---
# IPATool

IPATool is a Homebrew-installed CLI for searching the iOS App Store and
downloading app packages (`.ipa`) with an Apple App Store account. It remains
installed as a general developer utility, but it is **not** the acquisition
path for PlayCover on this fleet: M4a and M4b already verified that the
account/authentication workflow is not usable for the required packages.

## Installation

```sh
brew install ipatool
ipatool --version
```

## Apple account login

1. Identify the intended App Store purchase account. The Mac's current iCloud
   account is only a candidate; iCloud and App Store purchase accounts can
   differ.
2. Start the login from a visible Terminal so the user can enter secrets:

   ```sh
   ipatool auth login --email "<APPLE_ID>"
   ```

3. Enter the Apple password and any six-digit two-factor code in Terminal.
   Never send either value through chat or write them to the catalog, `state/`,
   logs, or Git.
4. Verify the account:

   ```sh
   ipatool auth info
   ```

The current IPATool CLI uses an email/password plus two-factor interaction; it
does not provide a native macOS Passkey/Touch ID login prompt. If the account
is protected by a flow that cannot complete this interaction, stop and let the
user finish authentication manually.

## YouTube example (not the PlayCover path)

YouTube's App Store bundle identifier is `com.google.ios.youtube`:

```sh
ipatool search YouTube
ipatool download \
  --bundle-identifier com.google.ios.youtube \
  --purchase \
  --output ~/Downloads/YouTube.ipa
```

IPATool downloads an App Store package, which may be encrypted. A successful
download is not proof that PlayCover can run it, and this workflow is known to
be unusable on M4a/M4b. Do not use it as a prerequisite for YouTube.

For PlayCover, use only the approved decrypted-IPA source label from
`Private/app-catalog-overlay.json`, verify the bundle identifier and decrypted
status, then import it in PlayCover. Never silently install modified or
unverified IPA files.

## Verification and cleanup

```sh
ipatool auth info
file ~/Downloads/YouTube.ipa
```

Record the current version, authentication result, download path, and PlayCover
test result only in ignored machine-local `state/` records. Remove temporary
IPA files after the test when they are no longer needed. Revoke IPATool's saved
credentials when retiring the account from this Mac:

```sh
ipatool auth revoke
```
