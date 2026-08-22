---
component_id: "android-ヤマトtransport"
name: "ヤマト運輸"
category: "Lifestyle"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "jp.co.kuronekoyamato.kuronekoyamato"
play_store_url: "https://play.google.com/store/apps/details?id=jp.co.kuronekoyamato.kuronekoyamato"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# ヤマト運輸 (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `jp.co.kuronekoyamato.kuronekoyamato`.

## Install (Play Store via apkeep)

```sh
apkeep -a jp.co.kuronekoyamato.kuronekoyamato -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/jp.co.kuronekoyamato.kuronekoyamato/*.apk
```

## Verification

- `adb shell pm list packages | grep jp.co.kuronekoyamato.kuronekoyamato` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `jp.co.kuronekoyamato.KuronekoyamatoOfficialApp`; see `references/cross-platform-app-map.json`.
