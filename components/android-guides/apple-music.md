---
component_id: "android-apple-music"
name: "Apple Music"
category: "Media"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.apple.android.music"
play_store_url: "https://play.google.com/store/apps/details?id=com.apple.android.music"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Apple Music (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.apple.android.music`. Apple 生态 Android 版

## Install (Play Store via apkeep)

```sh
apkeep -a com.apple.android.music -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.apple.android.music/*.apk
```

## Verification

- `adb shell pm list packages | grep com.apple.android.music` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.apple.Music`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.apple.android.music   # only after explicit confirmation
```
