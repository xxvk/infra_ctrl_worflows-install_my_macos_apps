---
component_id: "ios-iam"
name: "IAM"
category: "Japan life"
tier: "optional"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "jp.co.shiftplus.iammobile.production"
app_store_id: 1636275218
app_store_url: "https://apps.apple.com/app/id1636275218"
region_availability: ["JP"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# IAM (iOS)

> [!summary] Purpose
> Device inventory 2026-08, optional tier. iOS bundle `jp.co.shiftplus.iammobile.production`, App Store id `1636275218`.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id1636275218
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account/version.
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- Android equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

- Delete from the iPhone via the home-screen long-press flow (user action).
