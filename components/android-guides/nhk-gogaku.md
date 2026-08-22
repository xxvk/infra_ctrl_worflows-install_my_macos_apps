---
component_id: "android-nhk-gogaku"
name: "NHK gogaku"
category: "Learning"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "jp.or.nhk.gogaku"
play_store_url: "https://play.google.com/store/apps/details?id=jp.or.nhk.gogaku"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# NHK gogaku (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `jp.or.nhk.gogaku`.

## Install (Play Store via apkeep)

```sh
apkeep -a jp.or.nhk.gogaku -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/jp.or.nhk.gogaku/*.apk
```

## Verification

- `adb shell pm list packages | grep jp.or.nhk.gogaku` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `jp.or.nhk.gogaku`; see `references/cross-platform-app-map.json`.
