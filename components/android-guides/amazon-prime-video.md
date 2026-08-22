---
component_id: "android-amazon-prime-video"
name: "Amazon Prime Video"
category: "Media"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.amazon.avod.thirdpartyclient"
play_store_url: "https://play.google.com/store/apps/details?id=com.amazon.avod.thirdpartyclient"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Amazon Prime Video (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.amazon.avod.thirdpartyclient`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.amazon.avod.thirdpartyclient -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.amazon.avod.thirdpartyclient/*.apk
```

## Verification

- `adb shell pm list packages | grep com.amazon.avod.thirdpartyclient` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.amazon.aiv.AIVApp`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.amazon.avod.thirdpartyclient   # only after explicit confirmation
```
