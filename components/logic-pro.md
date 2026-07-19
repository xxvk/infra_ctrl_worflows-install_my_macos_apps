---
component_id: "logic-pro"
name: "Logic Pro"
category: "Audio"
tier: "optional"
lifecycle_status: "active"
source: "app_store"
delivery_method: "app-store"
brew_cask: null
brew_formula: null
official_url: null
check_command: null
install_after: []
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
installed_measurement_method: "local_du"
---
# Logic Pro

## Delivery

- Preferred source: Mac App Store: https://apps.apple.com/app/logic-pro/id634148309?mt=12
- This is an Optional item; do not install automatically during a Core deployment.
- App Store installs require the user to complete Get/Download, password, Touch ID, or 2FA.

## Size tracking

- Planning download estimate: 7000000000 bytes (`size_gb` catalog estimate).
- Installed footprint above is measured locally; download bytes remain `null` unless a package transfer log is available.
- After installation, record `download_bytes`, `installed_bytes`, `installed_version`, and `installed_at`.

## Post-install checklist

- [ ] Download sound libraries only when needed
- [ ] Choose sound-library location

## Notes

Review account, license, privacy, and storage settings before using the app.

## Local evidence (2026-07-16)

- Installed path: `/Applications/Logic Pro.app`
- Installed version: `12.0.1`
- Installed footprint: `1989111808` bytes, measured with `du -sk`.
- Download bytes are recorded separately; a local bundle footprint is not treated as download volume.
