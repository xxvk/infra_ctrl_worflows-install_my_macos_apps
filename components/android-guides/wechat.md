---
component_id: "android-wechat"
name: "WeChat (Android)"
category: "Communication"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.tencent.mm"
play_store_url: "https://play.google.com/store/apps/details?id=com.tencent.mm"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: true
permissions_required: []
secrets_policy: "Never store WeChat account credentials, tokens, or chat content here."
install_after: []
---

# WeChat (Android)

> [!summary] Purpose
> Core communication app for the Pixel. iOS counterpart is `com.tencent.xin`;
> see `cross-platform-app-map.json`.

## Install (Play Store via apkeep)

```sh
# user provides a one-time OAuth/AAS token (never stored)
apkeep -a com.tencent.mm -d google-play -e '<user@example.com>' -t <aas_token> .
adb install --user 0 <downloaded>.apk
```

## Verification

- `adb shell pm list packages | grep com.tencent.mm` read-back.
- Launch on the Pixel and confirm the visible account matches.

## Cross-platform

- iOS: `com.tencent.xin` (App Store)
- macOS: catalog `WeChat` entry

## Cleanup

```sh
adb uninstall com.tencent.mm   # only after explicit confirmation; chat data is lost
```

## Evidence and notes

- Play Store package verified (HTTP 200).
- Machine-specific install state belongs in `Private/android-inventory.json`.
