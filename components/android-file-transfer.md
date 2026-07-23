---
component_id: "android-file-transfer"
name: "Android File Transfer"
category: "File transfer"
tier: "optional"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "android-file-transfer"
brew_formula: null
official_url: "https://www.android.com/filetransfer/"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 100000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# Android File Transfer

## Delivery

- Preferred source: Homebrew cask `android-file-transfer`.
- Official project page: https://www.android.com/filetransfer/
- The current cask is Intel-only and requires Rosetta 2 on Apple Silicon.
- This is an Optional item; do not install automatically during a Core deployment.

## Size tracking

- Planning download estimate: 100000000 bytes (`size_gb` catalog estimate).
- Record transfer and installed-byte measurements only in machine-local state.
- After installation, record `download_bytes`, `installed_bytes`, `installed_version`, and `installed_at`.

## Post-install checklist

- [ ] Connect an Android device and confirm file-access permission

## Notes

Review account, license, privacy, and storage settings before using the app.
