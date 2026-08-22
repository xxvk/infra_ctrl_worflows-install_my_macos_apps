---
component_id: "android-discord"
name: "Discord"
category: "Communication"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.discord"
play_store_url: "https://play.google.com/store/apps/details?id=com.discord"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Discord (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.discord`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.discord -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.discord/*.apk
```

## Verification

- `adb shell pm list packages | grep com.discord` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.hammerandchisel.discord`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.discord   # only after explicit confirmation
```
