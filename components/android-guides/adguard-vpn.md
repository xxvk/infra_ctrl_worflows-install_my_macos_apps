---
component_id: "android-adguard-vpn"
name: "AdGuard VPN"
category: "Developer tools"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.adguard.vpn"
play_store_url: "https://play.google.com/store/apps/details?id=com.adguard.vpn"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# AdGuard VPN (Android)

> [!summary] Purpose
> Core app synced from iOS catalog (2026-08). Play Store package `com.adguard.vpn`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.adguard.vpn -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.adguard.vpn/*.apk
```

## Verification

- `adb shell pm list packages | grep com.adguard.vpn` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.adguard.ios.AdGuardVPN`; see `references/cross-platform-app-map.json`.
