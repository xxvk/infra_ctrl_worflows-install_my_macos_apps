---
component_id: "ios-wechat"
name: "WeChat (iOS)"
category: "Communication"
tier: "core"
lifecycle_status: "active"
source: "app_store"
ios_bundle_id: "com.tencent.xin"
app_store_id: 414478124
app_store_url: "https://apps.apple.com/app/id414478124"
region_availability: []
account_required: true
permissions_required: []
secrets_policy: "Never store WeChat account credentials, tokens, or chat content here."
install_after: []
---

# WeChat (iOS)

> [!summary] Purpose
> Core communication app. iOS counterpart of the macOS WeChat catalog entry;
> Android counterpart is `com.tencent.mm` (see `cross-platform-app-map.json`).

## Install (App Store)

Open the canonical App Store URL and continue serially (the user completes the
Apple ID flow; never automate login):

```text
macappstore://itunes.apple.com/app/id414478124
```

Opening the page is not installation evidence.

## Verification

- Launch WeChat on the iPhone and confirm the visible account matches the
  intended one.
- Record version/account/installation state in machine-local state or
  `Private/ios-inventory.json`; never here.

## Cross-platform

- Android: `com.tencent.mm` (Play Store)
- macOS: catalog `WeChat` entry

## Cleanup

- Remove via the iPhone App Store (user action); never delete chat history or
  account data as part of cleanup.
