---
component_id: "android-world-app"
name: "World App"
category: "Finance"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "org.worldcoin.worldapp"
play_store_url: "https://play.google.com/store/apps/details?id=org.worldcoin.worldapp"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# World App (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `org.worldcoin.worldapp`.

## Install (Play Store via apkeep)

```sh
apkeep -a org.worldcoin.worldapp -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/org.worldcoin.worldapp/*.apk
```

## Verification

- `adb shell pm list packages | grep org.worldcoin.worldapp` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `org.worldcoin.insight`; see `references/cross-platform-app-map.json`.
