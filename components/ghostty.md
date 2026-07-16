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
| Delivery | Homebrew cask |
| Package identifier | `ghostty` |
| Official source | https://ghostty.org/download |
| Required tier | developer |
| Install order | none |
| Download recorded | 34,508,800 bytes (~32.9 MiB) |
| Installed size recorded | 70,725,632 bytes (~67.4 MiB) |
| Config path | `~/.config/ghostty/config` |
| Account needed | no |
| Permissions | none required for the default setup |
| Config path | `~/.config/ghostty/config` |
| Account needed | no |
| Permissions | none required for the default setup |

## Installation

- [x] Confirmed missing during the 2026-07-15 scan.
- [x] Dry run completed.
- [x] Installed with the verified Homebrew cask:

```sh
brew install --cask ghostty
```

- [x] Installed version: `1.3.1`.

## Configuration

The skill default configuration is:

```ini
theme = Cyberpunk Scarlet Protocol
font-family = JetBrains Mono
font-size = 20
```

It is stored at `~/.config/ghostty/config`. Preserve unrelated user settings when adding or changing these lines.

- [x] Created `~/.config/ghostty/config` with the three default settings on 2026-07-15.

## Verification

```sh
/Applications/Ghostty.app/Contents/MacOS/ghostty +list-themes --plain | rg -i 'Cyberpunk Scarlet Protocol'
/Applications/Ghostty.app/Contents/MacOS/ghostty +show-config | rg -n 'theme|font-family|font-size'
```

- [x] `Cyberpunk Scarlet Protocol` is available as a built-in theme.
- [x] Ghostty reads `Cyberpunk Scarlet Protocol`, `JetBrains Mono`, and font size `20`.
- [ ] Open Ghostty and confirm the first window renders without a crash or macOS security warning.
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

- Install record: [`state/install-20260715-125224.json`](../state/install-20260715-125224.json)
- Scan record: [`state/scan-20260715-125235.json`](../state/scan-20260715-125235.json)
- Notes: The install record separates download and installed bytes. The app was installed after one failed download attempt caused by a reset connection.
