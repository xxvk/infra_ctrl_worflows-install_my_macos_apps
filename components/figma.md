---
component_id: "figma"
name: "Figma"
category: "Design"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "figma"
official_url: "https://www.figma.com/"
bundle_identifiers: ["com.figma.Desktop"]
application_path: "/Applications/Figma.app"
check_command: "test -d '/Applications/Figma.app'"
account_required: true
permissions_required: []
secrets_policy: "Never store Figma account tokens, passwords, or recovery codes here."
install_after: []
brew_formula: null
download_estimate_bytes: 350000000
download_estimate_method: "cask_zip_metadata"
---

# Figma

> [!summary] Purpose
> Collaborative interface design tool (desktop app). Core design capability for
> UI/UX work; requires an account for real use.

## Source

- Cask: `figma` (official Homebrew cask, `homebrew/homebrew-cask`)
- Upstream: `https://www.figma.com/`
- Cask URL: `https://desktop.figma.com/mac-arm/Figma-126.7.10.zip`

Source priority: **Homebrew cask first** (official core cask), then official
website download, then manual. Verify the exact cask URL and sha256 before
installing.

## Parameters

| Parameter | Value |
|---|---|
| Version | 126.7.10 (auto_updates) |
| Bundle ID | `com.figma.Desktop` |
| App path | `/Applications/Figma.app` |
| Account | Required (sign in to use) |

## Installation

- [ ] Confirm the app is missing from the latest scan.
- [ ] Confirm the selected plan and available disk space.
- [ ] Run the dry run with no external changes.
- [ ] Obtain explicit approval before installing.
- [ ] Record bytes, version, paths, timestamps, and pass/fail only in
      machine-local state.

```sh
brew install --cask figma
```

## Follow-up and verification

- Sign in with the intended Figma account (interactive; never automate login).
- Verify the account shown in Figma matches before continuing.
- Review font/plugin/asset sync settings.
- Confirm the installed version is at least 126.7.10.

## Cleanup

```sh
brew uninstall --cask figma
```

Do not remove local design files or account data without a separate,
path-specific cleanup review and confirmation.

## Evidence and notes

- Cask source: `https://github.com/Homebrew/homebrew-cask/blob/HEAD/Casks/f/figma.rb`
- Machine-specific account, version, paths, and verification results belong
  only in machine-local state.

Never paste a machine-local record, completed checkbox, detected version,
account identity, or timestamp back into this tracked guide.
