---
component_id: "android-suica"
name: "Suica"
category: "Finance"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.mobilesuica.msb.android"
play_store_url: "https://play.google.com/store/apps/details?id=com.mobilesuica.msb.android"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Suica (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.mobilesuica.msb.android`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.mobilesuica.msb.android -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.mobilesuica.msb.android/*.apk
```

## Verification

- `adb shell pm list packages | grep com.mobilesuica.msb.android` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.mobilesuica.msb.android   # only after explicit confirmation
```
