---
component_id: "pnpm"
name: "pnpm"
category: "Developer CLI"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-formula"
brew_cask: null
brew_formula: "pnpm"
official_url: "https://pnpm.io/installation"
check_command: "fnm exec --using=24 pnpm --version"
install_after: ["node"]
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 20000000
download_estimate_method: "catalog_size_gb_planning_estimate"
cli_path: "/opt/homebrew/opt/pnpm"
---

# pnpm

> [!summary] Purpose
> Core JavaScript package client used by the Pi Agent stack. Homebrew owns the
> pnpm executable; fnm Node 24 owns the runtime and approved global binaries.

## Installation

```sh
brew install pnpm
fnm exec --using=24 pnpm --version
```

Do not run `pnpm setup` automatically because it edits shell startup files.
The repository installer instead resolves the fnm Node 24 global prefix and
sets `PNPM_HOME` only for each approved global transaction.

## Global package boundary

Every Core global package must pin an exact version and lifecycle policy. Use
`--ignore-scripts` when no build script is required, or one or more exact
`--allow-build=<package>` flags when a reviewed native dependency is required.
Never approve all builds or use an interactive global approval as reusable
installation authority.

Verify runtime ownership before use:

```sh
fnm exec --using=24 node --version
fnm exec --using=24 npm prefix --global
fnm exec --using=24 pnpm --version
```

## Rollback

Remove only the exact global package after reviewing its dependent tools.
Uninstall the Homebrew `pnpm` formula only when no retained component uses it.
