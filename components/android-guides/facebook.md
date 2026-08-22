---
component_id: "android-facebook"
name: "Facebook"
category: "Communication"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.facebook.katana"
play_store_url: "https://play.google.com/store/apps/details?id=com.facebook.katana"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Facebook (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.facebook.katana`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.facebook.katana -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.facebook.katana/*.apk
```

## Verification

- `adb shell pm list packages | grep com.facebook.katana` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.facebook.Facebook`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.facebook.katana   # only after explicit confirmation
```
