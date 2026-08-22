---
component_id: "android-yahoonorikae"
name: "Yahoo!乗換案内"
category: "Travel"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "jp.co.yahoo.android.apps.transit"
play_store_url: "https://play.google.com/store/apps/details?id=jp.co.yahoo.android.apps.transit"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Yahoo!乗換案内 (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `jp.co.yahoo.android.apps.transit`.

## Install (Play Store via apkeep)

```sh
apkeep -a jp.co.yahoo.android.apps.transit -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/jp.co.yahoo.android.apps.transit/*.apk
```

## Verification

- `adb shell pm list packages | grep jp.co.yahoo.android.apps.transit` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall jp.co.yahoo.android.apps.transit   # only after explicit confirmation
```
