---
component_id: "ios-woodstock"
name: "Woodstock"
category: "Finance"
tier: "optional"
lifecycle_status: "active"
source: "manual_or_unknown"
ios_bundle_id: "club.woodstock.app"
app_store_id: null
app_store_url: ""
region_availability: []
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Woodstock (iOS)

> [!summary] Purpose
> Device inventory 2026-08, optional tier. iOS bundle `club.woodstock.app`.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/idNone
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account/version.
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- Android equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

- Delete from the iPhone via the home-screen long-press flow (user action).
