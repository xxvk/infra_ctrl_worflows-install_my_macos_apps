---
component_id: "android-booking-com"
name: "Booking.com"
category: "Travel"
tier: "core"
lifecycle_status: "active"
source: "play_store"
play_store_package: "com.booking"
play_store_url: "https://play.google.com/store/apps/details?id=com.booking"
apk_source: "play_store"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Booking.com (Android)

> [!summary] Purpose
> core expansion 2026-08 (user selection). Play Store package
> `com.booking`.

## Install (Play Store via apkeep)

```sh
apkeep -a com.booking -d google-play -e '<user@example.com>' -t <aas_token> -o split_apk=true .
adb install-multiple <download-dir>/com.booking/*.apk
```

## Verification

- `adb shell pm list packages | grep com.booking` read-back.
- Launch on the Pixel and confirm the visible account.

## Cross-platform

- iOS equivalent: `com.booking.BookingApp`; see `references/cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.booking   # only after explicit confirmation
```
