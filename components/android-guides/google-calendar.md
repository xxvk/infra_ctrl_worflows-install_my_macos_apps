---
component_id: "android-google-calendar"
name: "Google Calendar"
category: "Productivity"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.google.android.calendar"
play_store_url: "https://play.google.com/store/apps/details?id=com.google.android.calendar"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Google Calendar (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.google.android.calendar`. Pixel 预装

## Install (Play Store via apkeep)

```sh
apkeep -a com.google.android.calendar -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.google.android.calendar/*.apk
```

## Verification

- `adb shell pm list packages | grep com.google.android.calendar` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.google.android.calendar   # only after explicit confirmation
```
