---
component_id: "android-hotpepper"
name: "ホットペッパー"
category: "Lifestyle"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "jp.co.recruit.hotpepperbeauty"
play_store_url: "https://play.google.com/store/apps/details?id=jp.co.recruit.hotpepperbeauty"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# ホットペッパー (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `jp.co.recruit.hotpepperbeauty`.

## Install (Play Store via apkeep)

```sh
apkeep -a jp.co.recruit.hotpepperbeauty -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/jp.co.recruit.hotpepperbeauty/*.apk
```

## Verification

- `adb shell pm list packages | grep jp.co.recruit.hotpepperbeauty` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `jp.co.recruit.mtl.beauty.salon`; see `references/cross-platform-app-map.json`.
