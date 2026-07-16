---
component_id: "fnm"
name: "fnm"
category: "Developer CLI"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-formula"
brew_cask: null
brew_formula: "fnm"
official_url: "https://github.com/Schniz/fnm"
check_command: "fnm"
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 20000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# fnm

Fast Node.js version manager. Install with `brew install fnm`; review shell integration before enabling it.

## Activation

`~/.zshrc` currently contains the recommended initializer:

```sh
eval "$(fnm env --use-on-cd)"
```

Open a fresh shell and verify `fnm --version`. The initializer may create
state under `~/.local/state/fnm_multishells`; if that directory is not writable,
fix ownership/permissions only after inspecting the cause. Do not duplicate the
initializer block.
