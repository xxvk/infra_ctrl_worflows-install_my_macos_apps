---
component_id: "android-command-line-tools"
name: "Android command-line tools"
category: "Android tools"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "android-commandlinetools"
brew_formula: null
official_url: "https://developer.android.com/tools"
check_command: "sdkmanager"
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 200000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# Android command-line tools

Android SDK command-line tools. Install with
`brew install --cask android-commandlinetools`. Command-line tools 22 and newer
include the `android` CLI and deprecate `sdkmanager`; use `android sdk` for new
read-only inventory and package-management workflows. Keep `sdkmanager` as a
compatibility path for license acceptance and existing deterministic install
scripts until the replacement flow has been validated unattended. See
[`references/environment.md`](../references/environment.md) for the complete
Apple Silicon/Intel setup and shell verification.
