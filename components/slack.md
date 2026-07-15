---
name: "Slack"
category: "Communication"
tier: core
status: installed
source: app_store
download_bytes: null
download_estimate_bytes: 1000000000
download_estimate_method: catalog_size_gb_planning_estimate
installed_bytes: 735780864
installed_version: "4.50.143"
installed_at: "2026-07-16"
secrets_policy: Never store passwords, API keys, recovery codes, or license secrets here.
---
om.tinyspeck.slackmacgap`
- App Store receipt present.
- User login verified before cleanup.

The old direct-download copy (`4.49.89`) was moved to the user's Trash after
the App Store copy was logged in and verified. Only one Slack app remains in
`/Applications`. The old direct-download data directory
`~/Library/Application Support/Slack` was then removed (about 461 MB). The
App Store sandbox data under
`~/Library/Containers/com.tinyspeck.slackmacgap` was preserved and Slack still
opened the logged-in workspace afterward.
