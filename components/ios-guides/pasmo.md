---
component_id: "ios-pasmo"
name: "PASMO"
category: "Finance"
tier: "core"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "jp.pasmo.mobile.app"
app_store_id: 1489151487
app_store_url: "https://apps.apple.com/app/id1489151487"
region_availability: ["JP"]
account_required: true
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# PASMO (iOS)

> [!summary] Purpose
> Japan-region core app (2026-08 user selection). iOS bundle `jp.pasmo.mobile.app`,
> App Store id `1489151487`. Requires a Japanese account.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id1489151487
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account (Japanese banking/POS account).
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- Android equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

- Delete from the iPhone via the home-screen long-press flow (user action).
