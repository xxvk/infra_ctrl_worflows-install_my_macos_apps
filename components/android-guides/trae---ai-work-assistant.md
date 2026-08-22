---
component_id: "android-trae---ai-work-assistant"
name: "TRAE - AI Work Assistant"
category: "AI"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.stone.solo.cn"
play_store_url: "https://play.google.com/store/apps/details?id=com.stone.solo.cn"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# TRAE - AI Work Assistant (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `com.stone.solo.cn`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.stone.solo.cn -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.stone.solo.cn/*.apk
```

## Verification

- `adb shell pm list packages | grep com.stone.solo.cn` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.stone.solo.i18n`; see `references/cross-platform-app-map.json`.
