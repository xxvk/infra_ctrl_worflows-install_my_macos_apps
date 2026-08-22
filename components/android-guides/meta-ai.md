---
component_id: "android-meta-ai"
name: "Meta AI"
category: "AI"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.instagram.barcelona"
play_store_url: "https://play.google.com/store/apps/details?id=com.instagram.barcelona"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Meta AI (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.instagram.barcelona`. Play 上为 Meta AI / Instagram 内置

## Install (Play Store via apkeep)

```sh
apkeep -a com.instagram.barcelona -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.instagram.barcelona/*.apk
```

## Verification

- `adb shell pm list packages | grep com.instagram.barcelona` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.facebook.stellaapp`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.instagram.barcelona   # only after explicit confirmation
```
