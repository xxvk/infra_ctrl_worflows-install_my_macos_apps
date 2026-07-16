---
component_id: "dbeaver-community"
name: "DBeaver Community"
category: "Developer tools"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "dbeaver-community"
brew_formula: null
official_url: "https://dbeaver.io/download/"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 1000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
all checklist

- Add database connections manually; do not store production credentials in this catalog.
- Download JDBC drivers only after reviewing the vendor URL and network policy.
- Keep local workspace metadata backed up if it contains connection definitions.
