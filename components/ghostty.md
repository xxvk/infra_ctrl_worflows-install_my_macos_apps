---
component_id: "ghostty"
name: "Ghostty"
category: "Developer tools"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "ghostty"
brew_formula: null
official_url: "https://ghostty.org/download"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 1000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# Ghostty

Ghostty is the preferred Core terminal. Install it from the Homebrew cask and
apply the tracked visual baseline without replacing unrelated settings.

## Installation

```sh
brew install --cask ghostty
```

## Configuration

The skill default configuration is:

```ini
theme = Cyberpunk Scarlet Protocol
font-family = JetBrains Mono
font-size = 20
```

It is stored at `~/.config/ghostty/config`. Preserve unrelated user settings when adding or changing these lines.

## Verification

```sh
/Applications/Ghostty.app/Contents/MacOS/ghostty +list-themes --plain | rg -i 'Cyberpunk Scarlet Protocol'
/Applications/Ghostty.app/Contents/MacOS/ghostty +show-config | rg -n 'theme|font-family|font-size'
```

- [ ] Open Ghostty and confirm the first window renders without a crash or macOS security warning.
- [ ] Confirm the built-in theme and the three tracked values through the commands above.
- [ ] Test shell integration, tabs, splits, and the configured font at the preferred display scale.

## Follow-up

- [ ] Import terminal preferences only after reviewing them for secrets and machine-specific paths.
- [ ] Confirm shell and SSH configuration separately; do not copy private keys into this guide.

## Rollback

Remove or edit the three default lines in `~/.config/ghostty/config` to return to Ghostty defaults. To uninstall the app while preserving the config:

```sh
brew uninstall --cask ghostty
```

## Evidence and notes

Write version, path, byte measurements, timestamps, and pass/fail results only
to the active machine-local state directory.
