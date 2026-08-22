---
component_id: "android-iaeon"
name: "iAEON"
category: "Finance"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.aeonmy.myaeon"
play_store_url: "https://play.google.com/store/apps/details?id=com.aeonmy.myaeon"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: true
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# iAEON (Android)

> [!summary] Purpose
> Japan-region core app (2026-08 user selection). Play Store package
> `com.aeonmy.myaeon`. Requires a Japanese account.

## Install (Play Store via apkeep)

```sh
apkeep -a com.aeonmy.myaeon -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.aeonmy.myaeon/*.apk
```

## Verification

- `adb shell pm list packages | grep com.aeonmy.myaeon` read-back.
- Launch on the Pixel and confirm the visible Japanese account.

## Cross-platform

- iOS equivalent: `com.aeonmy.myaeon`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.aeonmy.myaeon   # only after explicit confirmation
```
