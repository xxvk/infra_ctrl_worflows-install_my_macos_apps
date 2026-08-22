---
component_id: "android-x-(twitter)"
name: "X (Twitter)"
category: "Communication"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.twitter.android"
play_store_url: "https://play.google.com/store/apps/details?id=com.twitter.android"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# X (Twitter) (Android)

> [!summary] Purpose
> v0 core app mapped from the iOS catalog (2026-08). Play Store package
> `com.twitter.android`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.twitter.android -d google-play -e '<user@example.com>' -t <aas_token> .
adb install --user 0 <downloaded>.apk
```

## Verification

- `adb shell pm list packages | grep com.twitter.android` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.twitter.android   # only after explicit confirmation
```
