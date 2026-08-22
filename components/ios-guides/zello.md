---
component_id: "ios-zello"
name: "Zello"
category: "Communication"
tier: "optional"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "com.zello.client.main"
app_store_id: 508231856
app_store_url: "https://apps.apple.com/app/id508231856"
region_availability: []
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Zello (iOS)

> [!summary] Purpose
> Device inventory 2026-08, optional tier. iOS bundle `com.zello.client.main`, App Store id `508231856`.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id508231856
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account/version.
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- Android equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

- Delete from the iPhone via the home-screen long-press flow (user action).
