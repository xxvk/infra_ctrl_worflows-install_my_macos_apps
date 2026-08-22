---
component_id: "ios-google-home"
name: "Google Home"
category: "Smart home"
tier: "core"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "com.google.Chromecast"
app_store_id: 680819774
app_store_url: "https://apps.apple.com/app/id680819774"
region_availability: []
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Google Home (iOS)

> [!summary] Purpose
> core expansion 2026-08 (user selection). iOS bundle `com.google.Chromecast`,
> App Store id `680819774`.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id680819774
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account/version.
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- Android equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

- Delete from the iPhone via the home-screen long-press flow (user action).
