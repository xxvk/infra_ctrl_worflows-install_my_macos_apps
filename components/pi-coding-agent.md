---
component_id: "pi-coding-agent"
name: "Pi Coding Agent"
category: "AI developer agent"
tier: "core"
lifecycle_status: "active"
source: "npm_global"
delivery_method: "pnpm-global"
brew_cask: null
brew_formula: null
official_url: "https://github.com/earendil-works/pi"
check_command: "fnm exec --using=24 pi --version"
install_after: ["node", "pnpm"]
account_required: true
permissions_required: []
secrets_policy: "Never store provider API keys, OAuth tokens, subscription sessions, prompts, repository content, or agent credentials here."
download_estimate_bytes: 150000000
download_estimate_method: "catalog_size_gb_planning_estimate"
npm_package: "@earendil-works/pi-coding-agent"
npm_version: "0.84.2"
npm_runtime_manager: "fnm"
npm_runtime_version: "24"
npm_install_client: "pnpm"
npm_lifecycle_policy: "ignore_all"
---

# Pi Coding Agent

> [!summary] Purpose
> Core terminal coding agent and the runtime prerequisite for PI WEB. Pi runs
> tools in the current user account and trusted workspace; it is not an
> operating-system sandbox.

## Parameters

| Parameter | Value |
|---|---|
| Delivery | `pnpm-global` under fnm Node 24 |
| Package | `@earendil-works/pi-coding-agent@0.84.2` |
| Lifecycle scripts | all disabled with `--ignore-scripts` |
| Executable | `pi` |
| Install order | `node`, then `pnpm` |
| Account | provider or subscription authentication is interactive |

## Installation

Verify the registry version and integrity against `source-policy.json`. Bind
pnpm's global executable directory to the fnm runtime so Pi does not land in a
Homebrew Node or unrelated pnpm prefix:

```sh
export PNPM_HOME="$(fnm exec --using=24 npm prefix --global)"
fnm exec --using=24 pnpm add --global --ignore-scripts \
  @earendil-works/pi-coding-agent@0.84.2
```

The repository installer supplies the same runtime-scoped `PNPM_HOME` without
editing shell files. Never replace the exact version with `latest` during an
automated bootstrap. Package installation does not authorize provider login.

## Verification

```sh
fnm exec --using=24 node --version
fnm exec --using=24 pi --version
fnm exec --using=24 pi --help
```

Run one non-sensitive session only inside a trusted disposable repository.
Pi intentionally trusts local workspace instructions, extensions, and skills;
do not use that check against an unreviewed repository.

## Authentication and configuration

Start `pi` in a visible Terminal and use its interactive login flow only when
the intended provider or subscription is known. The user enters every secret.
Keep credentials and session state in Pi's user-owned storage, never in this
catalog, component guide, diagnostics, or Git.

Review each extension or Pi package separately. Installing the Core agent does
not authorize loading third-party extensions, exposing a remote endpoint, or
running it against untrusted source code.

## Rollback

Remove only the pinned global package after explicit approval:

```sh
export PNPM_HOME="$(fnm exec --using=24 npm prefix --global)"
fnm exec --using=24 pnpm remove --global @earendil-works/pi-coding-agent
```

Do not delete Pi sessions, authentication state, extensions, or project files
as part of package rollback. Inspect PI WEB first because it depends on Pi.

## Evidence and notes

- Registry: `https://registry.npmjs.org/`
- Repository: `https://github.com/earendil-works/pi`
- Machine-specific version, path, size, authentication and verification
  evidence belongs only in machine-local state.
