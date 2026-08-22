---
component_id: "android-ikea"
name: "IKEA"
category: "Shopping"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.ingka.ikea.app"
play_store_url: "https://play.google.com/store/apps/details?id=com.ingka.ikea.app"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# IKEA (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `com.ingka.ikea.app`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.ingka.ikea.app -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.ingka.ikea.app/*.apk
```

## Verification

- `adb shell pm list packages | grep com.ingka.ikea.app` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.ingka.ikea.app`; see `references/cross-platform-app-map.json`.
