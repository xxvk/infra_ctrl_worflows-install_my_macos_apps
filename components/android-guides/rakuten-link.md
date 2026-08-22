---
component_id: "android-rakuten-link"
name: "Rakuten Link"
category: "Communication"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "jp.co.rakuten.link"
play_store_url: "https://play.google.com/store/apps/details?id=jp.co.rakuten.link"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: true
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Rakuten Link (Android)

> [!summary] Purpose
> SIM/phone management for Rakuten Mobile (user selection 2026-08). Play Store package `jp.co.rakuten.link`.

## Install (Play Store via apkeep)

```sh
apkeep -a jp.co.rakuten.link -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/jp.co.rakuten.link/*.apk
```

## Verification

- `adb shell pm list packages | grep jp.co.rakuten.link` read-back.
- Launch and confirm the visible Rakuten account.

## Cross-platform

- iOS equivalent: `jp.co.rakuten.link`; see `references/cross-platform-app-map.json`.
