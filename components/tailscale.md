---
component_id: "tailscale"
name: "Tailscale"
category: "Network"
tier: "core"
lifecycle_status: "active"
source: "app_store"
delivery_method: "app-store"
brew_cask: null
brew_formula: null
official_url: "https://tailscale.com/download/mac"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 1000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
tore receipt present at `Contents/_MASReceipt/receipt`.
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
