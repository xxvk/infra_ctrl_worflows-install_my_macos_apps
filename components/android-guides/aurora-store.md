---
component_id: "android-aurora-store"
name: "Aurora Store"
category: "Developer tools"
tier: "core"
lifecycle_status: "active"
source: "fdroid"
play_store_package: "com.aurora.store"
play_store_url: "https://f-droid.org/packages/com.aurora.store/"
apk_source: "fdroid"
supported_abis: ["arm64-v8a"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Aurora Store (Android)

> [!summary] Purpose
> Alternative Play Store client: anonymous app browsing/download, plus a token
> dispenser that can mint auth tokens for `apkeep`. **Not distributed on
> Google Play** — the Play listing is a stale/unofficial upload rejected by
> modern devices ("device not supported"); always use F-Droid / IzzyOnDroid /
> GitLab / APKMirror.

## Install (F-Droid via apkeep)

```sh
apkeep -a com.aurora.store -d f-droid .
adb install -r -g com.aurora.store.apk
```

Verified: Aurora Store 4.8.4 (versionCode 76, minSdk 23 / targetSdk 37) on
Pixel 11 / Android 17, installed 2026-08-21.

## Verification

- `adb shell pm list packages | grep com.aurora.store` read-back.
- Launch; first run offers Anonymous login (no Google account needed) or your
  own account. Anonymous mode can still download public apps.

## Token dispenser for apkeep

Aurora Store can produce a short-lived auth token (`ya29...`) usable with
`apkeep -d google-play --auth-token <token>` — an alternative to the
Safari `oauth_token` flow. Tokens are one-time/short-lived; never store them.

## Cross-platform

- No iOS/macOS equivalent; Android-only utility (iOS App Store has no
  alternative-store client). Not in `cross-platform-app-map.json`.

## Cleanup

```sh
adb uninstall com.aurora.store   # only after explicit confirmation
```
