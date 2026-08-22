---
component_id: "android-nanaco"
name: "nanaco"
category: "Finance"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "jp.co.nanaco.app"
play_store_url: "https://play.google.com/store/apps/details?id=jp.co.nanaco.app"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: true
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# nanaco (Android)

> [!summary] Purpose
> Japan-region core app (2026-08 user selection). Play Store package
> `jp.co.nanaco.app`. Requires a Japanese account.

## Install (Play Store via apkeep)

```sh
apkeep -a jp.co.nanaco.app -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/jp.co.nanaco.app/*.apk
```

## Verification

- `adb shell pm list packages | grep jp.co.nanaco.app` read-back.
- Launch on the Pixel and confirm the visible Japanese account.

## Cross-platform

- iOS equivalent: `jp.nanaco-net.mobile.app`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall jp.co.nanaco.app   # only after explicit confirmation
```
