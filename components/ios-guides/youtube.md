---
component_id: "ios-youtube"
name: "YouTube"
category: "Media"
tier: "core"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "com.google.ios.youtube"
app_store_id: 544007664
app_store_url: "https://apps.apple.com/app/id544007664"
region_availability: []
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# YouTube (iOS)

> [!summary] Purpose
> v0 core app (purchase-history extraction, 2026-08). iOS bundle `com.google.ios.youtube`,
> App Store id `544007664`.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id544007664
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account/version.
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- See `references/cross-platform-app-map.json` for the Android equivalent.

## Cleanup

- Remove via the iPhone App Store (user action); never delete account data.
