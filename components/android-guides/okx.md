---
component_id: "android-okx"
name: "OKX"
category: "Finance"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.okinc.okex.gp"
play_store_url: "https://play.google.com/store/apps/details?id=com.okinc.okex.gp"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# OKX (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.okinc.okex.gp`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.okinc.okex.gp -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.okinc.okex.gp/*.apk
```

## Verification

- `adb shell pm list packages | grep com.okinc.okex.gp` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.okinc.okex.gp   # only after explicit confirmation
```
