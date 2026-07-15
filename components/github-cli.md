---
component_id: "github-cli"
name: "GitHub CLI (gh)"
category: "Developer tools"
tier: "developer"
status: "verified"
delivery_method: "homebrew-formula"
brew_cask: null
brew_formula: "gh"
official_url: "https://cli.github.com/"
check_command: "gh"
install_after: []
download_bytes: null
installed_bytes: null
installed_version: "2.96.0"
installed_at: "2026-07-15"
configured_at: "2026-07-15"
verified_at: "2026-07-15"
config_status: "complete"
verification_status: "passed"
account_required: true
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
---

# GitHub CLI (`gh`)

> [!summary] Purpose
> Command-line access to GitHub repositories, workflows, issues, and other GitHub operations.

## Parameters

| Parameter | Value |
|---|---|
| Delivery | Homebrew formula |
| Package identifier | `gh` |
| Official source | https://cli.github.com/ |
| Required tier | developer |
| Install order | none |
| Expected download | Not recorded; installed before per-app byte measurement was added |
| Expected installed size | Not recorded; installed before per-app byte measurement was added |
| Config path(s) | GitHub CLI keyring/config managed by `gh` |
| Account needed | yes |
| Permissions | none beyond the scopes explicitly granted during login |

## Installation

- [x] Confirmed missing during the 2026-07-15 scan.
- [x] Dry run completed.
- [x] Installed with the verified Homebrew formula:

```sh
brew install gh
```

- [x] Installed version: `2.96.0`.

## Configuration

Run the interactive login yourself; do not paste tokens into deployment records:

```sh
gh auth login
```

The completed setup uses HTTPS and the active account `xxvk`. Authentication is stored in the system keyring. The verified scopes were `gist`, `read:org`, `repo`, and `workflow`.

## Verification

```sh
command -v gh
gh --version
gh auth status
```

- [x] Binary path verified: `/opt/homebrew/bin/gh`.
- [x] Version verified: `2.96.0`.
- [x] Active GitHub account verified through the system keyring.
- [x] `repo` scope verified for private repository operations.

## Follow-up

- [ ] Re-run `gh auth status` after changing or revoking the GitHub token.
- [ ] Before private repository commands, verify the active account and required scope.

## Rollback

To remove the active login without deleting repositories:

```sh
gh auth logout -h github.com -u xxvk
```

To remove the CLI itself:

```sh
brew uninstall gh
```

## Evidence and notes

- Install record: [`state/install-20260715-120605.json`](../state/install-20260715-120605.json)
- Verification record: GitHub CLI auth status verified 2026-07-15
- Scan record: [`state/scan-20260715-120647.json`](../state/scan-20260715-120647.json)
- Notes: No token, password, recovery code, or license secret is stored in this guide.
