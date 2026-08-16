---
component_id: "xcode"
name: "Xcode"
category: "Developer tools"
tier: "optional"
lifecycle_status: "active"
source: "app_store"
delivery_method: "app-store"
brew_cask: null
brew_formula: null
official_url: null
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 15000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# Xcode

## Delivery

- Preferred source: Mac App Store: https://apps.apple.com/app/xcode/id497799835?mt=12
- This is an Optional item; do not install automatically during a Core deployment.
- App Store installs require the user to complete Get/Download, password, Touch ID, or 2FA.

## Size tracking

- Planning download estimate: 15000000000 bytes (`size_gb` catalog estimate).
- Record transfer and installed-byte measurements only in machine-local state.
- After installation, record `download_bytes`, `installed_bytes`, `installed_version`, and `installed_at`.

## Post-install checklist

- [ ] Open once to accept the license
- [ ] Install command-line tools only if required

## Notes

Review account, license, privacy, and storage settings before using the app.

## Storage and removal guard

Measure `/Applications/Xcode.app`, Xcode-managed DerivedData, simulators, and
`/Library/Developer/CommandLineTools` separately. Command Line Tools are not
duplicate Xcode data and remain a Core developer capability. Never delete SDK
directories or `/Library/Developer` subtrees directly to recover space.

Before an explicitly approved Xcode uninstall, read `xcode-select -p`. If it
points inside Xcode, switch to the installed Command Line Tools path through
the supported `xcode-select` operation, then verify `clang`, `git`, and the
required SDK tooling. Only the measured free-space delta after the app removal
is reclaimed capacity; App Store download size and recursive clone-sensitive
totals are planning evidence, not proof.

When Xcodes manages the replacement, follow the activation, exact-SDK symbol
check, and root-owned old-bundle recovery guard in [xcodes.md](xcodes.md).
Never infer that a replacement is active from Xcodes UI wording alone.
