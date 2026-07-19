---
component_id: "android-studio-preview"
name: "Android Studio Preview"
category: "Developer tools"
tier: "optional"
lifecycle_status: "active"
source: "official_web"
delivery_method: "vendor-download"
brew_cask: null
brew_formula: null
official_url: "https://developer.android.com/studio/preview"
check_command: null
install_after: []
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
installed_measurement_method: "local_du"
---
# Android Studio Preview

## Delivery

- Preferred source: https://developer.android.com/studio/preview
- This is an Optional item; do not install automatically during a Core deployment.
- App Store installs require the user to complete Get/Download, password, Touch ID, or 2FA.

## Size tracking

- Planning download estimate: 5000000000 bytes (`size_gb` catalog estimate).
- Actual download and installed footprint remain `null` until installation is performed and measured.
- After installation, record `download_bytes`, `installed_bytes`, `installed_version`, and `installed_at`.

## Post-install checklist

- [ ] Keep separate from the stable build when testing preview features

## Notes

Review account, license, privacy, and storage settings before using the app.

## Local evidence (2026-07-16)

- Installed path: `/Applications/Android Studio Preview.app`
- Installed version: `2025.3`
- Installed footprint: `3222032384` bytes, measured with `du -sk`.
- Download bytes are not available from the original installation record; the planning estimate remains separate.
