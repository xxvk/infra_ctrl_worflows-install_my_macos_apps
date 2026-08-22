---
component_id: "pi-web"
name: "PI WEB"
category: "AI developer agent"
tier: "core"
lifecycle_status: "active"
source: "npm_global"
delivery_method: "pnpm-global"
brew_cask: null
brew_formula: null
official_url: "https://pi-web.dev/"
check_command: "fnm exec --using=24 pi-web version"
install_after: ["Pi Coding Agent"]
account_required: false
permissions_required: []
secrets_policy: "Never store remote-machine tokens, provider credentials, repository content, session content, or reverse-proxy secrets here."
download_estimate_bytes: 150000000
download_estimate_method: "catalog_size_gb_planning_estimate"
npm_package: "@jmfederico/pi-web"
npm_version: "1.202608.1"
npm_runtime_manager: "fnm"
npm_runtime_version: "24"
npm_install_client: "pnpm"
npm_lifecycle_policy: "allow_listed"
npm_allowed_builds: ["node-pty"]
---

# PI WEB

> [!summary] Purpose
> Core browser control surface for persistent Pi Coding Agent sessions in real
> repositories and worktrees. It keeps the runtime local and serves the UI on
> `http://127.0.0.1:8504` by default.

## Parameters

| Parameter | Value |
|---|---|
| Delivery | `pnpm-global` under fnm Node 24 |
| Package | `@jmfederico/pi-web@1.202608.1` |
| Pi compatibility | `@earendil-works/pi-coding-agent >=0.84.0` |
| Allowed build script | `node-pty` only |
| Executables | `pi-web`, `pi-web-server`, `pi-web-sessiond` |
| Default URL | `http://127.0.0.1:8504` |

## Package installation

Install Pi Coding Agent first and verify its exact version. pnpm v11 global
installs use `--allow-build`; do not copy npm's `--allow-scripts` flag and do
not approve all dependency scripts:

```sh
export PNPM_HOME="$(fnm exec --using=24 npm prefix --global)"
fnm exec --using=24 pnpm add --global --allow-build=node-pty \
  @jmfederico/pi-web@1.202608.1
fnm exec --using=24 pi-web version
```

`node-pty` supplies terminal support. Any newly requested lifecycle-script
package is source drift and requires a new review before installation.

## Per-user service configuration

Package installation and service creation are separate changes. Preview the
component and obtain explicit approval before running:

```sh
fnm exec --using=24 pi-web install
fnm exec --using=24 pi-web doctor
fnm exec --using=24 pi-web status
fnm exec --using=24 pi-web version
```

`pi-web install` creates native per-user services. Until a dedicated PI WEB
service adapter is registered in `mutation-contracts.json`, the skill may
inspect and prepare this command but the user executes it manually. Do not
describe package installation alone as a functioning PI WEB deployment.

## Verification

Require all of the following:

- `pi-web doctor` passes its Node, Pi, service and terminal checks.
- `pi-web status` reports the intended user services running.
- `pi-web version` matches the pinned package.
- `http://127.0.0.1:8504` opens locally and a disposable trusted project can
  create and resume one session.

Global user configuration belongs at `~/.config/pi-web/config.json`; managed
state defaults to `~/.pi-web`; project configuration belongs at
`<project>/.pi-web/config.json`. Preserve unknown settings and keep tokens out
of Git and diagnostics.

## Network boundary

PI WEB assumes trusted users, repositories and machine paths; it is not a
sandbox or multi-tenant security boundary. Keep the listener on `127.0.0.1`.
Never expose port 8504 directly to the public internet. Remote access requires
a separately reviewed private network, SSH tunnel, or authenticated reverse
proxy with its credentials outside this repository.

## Rollback

Stop and remove the user services before removing the package:

```sh
fnm exec --using=24 pi-web uninstall
export PNPM_HOME="$(fnm exec --using=24 npm prefix --global)"
fnm exec --using=24 pnpm remove --global @jmfederico/pi-web
```

Inspect and preserve `~/.pi-web`, `~/.config/pi-web`, sessions and project
configuration. Package rollback does not authorize deletion of those paths.

## Evidence and notes

- Website: `https://pi-web.dev/`
- Repository: `https://github.com/jmfederico/pi-web`
- Machine-specific services, ports, paths, sizes and health results belong
  only in machine-local state.
