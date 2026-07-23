---
component_id: "filezilla"
name: "FileZilla"
category: "File transfer"
tier: "optional"
lifecycle_status: "active"
source: "official_web"
delivery_method: "vendor-download"
brew_cask: null
brew_formula: null
official_url: "https://filezilla-project.org/"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 1000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# FileZilla

## Delivery

- Preferred source: https://filezilla-project.org/
- This is an Optional item; do not install automatically during a Core deployment.
- App Store installs require the user to complete Get/Download, password, Touch ID, or 2FA.

## Size tracking

- Planning download estimate: 1000000000 bytes (`size_gb` catalog estimate).
- Record transfer and installed-byte measurements only in machine-local state.
- After installation, record `download_bytes`, `installed_bytes`, `installed_version`, and `installed_at`.

## Post-install checklist

- [ ] Add sites manually

## Notes

Review account, license, privacy, and storage settings before using the app.
