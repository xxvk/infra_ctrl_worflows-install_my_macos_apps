---
component_id: "redis-cli"
name: "Redis CLI"
category: "Developer CLI"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-formula"
brew_cask: null
brew_formula: "redis"
official_url: "https://redis.io/docs/latest/develop/tools/cli/"
check_command: "redis-cli --version"
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 50000000
download_estimate_method: "homebrew_formula_planning_estimate"
---

# Redis CLI

Redis CLI is the Core command-line interface for inspecting and operating
local or remote Redis databases. Homebrew delivers `redis-cli` through the
`redis` formula, which also contains `redis-server`; installing the formula
does not authorize starting or enabling the local server service.

## Installation

Dry-run through the catalog first, then apply only after approval. The direct
package-manager equivalent is:

```sh
HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_UPGRADE=1 brew install redis
```

Do not run `brew services start redis` unless the user separately requests a
local Redis server. The CLI can connect directly to an existing remote server.

## Verification

```sh
command -v redis-cli
redis-cli --version
brew services list | grep '^redis[[:space:]]'
```

The binary and version checks must pass. The service check should report no
started Redis service for the default Core installation.

Use `REDISCLI_AUTH` or another user-controlled secret mechanism for
authentication; never put a password, token, or credential-bearing Redis URI
in this guide, tracked configuration, shell history, or machine-local evidence.

## Rollback

`brew uninstall redis` removes the Homebrew CLI and server binaries. It does
not delete data on any remote Redis instance. Review any explicitly created
local Redis configuration or database files separately before removing them.
