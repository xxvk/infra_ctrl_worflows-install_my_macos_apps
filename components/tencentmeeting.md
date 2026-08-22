---
component_id: "tencentmeeting"
name: "TencentMeeting"
category: "Communication"
tier: "optional"
lifecycle_status: "active"
source: "official_web"
delivery_method: "vendor-download"
brew_cask: null
brew_formula: null
official_url: "https://meeting.tencent.com/download/"
check_command: "test -d '/Applications/TencentMeeting.app'"
install_after: []
account_required: true
permissions_required: ["Camera", "Microphone", "Screen Recording"]
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 474000000
download_estimate_method: "observed_installed_size"
---

# TencentMeeting

Video conferencing client (腾讯会议). Download from the official site; there is
no reviewed Homebrew cask.

## Verification

```sh
test -d "/Applications/TencentMeeting.app"
defaults read "/Applications/TencentMeeting.app/Contents/Info" CFBundleShortVersionString
codesign --verify --deep --strict --verbose=2 "/Applications/TencentMeeting.app"
```

## Accounts and permissions

Sign-in is interactive. Never automate login or account switching. Camera,
microphone, and screen-recording grants are requested on first use and must be
approved by the user in System Settings; record them as unavailable rather than
denied when the TCC database cannot be read.
