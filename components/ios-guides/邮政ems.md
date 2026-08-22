---
component_id: "ios-邮政ems"
name: "邮政EMS"
category: "Japan life"
tier: "optional"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "com.ems.newemsexpress"
app_store_id: 1242727213
app_store_url: "https://apps.apple.com/app/id1242727213"
region_availability: ["JP"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# 邮政EMS (iOS)

> [!summary] Purpose
> Device inventory 2026-08, optional tier. iOS bundle `com.ems.newemsexpress`, App Store id `1242727213`.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id1242727213
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account/version.
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- Android equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

- Delete from the iPhone via the home-screen long-press flow (user action).
