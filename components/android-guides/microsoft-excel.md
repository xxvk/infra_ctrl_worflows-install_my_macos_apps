---
component_id: "android-microsoft-excel"
name: "Microsoft Excel"
category: "Communication"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.microsoft.office.excel"
play_store_url: "https://play.google.com/store/apps/details?id=com.microsoft.office.excel"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Microsoft Excel (Android)

> [!summary] Purpose
> v0 core app mapped from the iOS catalog (2026-08). Play Store package
> `com.microsoft.office.excel`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.microsoft.office.excel -d google-play -e '<user@example.com>' -t <aas_token> .
adb install --user 0 <downloaded>.apk
```

## Verification

- `adb shell pm list packages | grep com.microsoft.office.excel` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.microsoft.office.excel   # only after explicit confirmation
```
