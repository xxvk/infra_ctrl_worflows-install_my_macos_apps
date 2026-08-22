---
component_id: "utm"
name: "UTM"
category: "Virtualization"
tier: "optional"
lifecycle_status: "active"
source: "official_web"
delivery_method: "vendor-download"
brew_cask: "utm"
brew_formula: null
official_url: "https://mac.getutm.app/"
check_command: "test -d '/Applications/UTM.app'"
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store guest credentials, disk-image passphrases, or license secrets here."
download_estimate_bytes: 1180000000
download_estimate_method: "observed_installed_size"
---

# UTM

QEMU-based virtual machine host for Apple Silicon.

## Source boundary

Three sources deliver the same application under different terms: the free
website build, the Homebrew cask (`brew install --cask utm`), and a paid Mac
App Store build that funds development. They are not interchangeable for
licensing purposes — never silently substitute one for another, and never
automate a purchase.

## Storage

The bundle is roughly 1.1 GB, but guest disk images live **outside** it, under
the user's VM library. Account for them separately in any storage plan; a
capacity estimate based on the bundle alone will be wrong by an order of
magnitude on a machine with active VMs.

## Verification

```sh
test -d "/Applications/UTM.app"
defaults read "/Applications/UTM.app/Contents/Info" CFBundleShortVersionString
codesign --verify --deep --strict --verbose=2 "/Applications/UTM.app"
```

Never delete guest images, snapshots, or VM configuration during a generic Mac
cleanup scan.
