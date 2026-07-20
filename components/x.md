---
component_id: "x"
name: "X"
category: "Social"
tier: "core"
lifecycle_status: "active"
source: "webcatalog"
delivery_method: "webcatalog-wrapper"
brew_cask: null
brew_formula: null
official_url: "https://x.com/"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 0
download_estimate_method: "catalog_size_gb_planning_estimate"
---

## macOS delivery

X is **WebCatalog-only** in this baseline. Reject native and Mac App Store
bundles, even if they launch. Create the wrapper for `https://x.com/` with
WebCatalog and store it under `~/Applications/WebCatalog Apps/`. Only after
the wrapper opens and is verified may the user approve removal of the legacy
`/Applications/X.app`. X-owned support data and caches are disposable and
must be removed during this cleanup; never delete the user's browser profile
or unrelated WebCatalog apps.

## Cleanup rule

After wrapper verification, remove the old X bundle and scan for X-specific
WebCatalog/Application Support, cache, and container directories. Record sizes
before deletion and remove those X-owned directories; do not retain login data
or cache for the retired copy.
