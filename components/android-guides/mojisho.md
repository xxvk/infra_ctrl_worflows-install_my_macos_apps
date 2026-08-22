---
component_id: "android-mojisho"
name: "MOJisho"
category: "Learning"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.mojisho.moji"
play_store_url: "https://play.google.com/store/apps/details?id=com.mojisho.moji"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# MOJisho (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `com.mojisho.moji`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.mojisho.moji -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.mojisho.moji/*.apk
```

## Verification

- `adb shell pm list packages | grep com.mojisho.moji` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `3EW3QF484M.MojiDict`; see `references/cross-platform-app-map.json`.
