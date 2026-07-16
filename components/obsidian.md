---
component_id: "obsidian"
name: "Obsidian"
category: "Productivity"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "obsidian"
brew_formula: null
official_url: "https://obsidian.md/download"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 1000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
Obsidian
  and verify the interface. This is an application-level setting stored in
  Obsidian's local storage (commonly the `language` key with value `zh`), not a
  vault setting in `.obsidian/app.json`; do not edit Electron/LevelDB files as
  part of deployment.
- Open the synced `XVK_PM` vault and confirm the expected files are visible.
- Choose one synchronization method deliberately: iCloud or Obsidian Sync;
  do not enable two competing sync mechanisms for the same vault without a
  backup and conflict plan.
- Review community plugins before enabling them and keep credentials outside
  the app catalog.
