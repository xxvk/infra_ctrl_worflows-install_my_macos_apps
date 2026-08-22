---
component_id: "cc-switch"
name: "CC Switch"
category: "Developer tools"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "cc-switch"
official_url: "https://github.com/farion1231/cc-switch"
bundle_identifiers: ["com.ccswitch.desktop"]
application_path: "/Applications/CC Switch.app"
check_command: "test -d '/Applications/CC Switch.app'"
account_required: false
permissions_required: []
secrets_policy: "Never store provider API keys or tokens here."
install_after: []
brew_formula: null
download_estimate_bytes: 200000000
download_estimate_method: "cask_dmg_metadata"
---

# CC Switch

> [!summary] Purpose
> Cross-platform desktop All-in-One assistant for Claude Code, Codex, OpenCode,
> OpenClaw, Grok Build & Hermes Agent. Core tool for switching AI coding agent
> provider configurations.

## Source

- Cask: `cc-switch` (official Homebrew cask)
- Upstream: `https://github.com/farion1231/cc-switch` (MIT, official site
  `https://ccswitch.io`)
- Cask URL: `https://github.com/farion1231/cc-switch/releases/download/v3.20.0/CC-Switch-v3.20.0-macOS.dmg`

## Parameters

| Parameter | Value |
|---|---|
| Version | 3.20.0 (auto_updates) |
| App path | `/Applications/CC Switch.app` |
| Account | Not required |
| macOS | >= 12 |

## Installation

- [ ] Confirm the app is missing from the latest scan.
- [ ] Confirm the selected plan and available disk space.
- [ ] Run the dry run with no external changes.
- [ ] Obtain explicit approval before installing.
- [ ] Record bytes, version, paths, timestamps, and pass/fail only in
      machine-local state.

```sh
brew install --cask cc-switch
```

## Follow-up and verification

- Open CC Switch and review provider/API-key configuration (interactive).
- Never store API keys or tokens in the catalog or any tracked file.
- Verify provider profiles work with the intended AI coding agents.
- Confirm the installed version is at least 3.20.0.

## Cleanup

```sh
brew uninstall --cask cc-switch
```

Do not remove provider configuration or credentials without a separate,
path-specific cleanup review and confirmation.

## Evidence and notes

- Cask source: `https://github.com/Homebrew/homebrew-cask/blob/HEAD/Casks/c/cc-switch.rb`
- Machine-specific provider profiles and verification results belong only in
  machine-local state.

Never paste a machine-local record, completed checkbox, API key, or timestamp
back into this tracked guide.
