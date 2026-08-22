---
component_id: "android-aliexpress"
name: "AliExpress"
category: "Shopping"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.alibaba.aliexpresshd"
play_store_url: "https://play.google.com/store/apps/details?id=com.alibaba.aliexpresshd"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# AliExpress (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.alibaba.aliexpresshd`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.alibaba.aliexpresshd -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.alibaba.aliexpresshd/*.apk
```

## Verification

- `adb shell pm list packages | grep com.alibaba.aliexpresshd` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.alibaba.iAliexpress`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.alibaba.aliexpresshd   # only after explicit confirmation
```
