---
name: install-macos-apps
description: Scan a Mac for installed applications, compare it with a persistent personal macOS app catalog, and create or execute a capacity-aware installation plan. Use when setting up a new Mac, auditing missing apps, maintaining a personal app inventory, installing selected apps with Homebrew, or documenting download sources, accounts, licenses, privacy permissions, system preferences, hardware mappings, and post-install verification.
---

# Install My macOS Apps

Use this skill from its synced source folder. Treat the catalog and tracked
configuration as desired state; never infer that an app, permission, account,
or preference is ready merely because an installer, receipt, entitlement, or
documentation entry exists.

## Operating contract

Read `VERSION` as the version source of truth. Before release-status claims,
run `python3 scripts/validate_release_contract.py` and read:

- [release-acceptance-matrix.json](references/release-acceptance-matrix.json)
  for the single frozen 0.1.0 behavior contract;
- [release-roadmap.md](references/release-roadmap.md) for version scope;
- [product-ideas.md](references/product-ideas.md) only for uncommitted ideas.

Do not describe `interface_limited`, `deferred`, or `excluded` behavior as
supported. A `release_candidate` is not released. Version changes, commits,
pushes, tags, releases, and App Store submissions require separate explicit
authorization.

The mission is one-sync Mac readiness through a bounded
`scan → plan → authorize → apply → verify → record` workflow. Keep data in
four layers:

1. Public policy and engine: `components/`, `references/`, `settings/`,
   `scripts/`, and this entry point.
2. iCloud-synced personal configuration: `Private/`; the directory stays next
   to the engine for one-folder portability but is ignored by Git. Identifiers
   and approved preferences may sync through iCloud; secrets may not.
3. Machine-local observations: resolve with
   `python3 scripts/state_paths.py path`.
4. Secrets and grants: Keychain or another user-controlled store; never Git.

Read [configuration-layers.md](references/configuration-layers.md) before
moving configuration between layers. Read
[machine-local-state.md](references/machine-local-state.md) before state
migration or cleanup. Preserve unknown fields and existing behavior during
migrations.

## Reference routing

Read the directly linked reference completely before acting in that domain.
Do not load unrelated references.

| Domain | Required reference | Use when |
| --- | --- | --- |
| Runtime, Python, Android, and audio models | [runtime-and-developer-baseline.md](references/runtime-and-developer-baseline.md) | Managing shared Python Core, Android tools, Whisper, or optional audio models |
| Permissions, preferences, bootstrap, and TCC cleanup | [permissions-preferences-bootstrap.md](references/permissions-preferences-bootstrap.md) | Inspecting permissions, system preferences, bootstrap, iCloud/Git preflight details, or stale TCC state |
| Keyboard and Logitech hardware | [keyboard-and-logitech.md](references/keyboard-and-logitech.md) | Managing K240/MX Keys mappings, listeners, Solaar, or receiver battery telemetry |
| Startup, Dock, and macOS security | [startup-dock-and-security.md](references/startup-dock-and-security.md) | Auditing Login Items, LaunchAgents, Dock order, or Gatekeeper policy |
| Application installation | [application-installation-workflow.md](references/application-installation-workflow.md) | Scanning, planning, installing, using App Store/WebCatalog/official sources, or updating component documentation |
| Unified CLI | [macomrade-cli.md](references/macomrade-cli.md) | Routing scan, plan, apply, verify, drift, diagnostics, or migration through the stable repository-local command |
| JSON Schema and migration | [schema-and-migration.md](references/schema-and-migration.md) | Validating or migrating catalog, settings, Private overlay, plan, state, or diagnostic JSON |
| Redacted diagnostic bundle | [redacted-diagnostic-bundle.md](references/redacted-diagnostic-bundle.md) | Previewing or exporting a bounded support ZIP without credentials, private content, machine state, or raw TCC data |
| Supply-chain policy | [source-policy.md](references/source-policy.md) | Reviewing taps, trust, npm versions, GitHub artifacts, vendor downloads, or decrypted IPA provenance |
| Clean-Mac release acceptance | [clean-mac-release-acceptance.md](references/clean-mac-release-acceptance.md) | Preparing or running the unused/new-Mac 0.1.0 hardware acceptance gate |
| Application maintenance | [application-maintenance.md](references/application-maintenance.md) | Handling GUI/CLI pairs, duplicate bundles, helper cleanup, browser downloads, Chrome profiles, GitHub CLI, Docker retirement, or catalog edits |
| X read and account operations | [x-cli-operations.md](references/x-cli-operations.md) | Finding X users, reading recent posts, choosing `x` versus official `xurl`, or preparing a confirmed follow/unfollow operation |
| Machine-role Profiles | [machine-role-profiles.md](references/machine-role-profiles.md) | Building a role-based application plan or explaining role inheritance and overrides |
| Localization and accessibility | [localization-accessibility.md](references/localization-accessibility.md) | Adding user-facing text, terminal/HTML reports, or locale/accessibility behavior |
| App Adapter SDK | [app-adapter-sdk.md](references/app-adapter-sdk.md) | Adding or running WeChat, Claude VM, or future application lifecycle adapters |
| Performance and resources | [performance-benchmarks.md](references/performance-benchmarks.md) | Measuring command time, memory, output, state growth, or regression budgets |
| Accessible audit reports | [audit-reports.md](references/audit-reports.md) | Rendering a terminal or HTML audit view from existing JSON evidence |
| Low-noise Drift Monitor | [drift-monitor.md](references/drift-monitor.md) | Running or scheduling deduplicated, battery-aware read-only drift checks |
| Public repository release | [public-release-readiness.md](references/public-release-readiness.md) | Auditing, separating personal configuration, licensing, rehearsing, or changing repository visibility |
| Local macOS account removal | [account-removal.md](references/account-removal.md) | Retiring a local account through preflight, visible authorization, deletion, and post-delete verification |

App-specific installation and verification details live in the catalog entry's
`guide` under `components/`. Read that guide before changing the app.
Detailed component instructions are indexed by the catalog and
`components/README.md`; keep the catalog as installation metadata source of
truth and every guide path repository-relative.
Additional specialized references already linked by the six domain references
remain supporting evidence, not substitutes for this entry point.

## Mandatory execution sequence

### 1. Protect repository integrity

Before every Git-dependent operation—including status, diff, validation used as
release evidence, staging, commit preparation, submodule work, or history
inspection—run:

```sh
python3 scripts/icloud_git_guard.py inspect --repo .
```

This repository intentionally remains in iCloud Drive. If the guard reports
`dataless`, evicted, unreadable, or incomplete content, stop and follow
[icloud-git-integrity.md](references/icloud-git-integrity.md). Never interpret
a placeholder as deletion, relocate the repository as a workaround, or repair
Git before required content is materialized.

### 2. Resolve state and permission prerequisites

Resolve machine-local state once and propagate it to child commands:

```sh
STATE_DIR="$(python3 scripts/state_paths.py path)"
```

Before protected reads, run the permission inventory described in
[permissions-preferences-bootstrap.md](references/permissions-preferences-bootstrap.md).
For Chrome profile work, prove the current execution host can read
`~/Library/Application Support/Google/Chrome/Local State`. If access is
denied, stop; never report profiles as missing from an `Operation not
permitted` result.

Automatically complete ordinary non-secret macOS UI steps within the requested
scope. Hand off only when macOS requires an administrator password, Apple ID,
security confirmation, or another secret. Never type or expose secrets.

### 3. Inspect before planning

Run a fresh scan, then plan from that scan:

```sh
python3 scripts/macos_apps.py scan
python3 scripts/macos_apps.py plan --profile auto
```

Use `portable` below 512 GB and `expanded` at 512 GB or above unless the
user explicitly chooses another profile. Review missing items, source
mismatches, version issues, disk impact, dependencies, account reminders,
permissions, and follow-up checks. A receipt or Homebrew record is not proof
that a usable app bundle exists.

### 4. Bound and authorize the change

Present exact targets and commands before applying. GUI applications, App Store
items, WebCatalog wrappers, website downloads, and any item involving accounts,
permissions, or licenses are handled one at a time. Approved CLI-only Homebrew
items may be batched up to five.

Do not install, reinstall, replace, delete, grant, connect, or apply merely
because the plan recommends it. Obtain explicit confirmation for the concrete
action. Before a heavy app on a portable profile, state the space impact and
obtain an explicit override.

### 5. Execute through the declared source

Use `scripts/macos_apps.py install` for supported Homebrew actions, first
without `--apply`, then with `--apply` only after approval. Follow each
component guide for taps, trust, installers, reboot requirements, supported
URLs, and post-install checks.

For App Store entries, open the canonical
`macappstore://itunes.apple.com/app/id...` URL and continue serially. Opening
a page is not installation evidence. For official-web or browser workflows,
verify the domain and download artifact before opening it. Never silently
substitute a different source.

### 6. Verify by read-back

After each mutation, verify the exact target through independent evidence:
bundle/path and launch, command path and version, source receipt, service state,
preference read-back, profile identity, permission-dependent workflow, or the
component's documented check. Record unavailable interfaces as unavailable,
not empty or successful.

Account identifiers from the merged Private overlay are prompts only. Never
automate login or account switching. Compare the visible account when the
workflow permits it, and stop on mismatch.

### 7. Record and re-scan

Write versions, paths, timestamps, grants, measurements, command output, and
completion evidence only to machine-local state. Keep reusable public intent in
tracked policy and personal intent in iCloud-synced, Git-ignored `Private/`.
Re-run the relevant scan/check and leave an
explicit unresolved item when verification is incomplete.

## Mutation contract

Every mutating workflow follows:

```text
inspect → plan → confirm → apply → verify → record
```

Use stable action IDs and exact targets where available. Provide backup or
rollback notes before destructive/high-impact work. Require typed confirmation
when a workflow defines an exact phrase. On interruption, inspect both source
and destination before retrying. A repeated apply must either be idempotent or
stop with a clear already-applied state.

Never turn a design, dry run, opened page, synthetic fixture, cask receipt, or
entitlement into a claim of real completion.

Read
[mutation-transaction-contract.md](references/mutation-transaction-contract.md)
before changing or adding a mutation. The machine-readable registry assigns
stable action IDs and target, confirmation, verification, rollback,
interruption, idempotency, and record contracts. Run
`python3 scripts/validate_mutation_contracts.py` after any mutation change.

## Catalog and documentation contract

`references/app-catalog.json` is installation metadata source of truth.
The iCloud-synced `Private/app-catalog-overlay.json` supplies approved personal
fields when present; public-only clones operate without it. Keep
catalog names stable, declare the intended source, link a component guide, and
run catalog/frontmatter audits after edits.

Component Markdown stores reusable installation and verification know-how, not
current-machine status. Runtime versions, installed state, paths, dates,
permissions, and measurements belong in machine-local state. Update component
documentation only when source, dependency, authorization, configuration,
verification, cleanup, rollback, or durable know-how materially changes; do
not churn files for routine scans or version refreshes.

Read
[component-state-boundary.md](references/component-state-boundary.md) before
changing a component template, generator, repair script, or current-status
prose. Run `python3 scripts/component_state.py audit` after component edits.

Every generated component guide must satisfy the frontmatter template and
catalog audit. Read
[application-installation-workflow.md](references/application-installation-workflow.md)
for the exact source-specific and component-integrity rules.

## Persistent records and local validation

Runtime state defaults to
`~/Library/Application Support/install-macos-apps/state/<hashed-machine-id>/`.
A command-level `--state-dir` overrides
`INSTALL_MY_MACOS_APPS_STATE_DIR`, which overrides the default. The tracked
`state/README.md` and `state/locator.json` are compatibility locators only.

After substantive changes, run:

```sh
python3 scripts/icloud_git_guard.py inspect --repo .
./bin/macomrade validate --json
./bin/macomrade verify schemas
python3 scripts/release_check.py
```

`./bin/macomrade` is the stable repository-local entry point. Existing
`python3 scripts/*.py` commands remain supported compatibility shims. The
dispatcher never adds `--apply`, a confirmation phrase, a privilege, or a
credential; a route name is not mutation authorization.

Use local macOS validation as the default 0.1.0 gate. Do not create or restore
push, pull-request, or scheduled GitHub Actions unless the user explicitly
changes this policy. A hosted runner is not evidence for target-Mac apps,
accounts, TCC grants, hardware, or preferences.

Read [testing-contract.md](references/testing-contract.md) for fixture
boundaries and negative-path requirements. Add `--include-live-smoke` only when
the current Mac integration check is required; it remains dry-run and is not
clean-Mac evidence.

## Safety rules

- Treat Homebrew bootstrap, downloads, and every `--apply` as external changes
  requiring explicit user approval.
- Never automate login, license entry, security/privacy grants,
  device-management enrollment, VPN connection, purchases, passwords, API
  keys, recovery codes, private keys, cookies, or session material.
- Never copy raw TCC databases, authorization tokens, account sessions, private
  document contents, or machine observations into tracked configuration.
- Never weaken Gatekeeper, SIP, FileVault, Firewall, or MDM policy from an
  observed current state; use a separately reviewed security decision.
- Never delete application data, support files, cloud content, user accounts,
  or legacy state without the workflow's exact reviewed target and explicit
  confirmation.
- Preserve unrelated worktree changes. Do not reset, checkout, overwrite, or
  clean files that are outside the approved task.
- Never run `git commit`, push, tag, release, or submodule-pointer commit on
  your own initiative. Only do so after the user explicitly requests that
  publication action.
