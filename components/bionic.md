---
component_id: "lm-studio-bionic"
name: "LM Studio Bionic"
category: "AI Agent"
tier: "core"
lifecycle_status: "active"
source: "official_web"
delivery_method: "vendor-download"
brew_cask: null
brew_formula: null
official_url: "https://lmstudio.ai/bionic"
check_command: null
install_after: []
account_required: true
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
---

# LM Studio Bionic

Bionic is the primary LM Studio application for this Mac. It is used for
agent-oriented work, local models, LM Link, and LM Studio Secure Cloud.

## Local app name

After installing the official Bionic app, rename the application bundle in
`/Applications` to:

```text
LM Bionic.app
```

This is a local organization rule only. Do not change the bundle identifier or
internal application metadata. Open the renamed app once and verify that macOS
launches it normally.

## Runtime conflict rule

Bionic and the classic LM Studio desktop app use the same `llmster` daemon.
They are not two independent local inference runtimes. Do not run both local
backends at the same time. If classic LM Studio reports that the daemon is
already running, keep Bionic open and quit the classic app instead.

The classic LM Studio app is retired in this catalog. Keep shared model data
until Bionic has been verified; do not delete `~/.lmstudio` automatically.

## Verification

- Open Bionic and verify local, LM Link, and Secure Cloud model routes as
  applicable.
- Confirm the selected route before sending private files or source code.
- For Secure Cloud, verify account, credits, network access, and billing before
  treating cloud inference as available.
- Record only route (`local`, `remote`, or `cloud`), model, feature, and
  pass/fail. Never store credentials or document contents.

## Retired classic app

The catalog entry for classic LM Studio is retained only to prevent accidental
reinstallation and to document the migration. If it is still installed, quit
both applications before removing the classic app bundle. Preserve shared
models and configuration unless the user explicitly requests cleanup.
