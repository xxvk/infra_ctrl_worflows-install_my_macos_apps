---
component_id: "ios-imovie"
name: "iMovie"
category: "Media"
tier: "core"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "com.apple.iMovie"
app_store_id: 377298193
app_store_url: "https://apps.apple.com/app/id377298193"
region_availability: []
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# iMovie (iOS)

> [!summary] Purpose
> Device inventory 2026-08, core tier. iOS bundle `com.apple.iMovie`, App Store id `377298193`.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id377298193
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account/version.
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- Android equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

- Delete from the iPhone via the home-screen long-press flow (user action).
