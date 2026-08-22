---
component_id: "android-revolut"
name: "Revolut"
category: "Finance"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.revolut.revolut"
play_store_url: "https://play.google.com/store/apps/details?id=com.revolut.revolut"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Revolut (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.revolut.revolut`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.revolut.revolut -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.revolut.revolut/*.apk
```

## Verification

- `adb shell pm list packages | grep com.revolut.revolut` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.revolut.revolut`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.revolut.revolut   # only after explicit confirmation
```
