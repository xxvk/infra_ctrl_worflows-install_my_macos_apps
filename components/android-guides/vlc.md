---
component_id: "android-vlc"
name: "VLC"
category: "Media"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "org.videolan.vlc"
play_store_url: "https://play.google.com/store/apps/details?id=org.videolan.vlc"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# VLC (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `org.videolan.vlc`.

## Install (Play Store via apkeep)

```sh
apkeep -a org.videolan.vlc -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/org.videolan.vlc/*.apk
```

## Verification

- `adb shell pm list packages | grep org.videolan.vlc` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `org.videolan.vlc-ios`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall org.videolan.vlc   # only after explicit confirmation
```
