---
component_id: "ios-testflight"
name: "TestFlight"
category: "Developer tools"
tier: "core"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "com.apple.TestFlight"
app_store_id: 899247664
app_store_url: "https://apps.apple.com/app/id899247664"
region_availability: []
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# TestFlight (iOS)

> [!summary] Purpose
> Device inventory 2026-08, core tier. iOS bundle `com.apple.TestFlight`, App Store id `899247664`.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id899247664
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account/version.
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- Android equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

- Delete from the iPhone via the home-screen long-press flow (user action).
