---
component_id: "keystats"
name: "KeyStats"
category: "System tools"
tier: "core"
lifecycle_status: "planned"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "debugtheworldbot/keystats/keystats"
brew_formula: null
official_url: "https://keystats.vercel.app/"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 100000000
download_estimate_method: "catalog_size_gb_planning_estimate"
brew_tap: "debugtheworldbot/keystats"
brew_tap_repository: "https://github.com/debugtheworldbot/homebrew-keystats"
brew_tap_revision: "432771d212a4db269a37683ad707205f2fce2115"
brew_trust_cask: "debugtheworldbot/keystats/keystats"
---
# KeyStats

- Install with the verified Homebrew tap and cask:
  1. `brew tap debugtheworldbot/keystats`
  2. Review and explicitly trust only the required cask: `brew trust --cask debugtheworldbot/keystats/keystats`
  3. Verify the tap remote and HEAD against the pinned values above.
  4. `brew install --cask debugtheworldbot/keystats/keystats`
- The tap trust step is required by Homebrew and must not be replaced with whole-tap trust or `HOMEBREW_NO_REQUIRE_TAP_TRUST=1`.
- CLI status: not provided; verify the GUI app and Accessibility permission instead.

## Gatekeeper note

This cask may be ad-hoc signed and retain a quarantine attribute. If the
Homebrew source and checksum have been reviewed, remove only this App's
quarantine marker and open it:

```sh
xattr -dr com.apple.quarantine /Applications/KeyStats.app
open -a /Applications/KeyStats.app
```

Do not disable Gatekeeper globally merely for KeyStats. The app may still show
an ad-hoc signature in `codesign`; verify the running process and review the
Accessibility permission request in System Settings.
