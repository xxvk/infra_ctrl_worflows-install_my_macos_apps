---
component_id: "android-starlink"
name: "Starlink"
category: "Smart home"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.starlink.mobile"
play_store_url: "https://play.google.com/store/apps/details?id=com.starlink.mobile"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Starlink (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `com.starlink.mobile`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.starlink.mobile -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.starlink.mobile/*.apk
```

## Verification

- `adb shell pm list packages | grep com.starlink.mobile` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.starlink.mobile`; see `references/cross-platform-app-map.json`.
