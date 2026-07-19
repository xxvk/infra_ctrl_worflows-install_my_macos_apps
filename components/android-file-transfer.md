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
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
installed_measurement_method: "local_du"
---
# Android File Transfer

## Delivery

- Preferred source: Homebrew cask `android-file-transfer`.
- Official project page: https://www.android.com/filetransfer/
- The current cask is Intel-only and requires Rosetta 2 on Apple Silicon.
- This is an Optional item; do not install automatically during a Core deployment.

## Size tracking

- Planning download estimate: 100000000 bytes (`size_gb` catalog estimate).
- Installed footprint above is measured locally; download bytes remain `null` unless a package transfer log is available.
- After installation, record `download_bytes`, `installed_bytes`, `installed_version`, and `installed_at`.

## Post-install checklist

- [ ] Connect an Android device and confirm file-access permission

## Notes

Review account, license, privacy, and storage settings before using the app.

## Local evidence (2026-07-16)

- Installed path: `/Applications/Android File Transfer.app`
- Installed version: `1.0.12`
- Installed footprint: `6696960` bytes, measured with `du -sk`.
- Download bytes are recorded separately; a local bundle footprint is not treated as download volume.
