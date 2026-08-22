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

Activate the default Node version in Zsh by adding exactly one labelled
initializer to `~/.zshrc`:

```sh
# macomrade: fnm Node version manager
eval "$(fnm env --shell zsh)"
```

In a fresh shell, install and select the shared baseline:

```sh
fnm install 24 --use
fnm default 24
node --version
```

`fnm env --use-on-cd` is optional: it reads `.node-version`, `.nvmrc`,
and supported `package.json` engine settings when changing directories. Do
not enable it for the global-stable baseline unless explicitly chosen, and do
not activate nvm in the same shell startup path.

Fnm may create
state under `~/.local/state/fnm_multishells`; if that directory is not writable,
fix ownership/permissions only after inspecting the cause. Do not duplicate the
initializer block.
