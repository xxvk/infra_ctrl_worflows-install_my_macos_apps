---
component_id: "zerotier"
name: "ZeroTier"
category: "Network"
tier: "core"
lifecycle_status: "planned"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "zerotier-one"
brew_formula: null
allowed_sources: ["homebrew", "package_receipt"]
package_receipt: "com.zerotier.pkg.ZeroTierOne"
official_url: "https://www.zerotier.com/download/"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 1000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# ZeroTier

- Install with the verified Homebrew cask: `brew install --cask zerotier-one`.
  The cask installs an official pkg and may therefore be verified by the
  `com.zerotier.pkg.ZeroTierOne` package receipt rather than a Homebrew cask
  receipt.
- Follow-up remains manual: approve the network extension, sign in, and join only authorized networks.
