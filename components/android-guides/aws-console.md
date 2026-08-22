---
component_id: "android-aws-console"
name: "AWS Console"
category: "Developer tools"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.amazon.aws.console.mobile"
play_store_url: "https://play.google.com/store/apps/details?id=com.amazon.aws.console.mobile"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# AWS Console (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.amazon.aws.console.mobile`. iOS core 已有

## Install (Play Store via apkeep)

```sh
apkeep -a com.amazon.aws.console.mobile -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.amazon.aws.console.mobile/*.apk
```

## Verification

- `adb shell pm list packages | grep com.amazon.aws.console.mobile` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.amazon.aws.console.mobile   # only after explicit confirmation
```
