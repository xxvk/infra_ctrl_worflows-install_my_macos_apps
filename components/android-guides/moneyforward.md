---
component_id: "android-moneyforward"
name: "MoneyForward"
category: "Finance"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.moneyforward.mfwallet"
play_store_url: "https://play.google.com/store/apps/details?id=com.moneyforward.mfwallet"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# MoneyForward (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `com.moneyforward.mfwallet`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.moneyforward.mfwallet -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.moneyforward.mfwallet/*.apk
```

## Verification

- `adb shell pm list packages | grep com.moneyforward.mfwallet` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.moneyforward.moneyfwd`; see `references/cross-platform-app-map.json`.
