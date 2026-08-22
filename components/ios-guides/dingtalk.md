---
component_id: "ios-dingtalk"
name: "DingTalk"
category: "Communication"
tier: "optional"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "com.alibaba.dingtalklite"
app_store_id: 930368978
app_store_url: "https://apps.apple.com/app/id930368978"
region_availability: []
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# DingTalk (iOS)

> [!summary] Purpose
> Device inventory 2026-08, optional tier. iOS bundle `com.alibaba.dingtalklite`, App Store id `930368978`.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id930368978
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account/version.
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- Android equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

- Delete from the iPhone via the home-screen long-press flow (user action).
