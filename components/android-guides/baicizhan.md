---
component_id: "android-baicizhan"
name: "Baicizhan"
category: "Learning"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.jiongji.andriod.card"
play_store_url: "https://play.google.com/store/apps/details?id=com.jiongji.andriod.card"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Baicizhan (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `com.jiongji.andriod.card`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.jiongji.andriod.card -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.jiongji.andriod.card/*.apk
```

## Verification

- `adb shell pm list packages | grep com.jiongji.andriod.card` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.chaoui.jiongji100CN`; see `references/cross-platform-app-map.json`.
