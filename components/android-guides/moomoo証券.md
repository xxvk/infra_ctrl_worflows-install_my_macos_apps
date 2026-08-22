---
component_id: "android-moomoo証券"
name: "moomoo証券"
category: "Finance"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.futunn.futu"
play_store_url: "https://play.google.com/store/apps/details?id=com.futunn.futu"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# moomoo証券 (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `com.futunn.futu`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.futunn.futu -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.futunn.futu/*.apk
```

## Verification

- `adb shell pm list packages | grep com.futunn.futu` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.moomoo.mm`; see `references/cross-platform-app-map.json`.
