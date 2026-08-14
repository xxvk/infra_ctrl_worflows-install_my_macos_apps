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
official_url: "https://lmstudio.ai/download/bionic/latest/darwin/arm64"
check_command: null
install_after: []
account_required: true
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
---

# LM Studio Bionic

Bionic is a separate official LM Studio agent application. On Apple Silicon,
use the official endpoint above; it currently redirects to the signed
`Bionic-1.0.2-3-arm64.dmg` installer (the redirect may advance over time). Do not substitute the classic
`LM Studio.app` download.

## Local app name

Keep the official application bundle name. The current official bundle and
updater target is:

```text
Bionic.app
```

Do not rename it to `LM Bionic.app`: current in-app updates stage a signed
`Bionic.app` and fail to replace a renamed destination, leaving roughly one
extra app bundle in `~/.lmstudio/apps/bionic/.internal/staged-updates-app`.
After an update, verify the installed version and that this staging directory
returns to metadata-only size. Do not change the bundle identifier or internal
application metadata.

## Runtime conflict rule

Bionic and the classic LM Studio desktop app use the same `llmster` model
store/runtime components. They are not two independent local inference
runtimes. Do not run both local backends at the same time. If classic LM Studio reports that the daemon is
already running, keep Bionic open and quit the classic app instead.

The classic LM Studio app is retired in this catalog. Keep shared model data
until Bionic has been verified; do not delete `~/.lmstudio` automatically.

## Migration from classic LM Studio

1. Install and launch Bionic successfully.
2. Quit classic LM Studio and remove only `/Applications/LM Studio.app` (or
   uninstall its Homebrew cask).
3. Preserve `~/.lmstudio`; it contains shared models and runtime data.
4. Confirm `/Applications/Bionic.app` starts and can see the expected local model store before
   considering the migration complete.

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
