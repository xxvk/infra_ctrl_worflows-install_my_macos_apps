---
component_id: "ios-link-to-windows"
name: "Link to Windows"
category: "Productivity"
tier: "optional"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "com.microsoft.LinkToWindows"
app_store_id: 6443686328
app_store_url: "https://apps.apple.com/app/id6443686328"
region_availability: []
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Link to Windows (iOS)

> [!summary] Purpose
> Device inventory 2026-08, optional tier. iOS bundle `com.microsoft.LinkToWindows`, App Store id `6443686328`.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id6443686328
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account/version.
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- Android equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

- Delete from the iPhone via the home-screen long-press flow (user action).
