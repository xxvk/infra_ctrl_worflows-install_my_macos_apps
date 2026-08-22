---
component_id: "android-canva"
name: "Canva"
category: "Media"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.canva.editor"
play_store_url: "https://play.google.com/store/apps/details?id=com.canva.editor"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Canva (Android)

> [!summary] Purpose
> v0 core app mapped from the iOS catalog (2026-08). Play Store package
> `com.canva.editor`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.canva.editor -d google-play -e '<user@example.com>' -t <aas_token> .
adb install --user 0 <downloaded>.apk
```

## Verification

- `adb shell pm list packages | grep com.canva.editor` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.canva.editor   # only after explicit confirmation
```
