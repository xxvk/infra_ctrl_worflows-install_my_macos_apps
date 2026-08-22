---
component_id: "ios-yahooショッピング"
name: "Yahoo!ショッピング"
category: "Shopping"
tier: "optional"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "jp.co.yahoo.Shopping"
app_store_id: 446016180
app_store_url: "https://apps.apple.com/app/id446016180"
region_availability: []
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Yahoo!ショッピング (iOS)

> [!summary] Purpose
> Device inventory 2026-08, optional tier. iOS bundle `jp.co.yahoo.Shopping`, App Store id `446016180`.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id446016180
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account/version.
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- Android equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

- Delete from the iPhone via the home-screen long-press flow (user action).
