---
component_id: "slack"
name: "Slack"
category: "Communication"
tier: "core"
lifecycle_status: "active"
source: "app_store"
delivery_method: "app-store"
brew_cask: null
brew_formula: null
official_url: "https://slack.com/downloads/mac"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 1000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
he App Store copy was logged in and verified. Only one Slack app remains in
`/Applications`. The old direct-download data directory
`~/Library/Application Support/Slack` was then removed (about 461 MB). The
App Store sandbox data under
`~/Library/Containers/com.tinyspeck.slackmacgap` was preserved and Slack still
opened the logged-in workspace afterward.
