---
component_id: "wechat"
name: "WeChat"
category: "Communication"
tier: "core"
lifecycle_status: "active"
source: "app_store"
delivery_method: "app-store"
brew_cask: null
brew_formula: null
official_url: "https://www.wechat.com/"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 1000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---

## Lifecycle adapter

The WeChat adapter in `settings/app-adapters.json` is metadata-only. It can
classify the declared container roots and report allocated storage without
reading messages, attachments, account data, or session data.

Use `./bin/macomrade scan adapters --adapter wechat` to create a machine-local
inspection record. Any storage reduction remains a visible, manual handoff to
WeChat's supported storage-management interface. Never delete WeChat
container data, message history, attachments, or unknown files generically.
