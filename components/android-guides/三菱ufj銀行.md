---
component_id: "android-三菱ufj銀行"
name: "三菱UFJ銀行"
category: "Finance"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "jp.mufg.bk.applisp.app"
play_store_url: "https://play.google.com/store/apps/details?id=jp.mufg.bk.applisp.app"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: true
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# 三菱UFJ銀行 (Android)

> [!summary] Purpose
> Japan-region core app (2026-08 user selection). Play Store package
> `jp.mufg.bk.applisp.app`. Requires a Japanese account.

## Install (Play Store via apkeep)

```sh
apkeep -a jp.mufg.bk.applisp.app -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/jp.mufg.bk.applisp.app/*.apk
```

## Verification

- `adb shell pm list packages | grep jp.mufg.bk.applisp.app` read-back.
- Launch on the Pixel and confirm the visible Japanese account.

## Cross-platform

- iOS equivalent: `jp.mufg.bk.openaccount.app`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall jp.mufg.bk.applisp.app   # only after explicit confirmation
```
