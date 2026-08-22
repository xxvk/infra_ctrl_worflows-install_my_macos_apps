---
component_id: "dsh-computer-use"
name: "DSH Computer Use"
category: "AI Agent"
tier: "optional"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "zrui-c/tap/dsh-computer-use"
brew_formula: null
brew_tap: "zrui-c/tap"
brew_tap_repository: "https://github.com/ZRui-C/homebrew-tap"
official_url: "https://computer-use.zrui.tech/"
check_command: "test -d '/Applications/DSH Computer Use.app'"
install_after: []
bundle_identifiers: ["tech.zrui.dsh-computer-use"]
account_required: false
permissions_required: ["Accessibility", "Screen Recording"]
secrets_policy: "Never store browser session cookies, passwords, tokens, or recovery codes here."
download_estimate_bytes: 3000000
download_estimate_method: "cask_installed_size"
---

# DSH Computer Use

> [!summary] Purpose
> Text-first browser and background macOS control for the DeepSeek Harness
> ecosystem. It pairs with the `dsh-computer-use` plugin (host + tool rows in
> the DSH web profile) to let a DSH agent drive a browser and background
> system actions through the app's own interface.

Optional tier: this is a companion capability to DSH Desktop, installed only
when browser/background control from DSH is actually needed.

## Source

- Cask: `zrui-c/tap/dsh-computer-use` (Homebrew, preferred)
- Tap: `https://github.com/ZRui-C/homebrew-tap`
- Upstream: `https://github.com/ZRui-C/dsh-computer-use` (GitHub release `v0.3.0`)
- Official site: `https://computer-use.zrui.tech/`

Source priority: **Homebrew cask first** (pinned tap), then GitHub release,
then manual. Verify the Tap remote, HEAD, and exact Cask before trusting; never
trust the whole Tap.

## Parameters

| Parameter | Value |
|---|---|
| Version | 0.3.0 |
| Bundle ID | `tech.zrui.dsh-computer-use` |
| App path | `/Applications/DSH Computer Use.app` |
| macOS | >= 14 (Sonoma) |
| Installed size | ~3 MB (Caskroom) |

## Installation

- [ ] Confirm the app is missing from the latest scan.
- [ ] Confirm the selected plan and available disk space.
- [ ] Run the dry run with no external changes.
- [ ] Obtain explicit approval before tapping, trusting, or installing.
- [ ] Verify the exact Tap remote and HEAD against the pinned values above.
- [ ] Trust only the named Cask, never the complete Tap.
- [ ] Record bytes, version, paths, timestamps, and pass/fail only in
      machine-local state.

```sh
brew tap zrui-c/tap
brew install --cask zrui-c/tap/dsh-computer-use
```

## Follow-up and verification

- Open `DSH Computer Use.app` once to grant **Accessibility** and **Screen
  Recording** permissions (interactive; never automate the grant).
- Install the `dsh-computer-use` plugin into the DSH profile (host + tool
  rows) and restart the running DSH Host.
- Run the read-only verification command and require `status: passed`:

```sh
./bin/macomrade verify dsh-computer-use
```

  The command checks three independent layers: the installed bundle and its
  `tech.zrui.dsh-computer-use` identifier, the tracked catalog entry
  consistency, and the `computer-use-host` / `computer-use-tool` loader rows
  composed by `dsh --profile web --dump-config`. It never reads the TCC
  database, changes a permission, writes profile configuration, or sends a
  model request; Accessibility/Screen Recording grants remain
  `manual_verification_required` by design.
- Verify browser and background control work from a DSH session (read-back,
  not a claim).
- Verify the pinned Tap revision and Cask sha256 before trusting.

## Cleanup

```sh
brew uninstall --cask zrui-c/tap/dsh-computer-use
```

Do not remove Accessibility/Screen Recording grants or support data without a
separate, path-specific review and confirmation.

## Evidence and notes

- Upstream: `https://github.com/ZRui-C/dsh-computer-use`
- Tap: `https://github.com/ZRui-C/homebrew-tap`
- Machine-specific permission grants, versions, paths, and verification
  results belong only in machine-local state.

Never paste a machine-local record, completed checkbox, detected version,
permission grant, or timestamp back into this tracked guide.
