---
component_id: "android-uber"
name: "Uber"
category: "Travel"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.ubercab"
play_store_url: "https://play.google.com/store/apps/details?id=com.ubercab"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Uber (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.ubercab`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.ubercab -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.ubercab/*.apk
```

## Verification

- `adb shell pm list packages | grep com.ubercab` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.ubercab.UberClient`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.ubercab   # only after explicit confirmation
```
