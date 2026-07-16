---
component_id: "wordpress-studio-cli"
name: "WordPress Studio CLI"
category: "Web development CLI"
tier: "core"
lifecycle_status: "active"
source: "npm_global"
delivery_method: "npm-global"
brew_cask: null
brew_formula: null
official_url: "https://developer.wordpress.com/docs/developer-tools/studio/cli/"
check_command: "studio"
npm_package: "wp-studio"
install_after: []
account_required: true
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 50000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---

# WordPress Studio CLI

Core command-line companion for WordPress Studio. It manages local Studio
sites and supports account-backed workflows such as Studio Sync and previews.

## Installation

The preferred reproducible package installation is:

```sh
npm install --global wp-studio
studio --help
```

WordPress also provides an official installer script. Use it only when npm is
not suitable:

```sh
curl -fsSL https://wordpress.studio/install.sh | bash
```

Do not run both installation methods on the same Mac without first checking
which `studio` executable is active.

## Authentication and verification

```sh
command -v studio
studio --help
studio auth status
```

Run `studio auth login` interactively only when account-backed features are
needed. Never store the authentication token in this catalog or in a guide.

## Rollback

```sh
npm uninstall --global wp-studio
```
