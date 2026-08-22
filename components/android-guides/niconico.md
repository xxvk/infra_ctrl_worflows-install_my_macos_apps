---
component_id: "android-niconico"
name: "niconico"
category: "Media"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "jp.nicovideo.android"
play_store_url: "https://play.google.com/store/apps/details?id=jp.nicovideo.android"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# niconico (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `jp.nicovideo.android`.

## Install (Play Store via apkeep)

```sh
apkeep -a jp.nicovideo.android -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/jp.nicovideo.android/*.apk
```

## Verification

- `adb shell pm list packages | grep jp.nicovideo.android` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall jp.nicovideo.android   # only after explicit confirmation
```
