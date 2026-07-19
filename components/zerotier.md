---
component_id: "zerotier"
name: "ZeroTier"
category: "Network"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "zerotier-one"
brew_formula: null
official_url: "https://www.zerotier.com/download/"
check_command: null
install_after: []
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
---
# ZeroTier

- Install with the verified Homebrew cask: `brew install --cask zerotier-one`.
  The cask installs an official pkg and may therefore be verified by the
  `com.zerotier.pkg.ZeroTierOne` package receipt rather than a Homebrew cask
  receipt.
- Follow-up remains manual: approve the network extension, sign in, and join only authorized networks.
