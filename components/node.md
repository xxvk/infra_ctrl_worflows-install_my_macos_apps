---
component_id: "node"
name: "node"
category: "Developer CLI"
tier: "core"
lifecycle_status: "active"
source: "official_runtime_via_fnm"
delivery_method: "fnm-runtime"
brew_cask: null
brew_formula: null
official_url: "https://nodejs.org/en/download"
check_command: "fnm exec --using=24 node --version"
install_after: ["fnm"]
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 100000000
download_estimate_method: "catalog_size_gb_planning_estimate"
runtime_manager: "fnm"
runtime_version: "24"
---

# Node.js 24 LTS

Node 24 is the Core interactive development runtime. Install and select it
through fnm; do not activate nvm in the same shell startup path.

```sh
fnm install 24
fnm default 24
zsh -ic 'node --version; npm --version; command -v node; npm prefix -g'
```

The expected fresh-login result is Node major 24 with both `node` and npm's
global prefix under the fnm installation. Projects may still select another
version through an explicit local version file when that workflow is enabled.

Homebrew's unversioned `node` formula is a separate package-manager dependency.
Mermaid CLI, TypeScript, and Gemini CLI may bind directly to
`/opt/homebrew/opt/node/bin/node`; preserve that formula while
`brew uses --installed node` lists dependants. Do not relink `node@24` over it
or treat the Homebrew runtime version as the interactive baseline.

Before deleting an old fnm runtime, inspect its project references and global
packages. Runtime removal is a separate cleanup action.
