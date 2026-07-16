---
component_id: "deno"
name: "deno"
category: "Developer CLI"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-formula"
brew_cask: null
brew_formula: "deno"
official_url: "https://deno.com/"
check_command: "deno"
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 100000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# deno

JavaScript/TypeScript runtime and toolchain. Install with `brew install deno`.

## Activation

No global activation is required. The Homebrew binary is already on `PATH`.
Verify with `deno --version`. Project permissions remain explicit; review any
`--allow-*` flags before running third-party code. Shell completions are
optional and should be added only after previewing the generated block.
