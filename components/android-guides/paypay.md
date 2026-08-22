---
component_id: "android-paypay"
name: "PayPay"
category: "Finance"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "jp.ne.paypay.android.app"
play_store_url: "https://play.google.com/store/apps/details?id=jp.ne.paypay.android.app"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# PayPay (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `jp.ne.paypay.android.app`.

## Install (Play Store via apkeep)

```sh
apkeep -a jp.ne.paypay.android.app -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/jp.ne.paypay.android.app/*.apk
```

## Verification

- `adb shell pm list packages | grep jp.ne.paypay.android.app` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.smart.paypay`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall jp.ne.paypay.android.app   # only after explicit confirmation
```
