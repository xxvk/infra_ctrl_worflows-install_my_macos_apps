---
component_id: "android-ビューcard"
name: "ビューカード"
category: "Finance"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "jp.co.viewcard.app"
play_store_url: "https://play.google.com/store/apps/details?id=jp.co.viewcard.app"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# ビューカード (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `jp.co.viewcard.app`.

## Install (Play Store via apkeep)

```sh
apkeep -a jp.co.viewcard.app -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/jp.co.viewcard.app/*.apk
```

## Verification

- `adb shell pm list packages | grep jp.co.viewcard.app` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `jp.co.viewcard.viewcardapp.ios`; see `references/cross-platform-app-map.json`.
