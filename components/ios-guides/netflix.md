---
component_id: "ios-netflix"
name: "Netflix"
category: "Media"
tier: "core"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "com.netflix.Netflix"
app_store_id: 363590051
app_store_url: "https://apps.apple.com/app/id363590051"
region_availability: []
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Netflix (iOS)

> [!summary] Purpose
> v0 core app (purchase-history extraction, 2026-08). iOS bundle `com.netflix.Netflix`,
> App Store id `363590051`.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id363590051
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account/version.
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- See `references/cross-platform-app-map.json` for the Android equivalent.

## Cleanup

- Remove via the iPhone App Store (user action); never delete account data.
