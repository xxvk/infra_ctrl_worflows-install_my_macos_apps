---
component_id: "ios-booking-com"
name: "Booking.com"
category: "Travel"
tier: "optional"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "com.booking.BookingApp"
app_store_id: 367003839
app_store_url: "https://apps.apple.com/app/id367003839"
region_availability: []
account_required: false
permissions_required: []
secrets_policy: "Never store account credentials, tokens, or private content here."
install_after: []
---

# Booking.com (iOS)

> [!summary] Purpose
> core expansion 2026-08 (user selection). iOS bundle `com.booking.BookingApp`,
> App Store id `367003839`.

## Install (App Store)

Open the canonical URL and continue serially (user completes Apple ID flow):

```text
macappstore://itunes.apple.com/app/id367003839
```

Opening the page is not installation evidence.

## Verification

- Launch on the iPhone and confirm the visible account/version.
- Record state in machine-local or `Private/ios-inventory.json`.

## Cross-platform

- Android equivalent: see `references/cross-platform-app-map.json`.

## Cleanup

- Delete from the iPhone via the home-screen long-press flow (user action).
