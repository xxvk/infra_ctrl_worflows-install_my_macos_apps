---
component_id: "cursor-agent"
name: "Cursor Agent"
category: "AI developer agent"
tier: "core"
lifecycle_status: "active"
source: "official_web"
delivery_method: "shell-script"
brew_cask: null
brew_formula: null
official_url: "https://cursor.com/install"
check_command: "cursor-agent --version"
install_after: []
account_required: true
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
---

# Cursor Agent

> [!summary] Purpose
> Headless CLI agent for Cursor, heavily used as a driver for Open Design workflows.

## Parameters

| Parameter | Value |
|---|---|
| Delivery | `shell-script` |
| Package identifier | `cursor-agent` |
| Official source | `https://cursor.com/install` |
| Required tier | `core` |
| Install order | `none` |
| Expected download | `unknown` |
| Expected installed size | `unknown` |
| Config path(s) | `none` |
| Account needed | `yes` |
| Permissions | `none` |

## Installation

- [ ] Confirm the app is missing from the latest scan.
- [ ] Run the official installation script.
- [ ] Obtain explicit approval before download or installation.
- [ ] Record `download_bytes`, `installed_bytes`, detected version, paths, timestamps, and pass/fail only in the machine-local install record.

### Command or user action

```sh
curl https://cursor.com/install -fsS | bash
```

## Configuration

- [ ] Authenticate with Cursor.
- [ ] Run `cursor-agent login`.
- [ ] Follow the browser link to complete authentication.

### Known Limitations (Open Design)
- **Quota & Usage Limits**: Free Hobby users do not have a fixed number of requests. Usage is dynamically metered based on Token size and request complexity (context length, files read).
- **Exceeding Limits**: Once the free quota is exhausted, the service does **not** degrade to slower or smaller models; instead, advanced AI features (Agent, Composer) are strictly **blocked** (`Usage limit exceeded`) until the next monthly billing cycle or an upgrade to the Pro plan.
- **Backend Lock-in**: `cursor-agent` CLI is strictly bound to the official Cursor backend (`api2.cursor.sh`).
- **No Third-Party Models**: Third-party OpenAI-compatible endpoints (e.g., Aliyun Qwen) cannot be used directly in the CLI because `--endpoint` overrides the Cursor backend, not the completion endpoint, causing authentication failures. Do not try to bypass models with `--endpoint` or `--api-key`.


## Verification

- [ ] Confirm the binary is in PATH.
- [ ] Run the health check:

```sh
cursor-agent --version
```

- [ ] Run a simple headless test (requires active Cursor auth):

```sh
cursor-agent --print --trust "hi, what is 1+1? please answer in one sentence."
```

## Follow-up

- [ ] Verify `cursor-agent` is successfully authenticated under the correct Cursor account.
- [ ] Do not use custom third-party endpoints or API keys with `--endpoint` or `--api-key`.

## Rollback

To uninstall, remove the installed package and symlink, typically `~/.local/bin/cursor-agent` and related `.cursor` folders in the home directory.

## Evidence and notes

- Source reference: `https://cursor.com/install`
- Reusable notes: Uses a shell script install. Authentication requires opening the browser and syncing credentials locally. Open Design integrations must respect the Cursor backend limits.
