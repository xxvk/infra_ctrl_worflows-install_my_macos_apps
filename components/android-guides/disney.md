---
component_id: "android-disney"
name: "Disney+"
category: "Media"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.disney.disneyplus"
play_store_url: "https://play.google.com/store/apps/details?id=com.disney.disneyplus"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Disney+ (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.disney.disneyplus`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.disney.disneyplus -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.disney.disneyplus/*.apk
```

## Verification

- `adb shell pm list packages | grep com.disney.disneyplus` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.disney.disneyplus`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.disney.disneyplus   # only after explicit confirmation
```
