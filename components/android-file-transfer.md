---
installed_measurement_method: "local_du"
name: "Android File Transfer"
category: "File transfer"
tier: optional
status: "installed"
source: official_web
download_bytes: null
download_estimate_bytes: 100000000
download_estimate_method: catalog_size_gb_planning_estimate
installed_bytes: 6696960
installed_version: "1.0.12"
installed_at: "2026-07-16"
secrets_policy: Never store passwords, API keys, recovery codes, or license secrets here.
---
# Android File Transfer

## Delivery

- Preferred source: https://www.android.com/filetransfer/
- This is an Optional item; do not install automatically during a Core deployment.
- App Store installs require the user to complete Get/Download, password, Touch ID, or 2FA.

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
