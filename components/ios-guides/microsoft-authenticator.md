---
component_id: "ios-microsoft-authenticator"
name: "Microsoft Authenticator"
category: "Security"
tier: "core"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "com.microsoft.azureauthenticator"
app_store_id: 983156458
app_store_url: "https://apps.apple.com/app/id983156458"
region_availability: []
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Microsoft Authenticator (iOS)

> [!summary] Purpose
> core expansion 2026-08 (user selection). iOS bundle `com.microsoft.azureauthenticator`,
> App Store id `983156458`.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id983156458
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account/version.
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- Android equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

- Delete from the iPhone via the home-screen long-press flow (user action).
