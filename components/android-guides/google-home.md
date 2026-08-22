---
component_id: "android-google-home"
name: "Google Home"
category: "Smart home"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.google.android.apps.chromecast.app"
play_store_url: "https://play.google.com/store/apps/details?id=com.google.android.apps.chromecast.app"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Google Home (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.google.android.apps.chromecast.app`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.google.android.apps.chromecast.app -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.google.android.apps.chromecast.app/*.apk
```

## Verification

- `adb shell pm list packages | grep com.google.android.apps.chromecast.app` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.google.android.apps.chromecast.app   # only after explicit confirmation
```
