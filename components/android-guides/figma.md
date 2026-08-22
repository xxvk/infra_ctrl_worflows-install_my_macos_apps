---
component_id: "android-figma"
name: "Figma"
category: "Developer tools"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.figma.mirror"
play_store_url: "https://play.google.com/store/apps/details?id=com.figma.mirror"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Figma (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.figma.mirror`. Android 为 Figma Mirror 查看器

## Install (Play Store via apkeep)

```sh
apkeep -a com.figma.mirror -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.figma.mirror/*.apk
```

## Verification

- `adb shell pm list packages | grep com.figma.mirror` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.figma.FigmaMirror`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.figma.mirror   # only after explicit confirmation
```
