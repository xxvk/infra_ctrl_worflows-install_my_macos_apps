---
component_id: "playcover-learning-apps"
name: "PlayCover Learning Apps"
category: "Education"
tier: "option"
lifecycle_status: "active"
source: "manual"
delivery_method: "app-store-or-playcover-ipa"
brew_cask: null
brew_formula: null
official_url: "https://playcover.io/"
check_command: null
install_after: ["PlayCover"]
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
---
# PlayCover Learning Apps

These optional iPad/iPhone learning applications are retained inside
PlayCover. Keep them outside Core because they depend on PlayCover imports and
may require per-app IPA compatibility checks.

Current retained apps include Chinese vocabulary, exam-preparation, and date/
Japanese-learning tools. Do not remove or replace them during a generic Mac
cleanup scan.

## Source: App Store first, PlayCover only when required

On Apple Silicon many iPad/iPhone titles install natively from the App Store as
"Designed for iPad" builds and are **not** managed by PlayCover. The App Store
is the recommended source whenever it will deliver the title; reserve PlayCover
for titles the store will not install natively.

Both paths produce the same on-disk marker, so an `iTunesMetadata.plist`
receipt cannot distinguish them:

```text
/Applications/<Title>.app/Wrapper/iTunesMetadata.plist
```

Distinguish them by two other signals instead:

```sh
# native App Store (Designed for iPad): iOS signing authority, Wrapper only, no Contents
codesign -dv --verbose=2 "/Applications/<Title>.app" 2>&1 | grep Authority
#   -> Authority=Apple iPhone OS Application Signing

# PlayCover import: the bundle is registered under PlayCover's own directory
ls ~/Library/Containers/io.playcover.PlayCover/Applications/
```

A title absent from PlayCover's managed directory is a native App Store install
regardless of its receipt. Do not report such a title as a PlayCover
source mismatch, and do not "reinstall from the expected source" to resolve one
— confirm which path actually delivered the bundle first.

Acquiring these titles requires an Apple ID purchase or download. Never
automate sign-in, purchase, or account switching.
