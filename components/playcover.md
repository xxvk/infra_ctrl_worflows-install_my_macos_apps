---
component_id: "playcover"
name: "PlayCover"
category: "Compatibility"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "playcover/playcover/playcover-community"
brew_formula: null
official_url: "https://github.com/PlayCover/PlayCover"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 1000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
brew_tap: "playcover/playcover"
brew_tap_repository: "https://github.com/PlayCover/homebrew-playcover"
brew_tap_revision: "04bb422fa336c2b95bfa9962c91b5fbac30eac94"
brew_trust_cask: "playcover/playcover/playcover-community"
---

# PlayCover

PlayCover runs compatible iOS/iPadOS applications on Apple Silicon Macs.

## Installation

The skill must verify the tap remote and full reviewed revision before granting
package-scoped trust. Never trust the entire tap.

```sh
brew tap playcover/playcover
brew trust --cask playcover/playcover/playcover-community
brew install --cask playcover/playcover/playcover-community
```

## Verification

```sh
brew list --cask playcover-community
test -d /Applications/PlayCover.app
```

Imported IPA files require a separate approval, hash, bundle-ID check, and
launch test. Installing PlayCover does not authorize importing an IPA.

## Rollback

```sh
brew uninstall --cask playcover-community
```

Remove imported applications or PlayCover containers only under a separate,
explicit cleanup request.
