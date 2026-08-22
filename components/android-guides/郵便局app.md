---
component_id: "android-郵便局app"
name: "郵便局アプリ"
category: "Productivity"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "jp.jppost.pfapp"
play_store_url: "https://play.google.com/store/apps/details?id=jp.jppost.pfapp"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# 郵便局アプリ (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `jp.jppost.pfapp`.

## Install (Play Store via apkeep)

```sh
apkeep -a jp.jppost.pfapp -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/jp.jppost.pfapp/*.apk
```

## Verification

- `adb shell pm list packages | grep jp.jppost.pfapp` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `jp.jppost.pfapp`; see `references/cross-platform-app-map.json`.
