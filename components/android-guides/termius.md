---
component_id: "android-termius"
name: "Termius"
category: "Developer tools"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.server.auditor.ssh.client"
play_store_url: "https://play.google.com/store/apps/details?id=com.server.auditor.ssh.client"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Termius (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.server.auditor.ssh.client`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.server.auditor.ssh.client -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.server.auditor.ssh.client/*.apk
```

## Verification

- `adb shell pm list packages | grep com.server.auditor.ssh.client` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.server.auditor.ssh.client   # only after explicit confirmation
```
