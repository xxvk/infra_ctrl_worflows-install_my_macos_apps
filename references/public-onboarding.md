# Public onboarding

This guide is the public entry point for evaluating and adopting macomrade
without inheriting the original author's accounts, machine state, or personal
configuration. The repository is a 0.2.0 release candidate; completing
this guide does not declare a stable release or authorize a GitHub visibility
change.

## Contents

- [Audience and support scope](#audience-and-support-scope)
- [Platform support matrix](#platform-support-matrix)
- [Prerequisites](#prerequisites)
- [Ten-minute read-only quick start](#ten-minute-read-only-quick-start)
- [Private overlay setup](#private-overlay-setup)
- [Permissions and secrets](#permissions-and-secrets)
- [Known limitations](#known-limitations)
- [Uninstall and rollback](#uninstall-and-rollback)
- [Troubleshooting](#troubleshooting)

## Audience and support scope

macomrade is for individual Mac owners and developers who want a reviewable,
local-first definition of applications, preferences, permissions, and machine
lifecycle policy. It assumes comfort with Terminal, Git, JSON/YAML review, and
macOS permission prompts.

The current release candidate provides reusable policy, read-only inventory,
planning, explicit mutation contracts, validation, and machine-local evidence.
It is not an unattended enterprise provisioner, MDM replacement, backup
product, malware remover, credential manager, or guarantee that every catalog
application is available in every country or macOS release. Support is
best-effort until a stable version is released.

## Platform support matrix

| Host | Status | Current boundary |
| --- | --- | --- |
| Apple silicon Mac on a currently supported public macOS release | Primary release-candidate target | Hermetic validation is available; live behavior still depends on installed apps, permissions, accounts, and hardware. |
| Apple silicon Mac on a macOS beta or prerelease | Best effort | Apple and Homebrew interfaces may change; warnings and source mismatches require manual review and are not release evidence. |
| Intel Mac | Unverified | Some scripts discover `/usr/local` Homebrew, but there is no completed Intel acceptance run and no support claim yet. |
| Linux or Windows | Unsupported as a managed host | Some pure-Python tests may run, but application inventory, TCC, `defaults`, LaunchServices, Dock, and other host integrations require macOS. |

No exact minimum macOS version is promised before an independent Clean-Mac
release-candidate run establishes one. Record `sw_vers` and `uname -m` when
reporting a platform-specific problem.

## Prerequisites

The read-only evaluation needs:

- a Mac and a normal local user account;
- Terminal or another shell;
- Git and Python 3;
- a locally materialized clone of the repository.

Homebrew is not required to validate the repository or generate the first app
inventory and plan. It is required for Homebrew-backed installation workflows.
Apple ID, administrator password, Full Disk Access, Accessibility, Screen
Recording, and other protected permissions are not required for the quick
start below. Individual later workflows may require them and must say so before
they run.

If `git` is unavailable, install Apple's Command Line Tools through the normal
macOS prompt before continuing. Do not pipe an unreviewed network script into a
shell merely to satisfy a prerequisite.

## Ten-minute read-only quick start

These commands clone files and write temporary JSON evidence under `/tmp`, but
they do not install or remove applications, change settings, request protected
permissions, invoke `sudo`, or contact an App Store account. The public clone
requires no GitHub account or repository credential.

```sh
git clone https://github.com/xxvk/macomrade.git
cd macomrade
export MACOMRADE_PUBLIC_ONLY=1
export INSTALL_MY_MACOS_APPS_STATE_DIR=/tmp/macomrade-public-quickstart

python3 scripts/bootstrap_validate.py
./bin/macomrade validate
./bin/macomrade verify schemas
./bin/macomrade scan apps
./bin/macomrade plan apps --profile auto
```

Review the command output and the temporary records before doing anything
else:

```sh
find "$INSTALL_MY_MACOS_APPS_STATE_DIR" -maxdepth 1 -type f -print
```

The app plan is advice, not authorization. Do not move from `plan` to `apply`
until you understand the selected machine profile, source mismatches, manual
handoffs, account requirements, and exact external changes. The repository-
local launcher never adds mutation flags on the user's behalf.

`MACOMRADE_PUBLIC_ONLY=1` explicitly disables the local Private app-catalog
overlay even if this checkout happens to sit beside an existing iCloud-synced
`Private/` directory. This prevents personal account prompts or private catalog
choices from entering a public evaluation result.

## Private overlay setup

A public clone works without `Private/`. Create an overlay only when you want
to sync personal desired configuration through your own iCloud Drive folder.
Start with the fictional templates under `examples/private/`; copy only the
files you intend to maintain:

```sh
mkdir -p Private/keyboards
cp examples/private/manifest.json Private/manifest.json
cp examples/private/app-catalog-overlay.json Private/app-catalog-overlay.json
cp examples/private/chrome-profiles.json Private/chrome-profiles.json
cp examples/private/dock-order.json Private/dock-order.json
cp examples/private/system-preferences-values.json Private/system-preferences-values.json
cp examples/private/keyboard.yaml Private/keyboard.yaml
cp examples/private/keyboards/example-keyboard.yaml Private/keyboards/example-keyboard.yaml
python3 scripts/config_layers.py audit
git check-ignore -v Private/manifest.json
```

Replace fictional values locally and keep the directory ignored by Git. The
public base loads first and the Private overlay loads second. Do not add Git
negation rules for selected Private files, and do not put passwords, tokens,
private keys, recovery codes, raw TCC databases, cookies, sessions, or private
document contents in either layer. See
[`configuration-layers.md`](configuration-layers.md) for merge and migration
rules.

## Permissions and secrets

macOS privacy grants are machine-local decisions enforced by TCC. They cannot
be copied from another Mac, truthfully represented by an application's code
signature, or restored by writing the TCC database. This repository records
the desired permission policy and can inspect supported authorization state;
the user must approve protected access visibly on each Mac.

The normal transaction is:

```text
inspect requirement → open the relevant system pane or trigger the request
→ user approves protected access → read back the resulting state
```

Administrator passwords, Apple ID credentials, passkeys, API keys, OAuth
tokens, and recovery material stay in Keychain or another user-selected secret
store and are never collected by the repository. See
[`permissions-preferences-bootstrap.md`](permissions-preferences-bootstrap.md)
for supported inspection and handoff behavior.

## Known limitations

- Version 0.2.0 remains a release candidate. There is no stable tag or public
  compatibility promise yet.
- A genuine unused Clean-Mac acceptance run remains externally deferred;
  already configured Macs cannot prove first-boot behavior.
- Apple silicon is the primary target. Intel behavior is unverified.
- App Store installation, account login, security prompts, Touch ID, passkeys,
  and some vendor installers require visible user interaction.
- macOS does not expose supported automation for replaying every TCC grant,
  menu-bar arrangement, widget layout, or application-internal preference.
- Website-installed applications may not retain enough portable evidence to
  prove their original download source; `manual_or_unknown` is not automatic
  proof of a bad install.
- Public policy and a user's iCloud-synced Private overlay can converge desired
  configuration, but machine-local observations and actual effects must be
  checked separately on every Mac.
- The repository currently uses local macOS release checks rather than hosted
  GitHub Actions because an ephemeral runner cannot represent real apps,
  accounts, hardware, TCC grants, or system preferences.

## Uninstall and rollback

The quick start installs no global command and changes no Mac settings. The
`macomrade` launcher runs from the repository, so removing an evaluation clone
does not require an uninstaller. Temporary quick-start evidence is confined to
the selected `/tmp/macomrade-public-quickstart` path.

Removing the repository does not uninstall applications or reverse settings
that a user later applied. There is intentionally no universal “undo the Mac”
command. Before every supported mutation, review its exact plan, backup or
rollback capability, verification method, and irreversible boundary. Use the
component-specific uninstall or rollback path recorded by that transaction;
never infer that deleting an application bundle also safely deletes its data.

If an operation is interrupted, stop, retain its machine-local transaction
record, inspect current state, and resume or roll back only through the same
operation contract. See
[`mutation-transaction-contract.md`](mutation-transaction-contract.md) and
[`application-maintenance.md`](application-maintenance.md).

## Troubleshooting

| Symptom | Safe next step |
| --- | --- |
| `python3` or `git` is not found | Install Apple's Command Line Tools through the macOS-supported prompt, then open a new Terminal. |
| `./bin/macomrade` is not executable | Run `python3 scripts/macomrade.py validate`; then inspect whether the checkout preserved executable modes before changing permissions. |
| iCloud reports an unavailable or `dataless` repository file | Stop Git-dependent work and run `python3 scripts/icloud_git_guard.py inspect --repo .`; follow the materialization guide instead of treating the file as deleted. |
| Homebrew is absent | The first scan and plan can continue with reduced source evidence. Install Homebrew only after reviewing the official source and supply-chain policy. |
| A scan reports permission-limited data | Read the named permission requirement; grant it visibly only if that feature is wanted, then rerun and read back. Do not edit TCC databases. |
| `Private/` is absent | This is valid for a public clone. Use public defaults or create selected overlays from `examples/private/`. |
| Planning reports no prior scan | Keep the same `INSTALL_MY_MACOS_APPS_STATE_DIR`, rerun `./bin/macomrade scan apps`, then plan again. |
| Homebrew warns about a prerelease macOS version | Treat results as best effort, avoid broad upgrades, and do not report the beta run as stable-platform acceptance. |
| A command would require `sudo`, account credentials, or a security confirmation | Stop at the visible handoff. Never paste the secret into an issue, diagnostic bundle, repository file, or agent chat. |

When asking for help, provide the command, exit status, macOS version,
architecture, and redacted error category. Review every diagnostic artifact
before sharing it and exclude Private files, tokens, account identifiers, raw
permission databases, and document contents.
