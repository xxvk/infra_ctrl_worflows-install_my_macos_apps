---
component_id: "open-design"
name: "Open Design"
category: "Design"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "open-design"
official_url: "https://open-design.ai/"
github_repository: "https://github.com/nexu-io/open-design"
bundle_identifiers: ["io.open-design.desktop"]
application_path: "/Applications/Open Design.app"
check_command: "test -d '/Applications/Open Design.app'"
account_required: false
permissions_required: []
secrets_policy: "Never store design tokens, API keys, or recovery codes here."
install_after: []
brew_formula: null
download_estimate_bytes: 300000000
download_estimate_method: "cask_dmg_metadata"
---

# Open Design

> [!summary] Purpose
> Local-first, agent-native design tool. Core design capability; runs locally
> with agent-native features (no account required).

## Source

- Cask: `open-design` (official Homebrew cask, `homebrew/homebrew-cask`)
- Upstream: `https://open-design.ai/` / `https://github.com/nexu-io/open-design`
- Cask URL: `https://github.com/nexu-io/open-design/releases/download/open-design-v0.20.0/open-design-0.20.0-mac-arm64.dmg`

Source priority: **Homebrew cask first** (official core cask), then GitHub
release, then official website, then manual.

## Parameters

| Parameter | Value |
|---|---|
| Version | 0.20.0 (auto_updates) |
| Bundle ID | `io.open-design.desktop` |
| App path | `/Applications/Open Design.app` |
| Account | Not required (local-first) |
| macOS | >= 12 |

## Installation

- [ ] Confirm the app is missing from the latest scan.
- [ ] Confirm the selected plan and available disk space.
- [ ] Run the dry run with no external changes.
- [ ] Obtain explicit approval before installing.
- [ ] Record bytes, version, paths, timestamps, and pass/fail only in
      machine-local state.

```sh
brew install --cask open-design
```

## Follow-up and verification

- Open Open Design and verify local-first project creation.
- Verify agent-native design features work from the local runtime.
- Review storage location and sync choices.
- Confirm the installed version is at least 0.20.0.

## Cleanup

```sh
brew uninstall --cask open-design
```

Do not remove local design files or support data without a separate,
path-specific cleanup review and confirmation.

## Evidence and notes

- Cask source: `https://github.com/Homebrew/homebrew-cask/blob/HEAD/Casks/o/open-design.rb`
- Machine-specific version, paths, and verification results belong only in
  machine-local state.

Never paste a machine-local record, completed checkbox, detected version, or
timestamp back into this tracked guide.
