---
component_id: "android-tinder"
name: "Tinder"
category: "Communication"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.tinder"
play_store_url: "https://play.google.com/store/apps/details?id=com.tinder"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Tinder (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `com.tinder`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.tinder -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.tinder/*.apk
```

## Verification

- `adb shell pm list packages | grep com.tinder` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.cardify.tinder`; see `references/cross-platform-app-map.json`.
