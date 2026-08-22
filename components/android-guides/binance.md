---
component_id: "android-binance"
name: "Binance"
category: "Finance"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.binance.dev"
play_store_url: "https://play.google.com/store/apps/details?id=com.binance.dev"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Binance (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.binance.dev`. 国际版（US 区下架，JP/SG 可用）

## Install (Play Store via apkeep)

```sh
apkeep -a com.binance.dev -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.binance.dev/*.apk
```

## Verification

- `adb shell pm list packages | grep com.binance.dev` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.czzhao.binance`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.binance.dev   # only after explicit confirmation
```
