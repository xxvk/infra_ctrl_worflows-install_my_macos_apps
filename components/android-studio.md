---
component_id: "android-studio"
name: "Android Studio"
category: "Developer tools"
tier: "optional"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "android-studio"
brew_formula: null
official_url: "https://developer.android.com/studio"
check_command: null
install_after: []
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
installed_measurement_method: "local_du"
---
# Android Studio

## Delivery

- Preferred source: Homebrew cask `android-studio`.
- Official project page: https://developer.android.com/studio
- Install with `brew install --cask android-studio`.
- If `/opt/homebrew/bin/studio` already belongs to WordPress Studio, use
  `brew install --cask --no-binaries android-studio` to preserve that CLI name;
  launch Android Studio from `/Applications/Android Studio.app`.
- This is an Optional item; do not install automatically during a Core deployment.

## Size tracking

- Planning download estimate: 5000000000 bytes (`size_gb` catalog estimate).
- Installed footprint above is measured locally; download bytes remain `null` unless a package transfer log is available.
- After installation, record `download_bytes`, `installed_bytes`, `installed_version`, and `installed_at`.

## Post-install checklist

- [ ] Install required SDK platforms and emulator images only

## Notes

Review account, license, privacy, and storage settings before using the app.

## Local evidence (2026-07-16)

- Installed path: `/Applications/Android Studio.app`
- Installed version: `2025.2`
- Installed footprint: `3208794112` bytes, measured with `du -sk`.
- Download bytes are recorded separately; a local bundle footprint is not treated as download volume.
