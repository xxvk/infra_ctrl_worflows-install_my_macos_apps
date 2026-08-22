---
component_id: "android-coursera"
name: "Coursera"
category: "Learning"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "org.coursera.android"
play_store_url: "https://play.google.com/store/apps/details?id=org.coursera.android"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Coursera (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `org.coursera.android`.

## Install (Play Store via apkeep)

```sh
apkeep -a org.coursera.android -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/org.coursera.android/*.apk
```

## Verification

- `adb shell pm list packages | grep org.coursera.android` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `org.coursera.coursera`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall org.coursera.android   # only after explicit confirmation
```
