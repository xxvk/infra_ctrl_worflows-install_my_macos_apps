---
component_id: "brave-browser"
name: "Brave Browser"
category: "Browser"
tier: "optional"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "brave-browser"
brew_formula: null
official_url: "https://brave.com/download/"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 1000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# Brave Browser

## Delivery

- Preferred source: `brew install --cask brave-browser`
- This is an Optional item; do not install automatically during a Core deployment.
- App Store installs require the user to complete Get/Download, password, Touch ID, or 2FA.

## Size tracking

- Planning download estimate: 1000000000 bytes (`size_gb` catalog estimate).
- Record transfer and installed-byte measurements only in machine-local state.
- After installation, record `download_bytes`, `installed_bytes`, `installed_version`, and `installed_at`.

## Post-install checklist

- [ ] Sign in only if needed

## Notes

Review account, license, privacy, and storage settings before using the app.
