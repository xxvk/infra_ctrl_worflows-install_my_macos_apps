---
component_id: "chatgpt"
name: "ChatGPT"
category: "AI"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "chatgpt"
brew_formula: null
official_url: "https://chatgpt.com/download"
check_command: null
install_after: []
account_required: true
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 1000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
- Sign in with the intended account from the merged Private app-catalog overlay.
- Open the account/avatar menu and verify the displayed email exactly.
- Keep the installed version at or above the baseline recorded in this guide.
- Never store passwords, API keys, recovery codes, or tokens here.

## Permissions

Review microphone, notifications, screen recording, or accessibility requests only when the app asks for them. The skill does not grant macOS privacy permissions automatically.

## Verification

- [ ] App opens without a security warning.
- [ ] Account email matches the merged `preferred_account`.
- [ ] Version is not below the recorded baseline.

## Storage lifecycle

`~/.cache/codex-runtimes` contains re-downloadable workspace runtimes, but it
may be in active use by ChatGPT/Codex, including the task performing the scan.
Do not classify it as a generic live-process-safe cache. A cleanup proposal
must require all ChatGPT/Codex tasks and helper processes to exit, verify that
no process holds the exact tree, and warn that document, spreadsheet, slide,
PDF, or other workspace work can download it again. Report the result as
transient reclaim until a later representative task proves otherwise.

Sparkle installation staging under `~/Library/Caches/com.openai.codex` can
also retain an older executable while a Codex process still has it open. Do
not kill the current task or remove the staging tree underneath it. Exit the
owning process first, then re-inspect the exact path; a reboot may release the
open executable, but that reboot benefit is not durable application cleanup.
