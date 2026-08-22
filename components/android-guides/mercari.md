---
component_id: "android-mercari"
name: "メルカリ（Mercari 日本版）"
category: "Shopping"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.kouzoh.mercari"
play_store_url: "https://play.google.com/store/apps/details?id=com.kouzoh.mercari"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# メルカリ / Mercari JP (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.kouzoh.mercari` -- this is the **Japanese** build.
>
> [!warning] Do not confuse with the US build
> `com.mercariapp.mercari` is Mercari **US**. It was side-loaded onto the Pixel
> on 2026-08-21 (`installerPackageName=null`, `en`-only splits), never signed
> in, and uninstalled at the user's request on 2026-08-22. The JP build carries
> `ja`/`zh` splits and installs from the Play Store. Same trap exists on iOS:
> `com.mercariapp.ios.mercari` (wrong) vs `com.kouzoh.ios.mercari` (correct).

## Install (Play Store via apkeep)

```sh
apkeep -a com.kouzoh.mercari -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.kouzoh.mercari/*.apk
```

## Verification

- `adb shell pm list packages | grep com.kouzoh.mercari` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.kouzoh.mercari   # only after explicit confirmation
```
