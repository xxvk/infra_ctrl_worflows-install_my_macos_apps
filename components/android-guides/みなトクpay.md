---
component_id: "android-みなトクpay"
name: "みなトクPAY"
category: "Finance"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "jp.tokyo.minato.rsa"
play_store_url: "https://play.google.com/store/apps/details?id=jp.tokyo.minato.rsa"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# みなトクPAY (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `jp.tokyo.minato.rsa`.

## Install (Play Store via apkeep)

```sh
apkeep -a jp.tokyo.minato.rsa -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/jp.tokyo.minato.rsa/*.apk
```

## Verification

- `adb shell pm list packages | grep jp.tokyo.minato.rsa` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `jp.tokyo.minato.rsa`; see `references/cross-platform-app-map.json`.
