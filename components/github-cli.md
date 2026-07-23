---
component_id: "github-cli-gh"
name: "GitHub CLI (gh)"
category: "Developer tools"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-formula"
brew_cask: null
brew_formula: "gh"
official_url: "https://cli.github.com/"
check_command: "gh"
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 50000000
download_estimate_method: "catalog_size_gb_planning_estimate"
cli_path: "/opt/homebrew/opt/gh"
---
# GitHub CLI (gh)

Use the Homebrew formula for the CLI and the system keyring for authentication.
Account and scope are verified separately on every Mac.

## Installation

```sh
brew install gh
```

## Configuration

Run the interactive login yourself; do not paste tokens into deployment records:

```sh
gh auth login
```

Resolve the intended account from the merged
`Private/app-catalog-overlay.json` entry for `GitHub CLI (gh)` and compare it
with `gh auth status`. Authentication belongs in the system keyring; never
copy its token into Git or infer live authorization from this guide.

## Verification

```sh
command -v gh
gh --version
gh auth status
```

- [ ] Confirm `command -v gh` resolves to the intended Homebrew installation.
- [ ] Confirm the active account and only the scopes required for the planned operation.

## Follow-up

- [ ] Re-run `gh auth status` after changing or revoking the GitHub token.
- [ ] Before private repository commands, verify the active account and required scope.

## Rollback

To remove the active login without deleting repositories:

```sh
gh auth logout -h github.com -u <github-account>
```

To remove the CLI itself:

```sh
brew uninstall gh
```

## Evidence and notes

Write version, resolved path, authentication result, scopes, and timestamps only
to machine-local state. Never record a token, password, recovery code, or
license secret.
