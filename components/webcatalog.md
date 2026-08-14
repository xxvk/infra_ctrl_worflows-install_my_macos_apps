---
component_id: "webcatalog"
name: "WebCatalog"
category: "Browser"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "webcatalog"
brew_formula: null
official_url: "https://webcatalog.io/"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 1000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# WebCatalog

WebCatalog creates separate desktop wrappers for web services. A wrapper's app
bundle, account/session data, and Chromium caches are distinct storage classes.
Removing an unused wrapper is preferable to deleting arbitrary shared
WebCatalog support data.

For an active wrapper, quit only that wrapper and preview its exact support
root. Cache, Code Cache, GPUCache, Dawn cache, and Service Worker cache may be
regenerable, but Cookies, Local Storage, IndexedDB, session files, and account
profiles must be preserved unless the user explicitly approves a sign-out/data
reset. Reopen the wrapper and verify the intended account and core page after
cache cleanup. Never apply one wrapper's path to every WebCatalog app.

Record exact paths, sizes, account read-back, and measured reclaim only in
machine-local state. Per-service exceptions belong in that component's guide.
