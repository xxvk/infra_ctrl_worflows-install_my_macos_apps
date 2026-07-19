---
component_id: "mole"
name: "mole"
category: "System tools"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-formula"
brew_cask: null
brew_formula: "mole"
official_url: "https://mole.fit"
check_command: "mole"
install_after: ["Ghostty"]
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
cli_path: "/opt/homebrew/opt/mole"
---
ry | `/opt/homebrew/bin/mole` |
| Download recorded | 4,403,200 bytes |
| Installed size recorded | 9,224,192 bytes (~8.8 MiB) |
| Binary | `/opt/homebrew/bin/mole` |
| Account needed | no |
| Permissions | Review each sudo/Touch ID request interactively |

## Installation

- [x] Confirmed missing during the 2026-07-15 scan.
- [x] Confirmed Ghostty was installed first.
- [x] Dry run completed.
- [x] Installed with the verified Homebrew formula:

```sh
brew install mole
```

- [x] Installed version: `1.46.0`.

## Configuration

No automatic cleanup configuration is applied. If shell completion is desired, review the preview before changing shell files:

```sh
mole completion --dry-run
```

Do not enable Touch ID or write whitelist rules without reviewing exactly which paths and commands will be affected.

## Verification

```sh
command -v mole
mole --version
mole --help
```

- [x] Binary path verified: `/opt/homebrew/bin/mole`.
- [x] Version verified: `1.46.0`.
- [x] Help output confirms the supported cleanup commands.
- [ ] Run the first review inside Ghostty and inspect every candidate before confirming any deletion.

## Safe operating procedure

Always preview first:

```sh
mole clean --dry-run
mole optimize --dry-run
mole purge --dry-run
mole installer --dry-run
```

Never approve a cleanup item merely because it is large. Preserve project files, databases, backups, package caches needed for active work, and anything whose ownership is unclear. The skill does not automate destructive `mole` actions.

## Follow-up

- [ ] Run `mole` in Ghostty and review the interactive menu.
- [ ] Decide whether shell completion is useful after reviewing its dry run.
- [ ] Record any whitelist or protected paths without storing secrets.

## Rollback

To remove Mole while preserving the files it has not deleted:

```sh
mole remove --dry-run
brew uninstall mole
```

Review the dry run before any `mole remove` action. Uninstalling the tool does not restore files removed by a prior cleanup.

## Evidence and notes

- Install record: [`state/install-20260715-132537.json`](../state/install-20260715-132537.json)
- Scan record: [`state/scan-20260715-132109.json`](../state/scan-20260715-132109.json)
- Notes: Installation succeeded after one permission-review timeout. No cleanup command has been run.
