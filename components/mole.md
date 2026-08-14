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
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 10000000
download_estimate_method: "catalog_size_gb_planning_estimate"
cli_path: "/opt/homebrew/opt/mole"
---
# Mole

Mole is the Core disk-maintenance CLI. Install it after Ghostty, preview every
cleanup, and preserve the tracked Hugging Face exclusion.

For macomrade 0.2 storage work, treat Mole as an optional interactive explorer
and `mole history --json` as read-only evidence. macomrade's Foundation-based
logical/allocated scan and post-action free-space measurement are the capacity
authority. Do not call a private executable inside Mole's Homebrew Cellar or
infer a retention decision from Mole history. See
[`storage-lifecycle.md`](../references/storage-lifecycle.md).

## Installation

```sh
brew install mole
```

## Configuration

The cross-device baseline protects Hugging Face model assets from Mole cleanup.
Preserve existing entries and ensure this line exists in
`~/.config/mole/whitelist`:

```sh
mkdir -p "$HOME/.config/mole"
touch "$HOME/.config/mole/whitelist"
grep -qxF '~/.cache/huggingface' "$HOME/.config/mole/whitelist" || \
  printf '%s\n' '~/.cache/huggingface' >> "$HOME/.config/mole/whitelist"
```

Verify the resulting file before cleanup. Do not store the machine-local
whitelist in tracked `state/`; recreate it on each device. If shell completion
is desired, review the preview before changing shell files:

```sh
mole completion --dry-run
```

Do not enable Touch ID or add other whitelist rules without reviewing exactly
which paths and commands will be affected. The Hugging Face rule above is part
of the approved baseline.

## Verification

```sh
command -v mole
mole --version
mole --help
```

- [ ] Confirm the binary, version output, and supported cleanup commands.
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

Write detected version, path, byte measurements, cleanup results, and timestamps
only to machine-local state.

Mole's own scan cache at `~/.cache/mole` is regenerable and is included in the
public macomrade `safe_cache` policy. It is not the Mole executable, whitelist,
user content, or a capacity authority. Clearing it may discard local scan
acceleration/history evidence and make the next analysis slower; verify the
directory is recreated normally before relying on Mole history again.
