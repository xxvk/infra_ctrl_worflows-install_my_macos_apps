---
component_id: "google-design-md"
name: "@google/design.md"
category: "Developer tools"
tier: "core"
lifecycle_status: "active"
source: "npm_global"
delivery_method: "npm-global"
npm_global: "@google/design.md"
npm_version: "0.4.0"
official_url: "https://github.com/google-labs-code/design.md"
check_command: "fnm exec --using=24 design.md --version"
account_required: false
permissions_required: []
secrets_policy: "Never store credentials or tokens here."
install_after: []
brew_formula: null
brew_cask: null
download_estimate_bytes: 1600000
download_estimate_method: "npm_unpacked_size"
---

# @google/design.md

> [!summary] Purpose
> Google's official bridge between design systems and code: a linter and
> exporter for the `DESIGN.md` format. Provides `design.md` and `designmd`
> binaries.

## Source

- npm: `@google/design.md` (0.4.0, published 2026-07-27, maintainer
  `google-wombot` = Google official Node team)
- Upstream: `https://github.com/google-labs-code/design.md`
- License: Proprietary (Google)

## Installation (fnm Node 24)

npm globals must install under the fnm Node 24 runtime, not the Homebrew Node:

```sh
fnm exec --using=24 npm install --global @google/design.md
fnm exec --using=24 design.md --version
```

## Follow-up and verification

- Verify `design.md` resolves under fnm Node 24 in a fresh login shell.
- Run `design.md lint` on one `DESIGN.md` file and verify the output.
- Run `designmd export` and verify the exported artifact.
- Keep the npm global prefix under the fnm Node 24 installation.

## Cleanup

```sh
fnm exec --using=24 npm uninstall --global @google/design.md
```

## Evidence and notes

- npm: `https://www.npmjs.com/package/@google/design.md`
- Machine-specific versions, paths, and verification results belong only in
  machine-local state.

Never paste a machine-local record, completed checkbox, or timestamp back
into this tracked guide.
