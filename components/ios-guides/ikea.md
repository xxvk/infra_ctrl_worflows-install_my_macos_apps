---
component_id: "ios-ikea"
name: "IKEA"
category: "Shopping"
tier: "core"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "com.ingka.ikea.app"
app_store_id: 1452164827
app_store_url: "https://apps.apple.com/app/id1452164827"
region_availability: []
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# IKEA (iOS)

> [!summary] Purpose
> Device inventory 2026-08, core tier. iOS bundle `com.ingka.ikea.app`, App Store id `1452164827`.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id1452164827
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account/version.
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- Android equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

- Delete from the iPhone via the home-screen long-press flow (user action).
