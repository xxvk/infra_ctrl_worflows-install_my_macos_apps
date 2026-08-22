---
component_id: "android-zoom"
name: "Zoom"
category: "Communication"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "us.zoom.videomeetings"
play_store_url: "https://play.google.com/store/apps/details?id=us.zoom.videomeetings"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Zoom (Android)

> [!summary] Purpose
> v0 core app mapped from the iOS catalog (2026-08). Play Store package
> `us.zoom.videomeetings`.

## Install (Play Store via apkeep)

```sh
apkeep -a us.zoom.videomeetings -d google-play -e '<user@example.com>' -t <aas_token> .
adb install --user 0 <downloaded>.apk
```

## Verification

- `adb shell pm list packages | grep us.zoom.videomeetings` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall us.zoom.videomeetings   # only after explicit confirmation
```
