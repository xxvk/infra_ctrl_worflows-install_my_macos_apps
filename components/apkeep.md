---
component_id: "apkeep"
name: "apkeep"
category: "Android tools"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-formula"
brew_formula: "apkeep"
official_url: "https://github.com/EFForg/apkeep"
check_command: "apkeep --version"
account_required: false
permissions_required: []
secrets_policy: "Never store Google account credentials, OAuth tokens, or AAS tokens here."
install_after: []
brew_cask: null
download_estimate_bytes: 10000000
download_estimate_method: "brew_bottle_estimate"
---

# apkeep

> [!summary] Purpose
> Command-line tool for downloading APK files from Google Play, APKPure,
> F-Droid, and Huawei AppGallery. Core Android tool for acquiring APKs onto a
> connected device.

## Source

- Formula: `apkeep` (official Homebrew core formula)
- Upstream: `https://github.com/EFForg/apkeep` (MIT)

## Authentication (Google Play)

Downloading directly from Google Play requires a Google account token:

1. The user obtains an OAuth token from
   `https://accounts.google.com/EmbeddedSetup` (browser Network tab, cookie
   `oauth_token`, starts `oauth2_4/`). This token is single-use.
2. Exchange it once for an AAS token:
   ```sh
   apkeep -e '<user@example.com>' --oauth-token oauth2_4/...
   ```
3. Download with the AAS token:
   ```sh
   apkeep -a <package> -d google-play -e '<user@example.com>' -t <aas_token> .
   ```

**Never automate, store, or type Google credentials or tokens on the user's
behalf** — the token steps are user handoffs. Third-party mirrors
(`-d apk-pure`) need no login but must be evaluated for signature/trust before
use.

## Usage

```sh
# Android CLI tools / platform-tools and adb are prerequisites (catalog)
apkeep --version
apkeep -a com.tencent.mm -d google-play -e '<user@example.com>' -t <aas_token> .
adb install --user 0 ./com.tencent.mm.apk   # or split-APK install
```

## Follow-up and verification

- Record downloaded APK paths and sha256 in machine-local state only.
- Verify the installed package with `adb shell pm list packages` read-back.
- Prefer `-d f-droid` for open-source apps; evaluate third-party mirrors.

## Cleanup

```sh
brew uninstall apkeep
```

## Evidence and notes

- Formula: `https://github.com/Homebrew/homebrew-core/blob/HEAD/Formula/a/apkeep.rb`
- Machine-specific downloads, paths, and verification results belong only in
  machine-local state.

Never paste a machine-local record, downloaded APK hash, token, or timestamp
back into this tracked guide.
