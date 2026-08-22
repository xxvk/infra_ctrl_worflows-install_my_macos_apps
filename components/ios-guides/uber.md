---
component_id: "ios-uber"
name: "Uber"
category: "Travel"
tier: "core"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "com.ubercab.UberClient"
app_store_id: 368677368
app_store_url: "https://apps.apple.com/app/id368677368"
region_availability: []
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Uber (iOS)

> [!summary] Purpose
> core expansion 2026-08 (user selection). iOS bundle `com.ubercab.UberClient`,
> App Store id `368677368`.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id368677368
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account/version.
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- Android equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

- Delete from the iPhone via the home-screen long-press flow (user action).
