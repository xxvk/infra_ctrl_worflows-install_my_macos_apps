---
component_id: "antigravity-cli"
name: "Antigravity CLI"
category: "Developer CLI"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "antigravity-cli"
brew_formula: null
official_url: "https://antigravity.google/product/antigravity-cli"
check_command: "agy"
install_after: []
account_required: true
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
cli_path: "/opt/homebrew/bin/agy"
---
# Antigravity CLI (`agy`)

> [!summary] Purpose
> Google Antigravity's terminal interface for agent workflows. This is the replacement path for the retired Homebrew `gemini-cli` package.

## Parameters

| Parameter | Value |
|---|---|
| Delivery | Homebrew cask |
| Package identifier | `antigravity-cli` |
| Official source | https://antigravity.google/product/antigravity-cli |
| Required tier | core |
| Install order | none |
| CLI command | `agy` |
| Account needed | yes, interactive only |
| Permissions | Review any requested workspace or code-access permissions |

## Installation

```sh
brew install --cask antigravity-cli
```

Homebrew currently publishes version `1.1.3,5723946948100096` and links the `antigravity` binary as `agy`.

## Configuration

Run sign-in or credential setup interactively when prompted. Never store tokens, passwords, recovery codes, or API keys in this guide, the catalog, or state logs.

## Verification

```sh
command -v agy
agy --version
```

- [ ] Confirm the binary is on PATH.
- [ ] Confirm the version output.
- [ ] Complete account sign-in yourself if required.
- [ ] Confirm the CLI can access only the intended workspace and repositories.

## Replacement procedure

Install and verify `agy` first. Only then retire and remove `gemini-cli`:

```sh
brew uninstall gemini-cli
```

Record the uninstall evidence in `state/`; do not delete the old CLI before the replacement passes verification.

## Rollback

To restore the previous CLI, reverse the lifecycle change in the catalog and reinstall its verified formula:

```sh
brew install gemini-cli
```

## Evidence and notes

- Homebrew availability checked 2026-07-16.
- `gemini-cli` is marked `lifecycle_status: retired` in the catalog after this replacement is verified.
