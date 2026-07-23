---
component_id: "affinity"
name: "Affinity"
category: "Design"
tier: "optional"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "affinity"
brew_formula: null
official_url: "https://affinity.serif.com/"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 3000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# Affinity

## Delivery

- Preferred source: Homebrew cask `affinity`.
- Official project page: https://www.affinity.studio/
- Install with `brew install --cask affinity`.
- This is an Optional item; do not install automatically during a Core deployment.
- App Store installs require the user to complete Get/Download, password, Touch ID, or 2FA.

## Size tracking

- Planning download estimate: 3000000000 bytes (`size_gb` catalog estimate).
- Record transfer and installed-byte measurements only in machine-local state.
- After installation, record `download_bytes`, `installed_bytes`, `installed_version`, and `installed_at`.

## Post-install checklist

- [ ] Sign in and activate the applicable Affinity license

## Notes

Review account, license, privacy, and storage settings before using the app.
