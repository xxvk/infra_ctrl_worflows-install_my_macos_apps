---
component_id: "android-apple-tv"
name: "Apple TV"
category: "Media"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.apple.atve.androidtv.appletv"
play_store_url: "https://play.google.com/store/apps/details?id=com.apple.atve.androidtv.appletv"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Apple TV (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.apple.atve.androidtv.appletv`. Android 为 Android TV 版，手机可装

## Install (Play Store via apkeep)

```sh
apkeep -a com.apple.atve.androidtv.appletv -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.apple.atve.androidtv.appletv/*.apk
```

## Verification

- `adb shell pm list packages | grep com.apple.atve.androidtv.appletv` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.apple.tv`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.apple.atve.androidtv.appletv   # only after explicit confirmation
```
