---
component_id: "android-paypal"
name: "PayPal"
category: "Finance"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.paypal.android.p2pmobile"
play_store_url: "https://play.google.com/store/apps/details?id=com.paypal.android.p2pmobile"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# PayPal (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.paypal.android.p2pmobile`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.paypal.android.p2pmobile -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.paypal.android.p2pmobile/*.apk
```

## Verification

- `adb shell pm list packages | grep com.paypal.android.p2pmobile` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.yourcompany.PPClient`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.paypal.android.p2pmobile   # only after explicit confirmation
```
