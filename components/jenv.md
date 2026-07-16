---
component_id: "jenv"
name: "jenv"
category: "Developer CLI"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-formula"
brew_cask: null
brew_formula: "jenv"
official_url: "https://www.jenv.be/"
check_command: "jenv"
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 20000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# jenv

Java version manager. Install with `brew install jenv`; configure only the JDKs actually needed.

## Activation

Installation alone does not enable jenv. Add one idempotent block to `~/.zshrc`
after reviewing the existing Java setup:

```sh
export PATH="$HOME/.jenv/bin:$PATH"
eval "$(jenv init -)"
```

Then register only approved JDK installations with `jenv add`, inspect
`jenv versions`, and choose a global or per-project version deliberately.
Changing the default Java runtime requires separate confirmation.
