---
component_id: "sourcetree"
name: "Sourcetree"
category: "Developer tools"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "sourcetree"
brew_formula: null
official_url: "https://www.sourcetreeapp.com/"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store GitHub passwords, OAuth tokens, personal access tokens, SSH private keys, recovery codes, or Keychain exports here."
download_estimate_bytes: 200000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# Sourcetree

> [!summary] Purpose
> Core graphical Git client for repositories that benefit from a visual
> history, staging, branch, merge, and multi-hosting-account workflow.
> Sourcetree includes its own Git binary and can operate without selecting the
> macOS system Git. Multiple accounts still require explicit separation of
> authentication credentials and per-repository commit identity.

## Parameters

| Parameter | Value |
|---|---|
| Delivery | Homebrew Cask |
| Package identifier | `sourcetree` |
| Official source | `https://www.sourcetreeapp.com/` |
| Required tier | Core |
| Install order | none |
| Expected download | 200 MB planning estimate |
| Expected installed size | measure per Mac |
| App path | `/Applications/Sourcetree.app` |
| Embedded Git path | `/Applications/Sourcetree.app/Contents/Resources/git_local/bin/git` |
| Account needed | no for local repositories; yes for GitHub/Bitbucket hosting access |
| Permissions | none by default; Keychain and SSH access follow the chosen authentication method |

## Installation

- [ ] Confirm Sourcetree is missing from the latest scan.
- [ ] Confirm the selected plan and available disk space.
- [ ] Run the managed dry run with no external changes.
- [ ] Obtain explicit approval before download or installation.
- [ ] Install from the official Homebrew Cask.
- [ ] Record observed version, paths, size, timestamps, and pass/fail only in
      machine-local state.

```sh
brew install --cask sourcetree
```

Do not replace GitHub Desktop or alter existing repository remotes merely
because Sourcetree is installed. The two clients may coexist and read the same
repository metadata.

## Embedded Git baseline

Sourcetree can use either its bundled Git or a user-selected system Git. For
the independent-client baseline, open `Sourcetree → Preferences → Git` and use
`Reset to Embedded Git`. Verify the displayed Git path and version against:

```sh
/Applications/Sourcetree.app/Contents/Resources/git_local/bin/git --version
```

The embedded executable removes the runtime dependency on `/usr/bin/git`, but
it does not create an isolated Git identity or credential store. Sourcetree and
other Git clients still read repository configuration such as `.git/config`,
and authentication can still involve the macOS Keychain or SSH agent.

Use system Git only when a repository requires a reviewed version, extension,
credential helper, or compatibility feature not provided by the embedded Git.
Record that exception in machine-local state rather than changing the shared
baseline.

## Multiple GitHub accounts

Atlassian documents that Sourcetree can add multiple accounts. Open the
Accounts preferences pane, add each GitHub account interactively, choose HTTPS
or SSH, and verify the visible username before cloning or pushing. Never
automate the browser login, password, two-factor prompt, OAuth consent, token,
or SSH private-key entry.

Keep these three concerns separate:

1. **Git engine:** embedded or system Git.
2. **Authentication:** which GitHub account and credential may access the
   remote repository.
3. **Commit identity:** the `user.name`, `user.email`, and optional signing key
   written into commits.

Set commit identity locally for every repository whose owner differs from the
default identity:

```sh
git -C <repository> config --local user.name "<name>"
git -C <repository> config --local user.email "<verified-email>"
git -C <repository> config --local --get-regexp '^user\\.|^commit\\.gpgsign$'
```

For SSH, use a separate key and host alias per GitHub account, then set each
repository remote to the intended alias, for example
`git@github-personal:<owner>/<repo>.git` and
`git@github-work:<owner>/<repo>.git`. Keep `~/.ssh/config`, private keys, and
Keychain records machine-local and secret. For HTTPS, verify the selected
Sourcetree account and credential before the first push; the shared
`github.com` hostname can otherwise make account selection ambiguous.

Adding an account is not authorization to clone, push, change a remote, or
rewrite repository identity. Apply those changes one repository at a time
through `inspect → plan → confirm → apply → verify`.

## Verification

```sh
brew list --cask --versions sourcetree
/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' \
  /Applications/Sourcetree.app/Contents/Info.plist
/Applications/Sourcetree.app/Contents/Resources/git_local/bin/git --version
```

- [ ] Confirm Homebrew records the `sourcetree` cask.
- [ ] Confirm `/Applications/Sourcetree.app` exists and launches.
- [ ] Confirm Bundle ID `com.torusknot.SourceTreeNotMAS`.
- [ ] Confirm the embedded Git executable works.
- [ ] Confirm Preferences → Git is set to embedded Git.
- [ ] For each added account, verify the visible username without recording a
      credential.
- [ ] For each managed repository, verify remote URL, fetch/push access, local
      commit identity, and signing policy independently.

An account appearing in the sidebar is not proof that the intended repository
will push with that account. Perform a bounded read or push only after the user
authorizes the exact repository operation.

## Rollback

Uninstalling the app does not authorize deleting Sourcetree preferences,
Keychain items, SSH keys, repository configuration, or local repositories:

```sh
brew uninstall --cask sourcetree
```

Use `brew uninstall --zap --cask sourcetree` only after separately reviewing
and explicitly approving every support path it removes. Account-token removal,
SSH-key retirement, and repository remote changes are separate destructive
actions.

## Evidence and notes

- Atlassian embedded/system Git documentation:
  `https://support.atlassian.com/sourcetree/kb/using-embedded-git-or-system-git-in-sourcetree/`
- Atlassian multiple-account documentation:
  `https://confluence.atlassian.com/get-started-with-sourcetree/connect-your-bitbucket-or-github-account-847359096.html`
- Homebrew Cask: `sourcetree`

Never paste a machine-local record, completed checkbox, detected version,
account identity, credential-helper output, token, SSH configuration, or
timestamp back into this tracked guide.
