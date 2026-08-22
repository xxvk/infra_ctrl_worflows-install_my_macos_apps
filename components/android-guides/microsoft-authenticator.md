---
component_id: "android-microsoft-authenticator"
name: "Microsoft Authenticator"
category: "Security"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.azure.authenticator"
play_store_url: "https://play.google.com/store/apps/details?id=com.azure.authenticator"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Microsoft Authenticator (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.azure.authenticator`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.azure.authenticator -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.azure.authenticator/*.apk
```

## Verification

- `adb shell pm list packages | grep com.azure.authenticator` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.azure.authenticator   # only after explicit confirmation
```
