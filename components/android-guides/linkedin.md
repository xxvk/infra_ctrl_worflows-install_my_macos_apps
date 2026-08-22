---
component_id: "android-linkedin"
name: "LinkedIn"
category: "Communication"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.linkedin.android"
play_store_url: "https://play.google.com/store/apps/details?id=com.linkedin.android"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# LinkedIn (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.linkedin.android`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.linkedin.android -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.linkedin.android/*.apk
```

## Verification

- `adb shell pm list packages | grep com.linkedin.android` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.linkedin.android   # only after explicit confirmation
```
