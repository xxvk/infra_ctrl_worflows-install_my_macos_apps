---
component_id: "ios-linksys"
name: "Linksys"
category: "Smart home"
tier: "optional"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "com.cisco.hnbu.connectcloud"
app_store_id: 533516503
app_store_url: "https://apps.apple.com/app/id533516503"
region_availability: []
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Linksys (iOS)

> [!summary] Purpose
> Device inventory 2026-08, optional tier. iOS bundle `com.cisco.hnbu.connectcloud`, App Store id `533516503`.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id533516503
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account/version.
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- Android equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

- Delete from the iPhone via the home-screen long-press flow (user action).
