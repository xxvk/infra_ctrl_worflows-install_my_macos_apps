---
component_id: "blender"
name: "Blender"
category: "3D and design"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "blender"
brew_formula: null
official_url: "https://www.blender.org/download/"
check_command: "test -d '/Applications/Blender.app'"
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 1500000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# Blender

## Delivery

- Preferred source: Homebrew cask `blender`.
- Official source: https://www.blender.org/download/
- Homebrew currently provides the cask on supported macOS versions.

```sh
brew install --cask blender
```

## Post-install checklist

- [ ] Open `/Applications/Blender.app` once and confirm the first window.
- [ ] Choose project, render-cache, and asset locations with sufficient free space.
- [ ] Keep large render caches and downloaded assets outside shared system folders unless intentionally shared.

## Verification

```sh
test -d '/Applications/Blender.app'
/usr/libexec/PlistBuddy -c 'Print :CFBundleShortVersionString' '/Applications/Blender.app/Contents/Info.plist'
```

Record `download_bytes`, `installed_bytes`, `installed_version`, and
`installed_at` in the ignored `state/` installation record. The catalog size is
only a planning estimate.
