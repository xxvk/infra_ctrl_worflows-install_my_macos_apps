---
component_id: "android-f-droid"
name: "F-Droid"
category: "Developer tools"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "org.fdroid.fdroid"
play_store_url: "https://play.google.com/store/apps/details?id=org.fdroid.fdroid"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# F-Droid (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `org.fdroid.fdroid`. 仅 Android

## Install (Play Store via apkeep)

```sh
apkeep -a org.fdroid.fdroid -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/org.fdroid.fdroid/*.apk
```

## Verification

- `adb shell pm list packages | grep org.fdroid.fdroid` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall org.fdroid.fdroid   # only after explicit confirmation
```
