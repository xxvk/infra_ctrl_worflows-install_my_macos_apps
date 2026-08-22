---
component_id: "android-line"
name: "LINE"
category: "Communication"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "jp.naver.line.android"
play_store_url: "https://play.google.com/store/apps/details?id=jp.naver.line.android"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# LINE (Android)

> [!summary] Purpose
> v0 core app mapped from the iOS catalog (2026-08). Play Store package
> `jp.naver.line.android`.

## Install (Play Store via apkeep)

```sh
apkeep -a jp.naver.line.android -d google-play -e '<user@example.com>' -t <aas_token> .
adb install --user 0 <downloaded>.apk
```

## Verification

- `adb shell pm list packages | grep jp.naver.line.android` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall jp.naver.line.android   # only after explicit confirmation
```
