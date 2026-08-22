---
component_id: "android-eight"
name: "Eight"
category: "Productivity"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "net.8card.eight"
play_store_url: "https://play.google.com/store/apps/details?id=net.8card.eight"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Eight (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `net.8card.eight`.

## Install (Play Store via apkeep)

```sh
apkeep -a net.8card.eight -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/net.8card.eight/*.apk
```

## Verification

- `adb shell pm list packages | grep net.8card.eight` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `net.8card.eight`; see `references/cross-platform-app-map.json`.
