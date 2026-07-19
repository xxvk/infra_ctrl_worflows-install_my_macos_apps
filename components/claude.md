---
component_id: "claude"
name: "Claude"
category: "AI"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "claude"
brew_formula: null
official_url: "https://claude.ai/download"
check_command: null
install_after: []
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
---
 `example.user@example.invalid`.
- Verify the account shown in Claude before proceeding; never store credentials or tokens here.
- Confirm notifications, microphone, accessibility, and any requested automation permission interactively.
- Version verified: `1.21459.0`.
- Path: `/Applications/Claude.app`; Bundle ID: `com.anthropic.claudefordesktop`.
- Complete VM bundle cleanup was completed after replacement; `vm_bundles/` is
  locked with `chmod 000` and `chflags uchg` to prevent automatic re-download.
- Claude.app was opened after installation and passed the follow-up source scan.

## Mandatory Developer mode, third-party inference, and Local MCP verification

After installation, account verification, and the first successful launch,
automatically check and enable Claude Desktop's Developer settings before
marking Claude ready for use. This is a local application preference; it does
not require entering credentials or changing macOS privacy permissions:

1. Open the `Help` menu and inspect `Troubleshooting`.
2. If the item says `Enable Developer Mode`, activate it, accept the app's
   non-binding warning, and wait for Claude Desktop to restart.
3. If the item already says `Disable Developer Mode`, treat Developer Mode as
   already enabled.
4. Confirm that a top-level `Developer` menu appears.
5. Open `Developer → Configure Third-party Inference…`.
6. If the page is available, configure the Gateway base URL, credential kind,
   custom inference headers, model discovery, and model list manually.
   Treat the model-list editor as Anthropic-family-only: a non-Anthropic
   OpenRouter ID such as `deepseek/deepseek-v4-pro` may be accepted by the
   form but causes a malformed provider setup after relaunch. If validation
   reports that the route is not an Anthropic model, remove/discard the entry,
   save and apply the restored list, relaunch Claude, and confirm the setup
   warning is gone. Do not force-apply that entry.
7. Verify required Local MCP servers, including command, arguments, and status.
8. Open server logs when a server is disconnected and resolve the issue before
   marking the Claude setup complete.
9. Record only provider name, endpoint type, model name, MCP server name,
   status, and pass/fail. Never record API keys, tokens, or request headers.
10. Use the GUI for third-party inference changes; do not edit Claude's local
    configuration files directly.

The exact location and availability of Developer settings may change by Claude
Desktop version, account type, region, and rollout status. If the setting is
not available, mark the installation follow-up as blocked and record the
installed version.

The verified current build exposes a `Configure Third-party Inference…` page
with a Gateway base URL, custom headers, credential kind, model discovery, and
model list. This makes compatible third-party inference gateways possible, but
provider compatibility still requires a real non-sensitive test. Never assume
that every OpenAI, Chinese, or other provider works without testing its
endpoint and model response.

### Non-Anthropic model compatibility guard

An Anthropic-compatible Gateway protocol does not guarantee that Claude
Desktop accepts the provider's native model ID. Current builds validate model
entries as Anthropic-family routes. For example, adding the OpenRouter ID
`deepseek/deepseek-v4-pro` produces a `Doesn't look like an Anthropic model`
warning and can make the relaunched app report `provider setup needs a fix`.

When a non-Anthropic model is requested:

1. Add it only through the GUI and observe the validation warning.
2. If the warning appears, do not apply it as a working configuration.
3. Remove the entry, save and apply the restored model list, relaunch Claude,
   and verify that the setup warning is gone and a normal Anthropic model can
   run a non-sensitive inference test.
4. Treat community model aliases, local proxies, and CC-switch-style routing
   as separate workarounds, not native Claude Desktop support. Prefer Claude
   Code CLI, OpenCode, or a separately tested Anthropic-compatible proxy for
   DeepSeek.

### Restore the original Claude subscription

Developer Mode can remain enabled while using the original Claude
subscription; it is independent of the inference mode. To leave Gateway / 3P
mode:

1. Open the current Gateway account menu and click `Sign out`/`Logout`.
2. After Claude relaunches, sign in again at `claude.ai` with the original
   Claude account.
3. Verify that the page URL is `claude.ai/new`, the `Gateway` indicator is
   gone, and the model picker shows the subscription model.

Do not disable Developer Mode during this switch. If signing out does not
restore the Anthropic login flow, stop before deleting local state; back up the
relevant 3P state first and treat filesystem cleanup as a separate recovery
operation.

### OpenRouter model discovery troubleshooting

For OpenRouter, use the Anthropic-compatible Gateway URL:

```text
https://openrouter.ai/api
```

Keep Model discovery enabled. Claude Desktop discovers models from:

```text
https://openrouter.ai/api/v1/models
```

After changing or creating a configuration, run `Test model discovery`. If it
finds models but the task model picker still shows only the previous default,
fully quit Claude Desktop and reopen it; discovery is loaded at launch. Do not
paste API keys into documentation or operation records. OpenRouter documents
this Gateway setup and model discovery flow at its Claude Desktop integration
guide.

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

## Mandatory Analyze Disk cleanup

After every Claude installation or replacement, run the Analyze Disk inspection and do not mark the operation complete while `claudevm.bundle` remains. Report the total bundle size, quit Claude completely, then obtain explicit confirmation and remove the complete bundle:

```sh
python3 scripts/claude_vm_cleanup.py inspect
python3 scripts/claude_vm_cleanup.py remove-bundle --confirm "REMOVE CLAUDE VM BUNDLE"
```

This removes the entire `~/Library/Application Support/Claude/vm_bundles/claudevm.bundle` and may disable or rebuild Cowork/local-agent execution. Verify the path is gone and record the reclaimed bytes in the ignored `state/` operation log. To prevent Claude from downloading the bundle again, lock the parent directory as the default storage-saving follow-up:

```sh
python3 scripts/claude_vm_cleanup.py lock --confirm "LOCK CLAUDE VM DIRECTORY"
```

Verify with `inspect`/`ls -ldO`; the expected directory state includes mode
`d---------` and the `uchg` flag. This lock intentionally disables Cowork and
local-agent VM features until it is removed.

## Separate cleanup actions

The skill must ask for a separate confirmation before either action:

```sh
python3 scripts/claude_vm_cleanup.py remove --confirm "REMOVE CLAUDE VM IMAGES"
python3 scripts/claude_vm_cleanup.py lock --confirm "LOCK CLAUDE VM DIRECTORY"
```

`remove` deletes only the two VM images and preserves the surrounding Claude support directory. `remove-bundle` deletes the complete VM bundle. `lock` applies `chmod 000` and `chflags uchg` to prevent automatic recreation; it deliberately disables Cowork/local-agent VM use and may cause retries or errors. Restore with:

```sh
python3 scripts/claude_vm_cleanup.py unlock
```

Do not run cleanup while Claude or `vfkit`/`gvisor` processes are active. After cleanup, reinstall Claude through the approved source, open it, and verify the first window. The cleanup and installation are two separate auditable operations.
