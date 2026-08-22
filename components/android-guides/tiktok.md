---
component_id: "android-tiktok"
name: "TikTok"
category: "Media"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.zhiliaoapp.musically"
play_store_url: "https://play.google.com/store/apps/details?id=com.zhiliaoapp.musically"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# TikTok (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `com.zhiliaoapp.musically`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.zhiliaoapp.musically -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.zhiliaoapp.musically/*.apk
```

## Verification

- `adb shell pm list packages | grep com.zhiliaoapp.musically` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.ss.iphone.ugc.Ame`; see `references/cross-platform-app-map.json`.
