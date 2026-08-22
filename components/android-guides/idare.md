---
component_id: "android-idare"
name: "IDARE"
category: "Lifestyle"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "jp.co.fivot.idare"
play_store_url: "https://play.google.com/store/apps/details?id=jp.co.fivot.idare"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# IDARE (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `jp.co.fivot.idare`.

## Install (Play Store via apkeep)

```sh
apkeep -a jp.co.fivot.idare -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/jp.co.fivot.idare/*.apk
```

## Verification

- `adb shell pm list packages | grep jp.co.fivot.idare` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `jp.co.fivot.idare`; see `references/cross-platform-app-map.json`.
