---
component_id: "npm"
name: "npm"
category: "Developer CLI"
tier: "core"
lifecycle_status: "active"
source: "bundled_with_node"
delivery_method: "bundled-fnm-runtime"
brew_cask: null
brew_formula: null
official_url: "https://docs.npmjs.com/downloading-and-installing-node-js-and-npm"
check_command: "fnm exec --using=24 npm --version"
install_after: ["node"]
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 0
download_estimate_method: "catalog_size_gb_planning_estimate"
runtime_manager: "fnm"
runtime_version: "24"
---

# npm

npm is bundled with the fnm-managed Node 24 Core runtime. It is not installed
as a separate Homebrew formula.

Verify ownership before any global installation:

```sh
fnm exec --using=24 node --version
fnm exec --using=24 npm --version
fnm exec --using=24 npm prefix -g
```

Core npm-global packages must be installed through an explicit runtime:

```sh
fnm exec --using=24 npm install --global <package>@<exact-version>
```

Do not use a bare `npm install --global` in automation. It can write into a
Homebrew, fnm, nvm, or system prefix depending on the caller's PATH. Existing
packages under `/opt/homebrew/lib/node_modules` remain untouched until each is
reinstalled under Node 24, verified, and separately approved for cleanup.
