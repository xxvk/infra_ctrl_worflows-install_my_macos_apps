---
component_id: "ios-whatsapp"
name: "WhatsApp"
category: "Communication"
tier: "core"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "net.whatsapp.WhatsApp"
app_store_id: 310633997
app_store_url: "https://apps.apple.com/app/id310633997"
region_availability: []
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# WhatsApp (iOS)

> [!summary] Purpose
> v0 core app (purchase-history extraction, 2026-08). iOS bundle `net.whatsapp.WhatsApp`,
> App Store id `310633997`.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id310633997
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account/version.
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- See `references/cross-platform-app-map.json` for the Android equivalent.

## Cleanup

- Remove via the iPhone App Store (user action); never delete account data.
