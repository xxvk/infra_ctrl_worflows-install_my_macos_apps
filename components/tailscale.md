---
name: "Tailscale"
category: "Network"
tier: core
status: installed
source: app_store
download_bytes: null
download_estimate_bytes: 1000000000
download_estimate_method: catalog_size_gb_planning_estimate
installed_bytes: 31293440
installed_version: "1.98.8"
installed_at: "2026-07-16"
secrets_policy: Never store passwords, API keys, recovery codes, or license secrets here.
---
# Tailscale

> [!summary]
> Mesh VPN client. The GUI is sourced from the Mac App Store; the `tailscale` CLI is a separate Homebrew formula.

## Verification

- Mac App Store receipt present at `Contents/_MASReceipt/receipt`.
- Opened successfully; current UI state: `Not Connected`.
- Sign in to the intended tailnet and approve the macOS VPN configuration when prompted.
- Confirm the device appears in the tailnet and the connection switch is on.

## Optional CLI

Install separately only when CLI control is needed:

```sh
brew install tailscale
command -v tailscale
tailscale version
```
