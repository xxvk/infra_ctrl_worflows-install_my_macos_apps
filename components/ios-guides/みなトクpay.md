---
component_id: "ios-みなトクpay"
name: "みなトクPAY"
category: "Japan life"
tier: "core"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "jp.tokyo.minato.rsa"
app_store_id: 6502482755
app_store_url: "https://apps.apple.com/app/id6502482755"
region_availability: ["JP"]
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# みなトクPAY (iOS)

> [!summary] Purpose
> Device inventory 2026-08, core tier. iOS bundle `jp.tokyo.minato.rsa`, App Store id `6502482755`.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id6502482755
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account/version.
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- Android equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

- Delete from the iPhone via the home-screen long-press flow (user action).
