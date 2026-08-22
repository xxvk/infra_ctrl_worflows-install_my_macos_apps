---
component_id: "android-dポイントクラブ"
name: "dポイントクラブ"
category: "Finance"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "jp.docomo.dpoint"
play_store_url: "https://play.google.com/store/apps/details?id=jp.docomo.dpoint"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: true
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# dポイントクラブ (Android)

> [!summary] Purpose
> Japan-region core app (2026-08 user selection). Play Store package
> `jp.docomo.dpoint`. Requires a Japanese account.

## Install (Play Store via apkeep)

```sh
apkeep -a jp.docomo.dpoint -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/jp.docomo.dpoint/*.apk
```

## Verification

- `adb shell pm list packages | grep jp.docomo.dpoint` read-back.
- Launch on the Pixel and confirm the visible Japanese account.

## Cross-platform

- iOS equivalent: `com.nttdocomo.premierclub`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall jp.docomo.dpoint   # only after explicit confirmation
```
