---
component_id: "ios-sbi証券"
name: "SBI証券"
category: "Finance"
tier: "core"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "jp.co.sbisec.sbikabu2sp"
app_store_id: 1240742779
app_store_url: "https://apps.apple.com/app/id1240742779"
region_availability: ["JP"]
account_required: true
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# SBI証券 (iOS)

> [!summary] Purpose
> Japan-region core app (2026-08 user selection). iOS bundle `jp.co.sbisec.sbikabu2sp`,
> App Store id `1240742779`. Requires a Japanese account.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id1240742779
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account (Japanese banking/POS account).
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- Android equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

- Delete from the iPhone via the home-screen long-press flow (user action).
