---
component_id: "android-qwen-studio"
name: "Qwen Studio"
category: "AI"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.alibaba.qwen"
play_store_url: "https://play.google.com/store/apps/details?id=com.alibaba.qwen"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Qwen Studio (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `com.alibaba.qwen`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.alibaba.qwen -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.alibaba.qwen/*.apk
```

## Verification

- `adb shell pm list packages | grep com.alibaba.qwen` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `ai.qwenlm.chat.ios`; see `references/cross-platform-app-map.json`.
