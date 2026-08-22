---
component_id: "android-youtube-music"
name: "YouTube Music"
category: "Media"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.google.android.apps.youtube.music"
play_store_url: "https://play.google.com/store/apps/details?id=com.google.android.apps.youtube.music"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# YouTube Music (Android)

> [!summary] Purpose
> v0 core app mapped from the iOS catalog (2026-08). Play Store package
> `com.google.android.apps.youtube.music`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.google.android.apps.youtube.music -d google-play -e '<user@example.com>' -t <aas_token> .
adb install --user 0 <downloaded>.apk
```

## Verification

- `adb shell pm list packages | grep com.google.android.apps.youtube.music` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.google.android.apps.youtube.music   # only after explicit confirmation
```
