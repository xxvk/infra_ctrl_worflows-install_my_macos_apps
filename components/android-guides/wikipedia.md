---
component_id: "android-wikipedia"
name: "Wikipedia"
category: "Learning"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "org.wikipedia"
play_store_url: "https://play.google.com/store/apps/details?id=org.wikipedia"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Wikipedia (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `org.wikipedia`.

## Install (Play Store via apkeep)

```sh
apkeep -a org.wikipedia -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/org.wikipedia/*.apk
```

## Verification

- `adb shell pm list packages | grep org.wikipedia` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `org.wikimedia.wikipedia`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall org.wikipedia   # only after explicit confirmation
```
