---
component_id: "dsh-npm-engine"
name: "@deepseek-ai/dsh"
category: "AI development"
tier: "core"
lifecycle_status: "active"
source: "npm_global"
delivery_method: "npm-global"
npm_global: "@deepseek-ai/dsh"
npm_version: "0.1.0-rc.7"
official_url: "https://github.com/deepseek-ai/deepseek-harness"
check_command: "fnm exec --using=24 dsh --version"
account_required: false
permissions_required: []
secrets_policy: "Never store API keys, tokens, or credentials here."
brew_formula: null
brew_cask: null
install_after: []
download_estimate_bytes: 117400
download_estimate_method: "npm_unpacked_size"
---

# @deepseek-ai/dsh

> [!summary] Purpose
> The complete DeepSeek Harness engine as a CLI: profile boot, plugin
> management, and the browser UI alias. Core runtime for all DeepSeek Harness
> profiles.

## Source

- npm: `@deepseek-ai/dsh` (0.1.0-rc.7, MIT, maintainers include DeepSeek
  official `tianyicui-deepseek`)
- Upstream: `https://github.com/deepseek-ai/deepseek-harness`
- bin: `dsh`

## Installation (fnm Node 24)

npm globals must install under the fnm Node 24 runtime, not the Homebrew Node:

```sh
fnm exec --using=24 npm install --global @deepseek-ai/dsh
fnm exec --using=24 dsh --version
```

## PATH / wrapper precedence

A local wrapper may exist at `~/.local/bin/dsh` pointing at the desktop app's
bundled CLI. The fnm global install places `dsh` under
`~/.local/share/fnm/node-versions/v24.19.0/installation/bin/`. For the npm
engine to take precedence, ensure the fnm bin directory is earlier on `PATH`
than `~/.local/bin` (or remove/rename the wrapper). Verify with `which dsh`.

## Follow-up and verification

- Verify `dsh` resolves under fnm Node 24 in a fresh login shell.
- Ensure the fnm global `dsh` takes precedence over any app wrapper.
- Run `dsh --profile web --dump-config` and verify the composed plugin tree.
- Keep the npm global prefix under the fnm Node 24 installation.

## Cleanup

```sh
fnm exec --using=24 npm uninstall --global @deepseek-ai/dsh
```

## Evidence and notes

- npm: `https://www.npmjs.com/package/@deepseek-ai/dsh`
- Machine-specific versions, paths, and verification results belong only in
  machine-local state.

Never paste a machine-local record, completed checkbox, or timestamp back
into this tracked guide.
