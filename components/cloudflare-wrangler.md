---
component_id: "cloudflare-wrangler"
name: "Cloudflare Wrangler"
category: "Cloud CLI"
tier: "core"
lifecycle_status: "active"
source: "official_web"
delivery_method: "npm-global"
brew_cask: null
brew_formula: null
official_url: "https://developers.cloudflare.com/workers/wrangler/install/"
check_command: "wrangler"
install_after: []
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
npm_package: "wrangler"
---
# Cloudflare Wrangler

Cloudflare's official CLI for developing, testing, and deploying Workers and
related Cloudflare resources.

## Installation

The official installation path is a global npm package. Homebrew does not
provide the installation source used by this catalog entry.

```sh
npm install --global wrangler
wrangler --version
```

The skill may automate the package installation, but authentication remains
interactive and must never be recorded in the catalog.

## Verification

```sh
command -v wrangler
wrangler --version
wrangler whoami
```

Run `wrangler login` interactively only when a Cloudflare account is needed.
Confirm the intended account and active project before deployment.

## Rollback

```sh
npm uninstall --global wrangler
```
