---
name: "Claude"
category: "AI"
tier: core
status: installed
source: homebrew
download_bytes: null
download_estimate_bytes: 1000000000
download_estimate_method: catalog_size_gb_planning_estimate
installed_bytes: 1831919616
installed_version: "1.21459.0"
installed_at: "2026-07-16"
secrets_policy: Never store passwords, API keys, recovery codes, or license secrets here.
---
# Claude

> [!summary]
> Claude Desktop, with a separate Claude Code CLI workflow.

## Post-install checklist

- Open Claude and sign in with the Google account `example.user@example.invalid`.
- Verify the account shown in Claude before proceeding; never store credentials or tokens here.
- Confirm notifications, microphone, accessibility, and any requested automation permission interactively.
- Version verified: `1.21459.0`.
- Path: `/Applications/Claude.app`; Bundle ID: `com.anthropic.claudefordesktop`.
- VM image cleanup was completed before replacement; the directory was not locked.
- Claude.app was opened after installation and passed the follow-up source scan.

## Claude Code CLI

- Source: Homebrew cask `claude-code`
- CLI path: `/opt/homebrew/bin/claude`
- Version verified: `2.1.202`
- Complete CLI login interactively with the intended account when first used;
  never store credentials or tokens in this guide.

## Pre-install storage check

Claude Desktop may create a local-agent VM under `~/Library/Application Support/Claude/vm_bundles/`. Review it before installing or replacing Claude:

```sh
python3 scripts/claude_vm_cleanup.py inspect
```

The current tracked issue is [anthropics/claude-code#65577](https://github.com/anthropics/claude-code/issues/65577). It describes unbounded growth of `rootfs.img`; the issue is currently open and stale. The documented workaround is to remove `rootfs.img` and `sessiondata.img` while Claude is fully quit. Session state is stored separately, but Cowork/local-agent execution will rebuild or fail afterward.

## Separate cleanup actions

The skill must ask for a separate confirmation before either action:

```sh
python3 scripts/claude_vm_cleanup.py remove --confirm "REMOVE CLAUDE VM IMAGES"
python3 scripts/claude_vm_cleanup.py lock --confirm "LOCK CLAUDE VM DIRECTORY"
```

`remove` deletes only the two VM images and preserves the surrounding Claude support directory. `lock` applies `chmod 000` and `chflags uchg` to prevent automatic recreation; it deliberately disables Cowork/local-agent VM use and may cause retries or errors. Restore with:

```sh
python3 scripts/claude_vm_cleanup.py unlock
```

Do not run cleanup while Claude or `vfkit`/`gvisor` processes are active. After cleanup, reinstall Claude through the approved source, open it, and verify the first window. The cleanup and installation are two separate auditable operations.
