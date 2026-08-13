# TODO

Product-level scope, release status, acceptance gates, and candidate ideas live
in [`references/release-roadmap.md`](references/release-roadmap.md) and
[`references/product-ideas.md`](references/product-ideas.md). This file tracks
implementation details; an unchecked item is not automatically assigned to a
release.

## 0.1.0 release-candidate work

The repository remains in its current iCloud Drive location. Moving it out of
iCloud is not a product task. Instead, the implementation must treat
iCloud/File Provider behavior as a supported operating constraint.

The following list is the accepted release backlog. It contains exactly 20
items and is divided by release impact so accepted enhancements do not
silently expand the 0.1.0 release-candidate gate.

### P0 — blocks a validated 0.1.0 release candidate

- [x] **RC-01 — Add iCloud-aware Git integrity protection without relocating
      the repository.** Detect `dataless`, evicted, incomplete, or unreadable
      Git objects and required working files before Git-dependent operations;
      document and verify “Keep Downloaded” for the repository; stop safely
      instead of interpreting unavailable data as deletion or corruption;
      provide materialize/retry and fresh-clone recovery paths; and verify with
      `git fsck --full`, `git status`, and `git diff --check` when files are
      locally available.
      Resolved: added `scripts/icloud_git_guard.py`, 11 hermetic tests, the
      grouped/explicit-apply/exact-fallback download workflow, runtime
      capability detection for modern macOS where `fileproviderctl`
      advertises no `materialize` command, and the copy-first recovery guide
      in `references/icloud-git-integrity.md`. On this iCloud-backed submodule,
      the guard resolved the parent gitdir, found 323 remaining `dataless`
      objects after the grouped request, materialized them with `brctl`,
      rechecked 809 critical paths with zero findings, and then passed
      `git status --short`, `git diff --check`, and `git fsck --full`.
      Finder **Keep Downloaded** remains a visible manual preference; absence
      of `dataless` is the supported CLI read-back.
- [x] **RC-02 — Move runtime `state/` to truly machine-local storage.** Default
      to `~/Library/Application Support/install-macos-apps/state/<machine-id>/`,
      support an explicit `--state-dir` or environment override, retain a
      compatibility locator in the repository, and migrate all existing state
      copy-first with count/hash/read-back verification before any source
      cleanup.
      Resolved: added the machine-scoped resolver and command/environment
      overrides, migrated 651 files (40,209,928 logical bytes) copy-first,
      verified every destination with SHA-256, and recorded the verified
      machine-local migration manifest. After the exact
      `REMOVE VERIFIED LEGACY STATE` confirmation, the cleanup transaction
      re-hashed both sides, removed all 651 manifest-bound legacy files, and
      preserved only tracked `state/README.md` and `state/locator.json`.
- [x] **RC-03 — Separate public engine, private configuration,
      machine state, and secrets without losing existing configuration.**
      Preserve every currently tracked configuration value and its behavior;
      introduce a Private overlay for existing and future
      user-approved identifiers/preferences; keep runtime observations
      machine-local; keep passwords, tokens, private keys, raw TCC databases,
      and session material outside Git; add deterministic merge precedence and
      backward-compatible migration tests.
      Foundation complete: added `Private/manifest.json`,
      `scripts/config_layers.py`, fixture tests, secret-key/path guards, and
      `references/configuration-layers.md`. Existing personal values remain in
      their historical tracked paths; migrate consumers one at a time before
      marking RC-03 complete. Migrated Chrome profiles through a compatibility
      locator and moved ChatGPT/Claude account preferences into the layered
      Private app-catalog overlay without changing generated plan behavior.
      Migrated Dock order and confirmed allowlisted macOS preference values to
      Private files while retaining compatible `settings/` locators
      and redirecting Dock save plus preference check/apply consumers. Migrated
      personal keyboard selection, dictation preferences, and the K240 device
      mapping to Private YAML with strict compatibility locators and
      manifest audit coverage. Moved the intended GitHub CLI account identifier
      out of its public component guide and into the existing Private
      app-catalog overlay. Removed the stale tracked M4B security snapshot after
      verifying that per-machine security results already live in ignored local
      preference reports; the public baseline now contains only a new-Mac
      inspection and decision contract.
      The 0.1.1 publication decision supersedes Git tracking for this layer:
      `Private/` stays in the same iCloud project, is ignored by Git, and uses
      fictional public templates under `examples/private/`.
- [x] **RC-04 — Freeze the 0.1.0 release-candidate contract.** Maintain one
      acceptance matrix for supported, interface-limited, deferred, and
      deliberately excluded behavior; require evidence for each supported
      capability; and keep `VERSION` at `0.1.0` while the roadmap status is
      `release_candidate`.
      Resolved: added one canonical 28-row JSON matrix with all four
      classifications, 12 evidence-backed supported capabilities, and explicit
      behavior boundaries. `scripts/validate_release_contract.py` now binds the
      matrix to `VERSION=0.1.0`, the roadmap's `release_candidate` status,
      unique IDs, complete classification coverage, repository-contained
      evidence paths, and mandatory evidence for every supported row; three
      hermetic tests and the local smoke gate cover valid, missing-evidence,
      and version/status-drift cases.
- [x] **RC-05 — Split the 1,445-line `SKILL.md` into a concise entry point and
      focused references.** Keep trigger, safety, routing, and mandatory
      workflow rules in `SKILL.md`; move domain procedures into directly
      linked reference files; avoid deep reference chains; and verify that no
      existing rule or configuration is lost.
      Resolved: reduced the entry point from 1,495 to 243 lines while retaining
      the operating contract, four configuration layers, mandatory seven-step
      workflow, transaction contract, catalog/documentation rules, validation,
      and safety rules. Moved the detailed procedures into six directly linked,
      single-level domain references with contents sections. Added
      `scripts/validate_skill_structure.py` plus hermetic tests to enforce the
      500-line ceiling, all routes, preserved domain anchors, and local-link
      integrity; the coverage review found only intentionally superseded
      pre-RC-02/03 state paths, identifiers, and configuration locations.
- [x] **RC-06 — Establish a hermetic automated test system.** Add fixture-based
      unit and contract tests for catalog/schema validation, source/version
      detection, planning, migration, and command rendering; fake Homebrew,
      App Store, TCC, defaults, and filesystem responses; prove dry-run makes
      zero external changes; test negative and interrupted paths; and test
      repeat apply for idempotency without requiring a live configured Mac.
      Keep the complete suite available through one local release-check entry
      point. GitHub Actions is not part of the 0.1.0 release gate unless the
      user explicitly changes the local-validation policy.
      Resolved: added static app/platform fixtures and 20 new contracts for
      catalog errors, source/version detection, filesystem inventory, portable
      planning, deterministic tap/install rendering, Homebrew/App Store
      evidence, read-only TCC/defaults behavior, dry-run zero process
      execution, invalid/oversized targets, interrupted apply, and repeated
      idempotent package-manager commands. Existing migration tests retain
      conflict, unavailable-source, preview, and exact-confirmation coverage.
      `scripts/release_check.py` is now the single entry point: eight hermetic
      stages by default and an explicit ninth live-mac smoke stage only with
      `--include-live-smoke`. The final run passed all 58 tests, both modes,
      Skill validation, and diff checks without hosted CI.
- [x] **RC-07 — Give every mutation one transaction contract.** Standardize
      `inspect → plan → confirm → apply → verify → record`, with stable action
      IDs, exact targets, backups or rollback notes, typed confirmation for
      destructive/high-impact actions, interruption recovery, idempotency, and
      read-back evidence.
      Resolved: registered all supported mutation actions in one
      machine-validated contract registry with exact targets, risk,
      confirmation, verification, recording, rollback, interruption, and
      idempotency semantics. Every implementation now both declares and emits
      its stable action ID; Capacities and Skill-runtime removal gained exact
      typed confirmation tokens. Added the reusable contract/hash helper,
      validator, reference, acceptance-matrix evidence, bootstrap/release-check
      integration, and seven focused tests. Final validation passed all 65
      hermetic tests, all nine default release-check stages, and all ten stages
      including the current-Mac dry-run smoke.
- [x] **RC-08 — Remove current-machine state from component documentation.**
      Store desired/reusable facts in tracked component/config documents and
      detected versions, paths, timestamps, grants, measurements, and install
      status only in machine-local state; strengthen audits so ambiguous
      `installed`/`verified` prose cannot produce a false clean result; migrate
      existing documents without dropping reusable installation know-how.
      Resolved: copied 174 historical findings from 129 component guides into
      three timestamped machine-local migration records with exact source
      hashes, lines, codes, and text before normalization. Removed local
      evidence blocks, completed checkboxes, versions, measurements, state
      links, current-status tables, and machine-scoped lifecycle claims while
      preserving source, configuration, verification, and rollback know-how.
      Added the component-state boundary reference, 21st mutation contract,
      runtime audit/migration tool, frontmatter/release-check integration, and
      eight focused tests. Refactored the template and all known
      enrichment/repair generators so runtime observations cannot be written
      back into tracked guides. Final validation passed 129 guides with zero
      violations, all 73 hermetic tests, all ten default release-check stages,
      and all eleven stages including current-Mac dry-run smoke.
- [x] **RC-09 — Complete a supply-chain and installation-source audit.**
      Inventory and classify Homebrew taps/trust, App Store URLs, npm globals,
      `curl | shell`, GitHub branch downloads, official installers, PlayCover,
      IPA, and decrypted-package sources; pin versions/commits and verify
      hashes/signatures where supported; record provenance and rollback; and
      isolate high-risk personal sources from the reusable public core.
      Completed: classified all 130 catalog entries into ten source classes;
      pinned KeyStats and PlayCover to reviewed tap commits and package-scoped
      cask trust; pinned Wrangler and WordPress Studio CLI npm versions; pinned
      Solaar's signed 1.1.19 release artifact to a full commit and SHA-256; and
      removed all active mutable network-to-shell paths, including automatic
      Homebrew bootstrap. Decrypted-IPA source labels now live only in iCloud
      `Private/`, with no direct URL. Added source policy, static/live audit,
      provenance in install records, the 22nd mutation contract, and
      machine-local supply-chain capture. M4b read-back matched both managed
      taps and npm versions; four other taps are explicitly inventoried as
      observed-unmanaged with dispositions rather than silently authorized.
      Final validation passed 130 source records, 129 component guides with
      zero machine-state violations, 82 hermetic tests, all eleven default
      release stages, and all twelve stages including live macOS dry-run smoke.

### P1 — blocks changing 0.1.0 from release candidate to shipped

- [ ] **RC-10 — Pass a genuine Clean-Mac release acceptance run.** Prepare the
      deterministic checklist, evidence bundle, rollback drill, and acceptance
      script now; mark the hardware run `blocked_external` until an unused/new
      Mac is available (tentatively September); do not represent three
      previously configured Macs as clean-machine evidence.
      Status: `blocked_external`; tooling preparation is complete. Added a
      machine-validated 13-gate contract, tracked status, operator checklist,
      and machine-local acceptance session state machine. Initialization
      requires the exact unused/new-Mac attestation and a clean full Git
      commit. Evidence is JSON-only, secret-key checked, path/email redacted,
      copied into a bounded bundle, and recorded with source and bundle
      SHA-256. Gate-specific semantic validators reject generic pass JSON:
      automated gates must match their real result structures, interactive
      gates use a typed evidence envelope, and CM-12 requires distinct install
      and uninstall phases. Finalization rejects changed source, changed
      contract, pending, blocked, failed, under-evidenced, missing, malformed,
      or tampered evidence and explicitly leaves publication unauthorized.
      CM-12 requires a real drift-monitor
      install/read-back/uninstall/read-back rollback drill. The remaining work
      is only the genuine hardware execution and review; current M4 machines
      must not initialize an eligible session. Tooling validation passed 13
      focused Clean-Mac tests, all 95 hermetic tests, all 12 default release
      stages, and all 13 stages including current-Mac dry-run smoke; none of
      these substitute for the blocked external hardware run.
- [x] **RC-11 — Provide one distinct, conflict-checked CLI entry point.**
      Treat `mac-ctl` as a rejected placeholder, run a naming exercise, check
      likely Homebrew/npm/GitHub/domain collisions, select a name with product
      character, and route scan, plan, apply, verify, drift, diagnostics, and
      migration commands through it while retaining compatibility shims.
      Completed: selected the repository-local CLI name `macomrade` while
      leaving the future product name undecided. A dated, point-in-time
      exact-name audit covered local PATH, Homebrew formula/cask, npm, PyPI,
      crates.io, GitHub, Mac App Store, and `.com`/`.net`; unrelated music and
      username uses are recorded, and the audit is explicitly not trademark
      clearance or name reservation. `MacWeave` was abandoned and the
      intermediate `mac-comrade` spelling was superseded before release.
      `mac-buro` and `5y-plan` are reserved, unimplemented future Easter-egg
      commands and must currently fail before execution. Added a
      repository-local executable, 20 declarative
      compatibility routes across all seven required families, `--explain`,
      machine-readable route/identity contracts, and hermetic validation.
      Existing scripts remain callable and authoritative. The dispatcher
      preserves arguments, cwd, standard streams, and exit codes; rejects
      unknown routes before subprocess execution; and never adds `--apply`,
      confirmation, privileges, or credentials. Validation passed all seven
      focused CLI tests, all 102 hermetic tests, all 13 default release
      stages, and all 14 stages including current-Mac dry-run smoke.
- [x] **RC-12 — Publish formal JSON Schemas and migration tooling.** Version
      catalog, settings, private overlay, plan, state, and diagnostic formats;
      validate before use; provide upgrade/downgrade-safe migrations and
      fixtures; and preserve unknown fields when safe.
      Completed: published six Draft 2020-12 schemas and a tracked registry;
      added a standard-library validator that fails closed on unsupported
      schema keywords; validate catalog, Private overlay, generated plans, and
      release diagnostics before use; and version all newly generated app
      scan/plan/install records. Added reversible v0/v1 migration that changes
      only `schema_version`, preserves unknown nested fields, previews by
      default, requires a separate output and exact
      `WRITE SCHEMA MIGRATION` confirmation, writes atomically, refuses
      conflicts, and verifies SHA-256 read-back. Exposed schema list,
      validation, and migration through three `macomrade` routes and registered
      the 25th mutation contract. Validation passed 111 hermetic tests, all 14
      default release stages, and all 15 stages including current-Mac dry-run
      smoke with state redirected through the supported environment override.
- [x] **RC-13 — Generate a redacted diagnostic bundle.** Collect versions,
      checks, failure classes, policy hashes, and bounded logs while
      deterministically excluding secrets, account/session data, private
      filenames/content, raw TCC databases, and credentials; show a manifest
      and redaction preview before export.
      Completed: added an allowlist-only collector with six controlled
      read-only checks, six public policy hashes, normalized failure classes,
      4096-byte stdout/stderr limits, strict structured/text redaction, a
      Draft 2020-12 payload schema, and an exact in-memory payload preview.
      The bundle excludes arbitrary files, Private values and paths,
      machine-local records, account/session/host fields, credentials, home
      paths, URL queries, and raw TCC data. Dirty-source provenance records
      only status/count plus hashes of the exact implementation files, never
      Git filenames or diffs. Export requires a new `.zip`, `--apply`, and
      exact `EXPORT REDACTED DIAGNOSTICS`; an atomic hard-link publish prevents
      TOCTOU overwrite, then exact members, manifest hashes, payload schema,
      and sensitive-pattern checks are repeated on read-back. Added preview,
      validation, and export `macomrade` routes plus the 26th mutation
      contract. Independent forward testing found and drove fixes for dirty
      provenance, overwrite races, incomplete human preview, output-path
      privacy, and permissive schema fields. Validation passed 122 hermetic
      tests, all 15 default release stages, all 16 stages including current-Mac
      dry-run smoke, and a real temporary ZIP export/read-back; no artifact was
      retained or shared.
- [x] **RC-14 — Add repeatable performance and resource benchmarks.** Added
      schema-validated budgets for cold/warm inventory, plan, validation,
      drift, and migration inspection. The local runner records elapsed time,
      child-process RSS high-water mark, output bytes, and allocated state
      growth; it compares absolute and regression budgets against an optional
      per-Mac baseline. A real five-operation two-pass sample passed its
      declared budgets. Drift's normal mismatch exit is measured, not mistaken
      for a benchmark execution failure.
- [ ] **RC-15 — Generate a Release Manifest automatically.** Bind version,
      commit, schema versions, catalog/config hashes, supported macOS and
      architecture matrix, test/benchmark results, known limitations, and
      artifact provenance into a reproducible manifest; generating it does not
      authorize committing, tagging, pushing, or publishing.

### P2 — accepted 0.1.x enhancements; do not block 0.1.0

- [x] **RC-16 — Add composable machine-role Profiles.** Added a schema-validated
      base, compact, expanded, developer, robotics, content, and gaming role
      catalog. Roles compose parent-first; `auto` resolves by storage capacity;
      plans record a stable selected-app reason and explicit include/exclude
      precedence. Roles select capability only: they never grant permissions,
      sign in, buy, connect VPN, or activate a license.
- [x] **RC-17 — Generate human-friendly HTML and TUI audit reports.** Added
      zh-Hans, ja, and en terminal/HTML views for existing drift JSON. The
      summary keeps only aggregate missing-Core/source/permission/preference
      findings, omits paths and private content, uses semantic static HTML,
      WCAG-AA contrast, textual status, keyboard-readable TUI, and no scripts
      or color-only meaning. JSON remains the authoritative evidence.
- [x] **RC-18 — Define Chinese, Japanese, and English localization plus
      accessibility requirements.** Added zh-Hans, ja, and en message catalogs
      with exact message/placeholder parity tests, system-locale fallback, and
      stable English command/action IDs. The tracked accessibility contract
      requires WCAG AA contrast, keyboard-complete TUI, semantic VoiceOver
      output, and no color-only status. Historical CLI prose is intentionally
      migrated only when its workflow changes.
- [x] **RC-19 — Define an App Adapter SDK before adapters proliferate.** Added
      schema-validated metadata-only adapters for WeChat and Claude VM, with
      localized descriptions, root/data-class policy, read-only inspection,
      risk classification, and test fixtures. WeChat can only hand off to its
      official storage UI. Claude VM plans delegate only to existing named
      exact-confirmation transactions. There is deliberately no generic
      adapter apply/delete command.
- [x] **RC-20 — Add a low-noise scheduled Drift Monitor.** Replaced the weekly
      LaunchAgent's direct legacy calls with a read-only monitor that defers on
      low battery, filters by confidence, assigns stable finding IDs, suppresses
      unchanged notices by severity cooldown, bounds summaries, and persists
      only a machine-local redacted ledger. Scheduling remains opt-in through
      the existing `--apply` transaction; every repair remains separate and
      explicit. A live monitor cycle reported only existing preference drift.

## 0.1.1 — Public source release readiness

The goal is to make the reusable repository public without publishing personal
configuration or weakening the existing safety contract. Editing or completing
this list does not authorize a GitHub visibility change.

- [ ] **Runtime cleanup — migrate legacy npm-global ownership.** The Core
      contract now uses fnm Node 24 and all related CLI smoke tests pass, but
      existing `wp-studio` and `wrangler` copies remain under Homebrew's npm
      prefix. Reinstall exact pinned versions under fnm Node 24, verify command
      paths and account workflows, measure both prefixes, and remove old copies
      only after separate explicit approval. Vercel and `k6-html-reporter` are
      not Core and require individual keep/remove decisions.

- [x] **PUB-01 — Inventory and classify the publication surface.** Enumerate
      tracked files, submodules, large/generated artifacts, third-party assets,
      license obligations, personal data, organization-specific material, and
      full-history findings without copying sensitive values into reports.
      A repeatable path/count-only audit now covers the current tree and every
      reachable commit and stores evidence only in machine-local state. The
      2026-08-14 baseline inventoried 290 tracked files and 38 commits: seven
      tracked `Private/` files; four current-tree and four history finding
      categories; no large files, binary files, generated artifacts, vendored
      third-party assets, or submodules; and five missing governance files.
      It explicitly leaves publication, history rewrite, and visibility change
      unauthorized. Manual path-level classification and history strategy
      remain PUB-04.
- [x] **PUB-02 — Isolate the in-place iCloud Private overlay.** Keep all
      existing personal files under the current `Private/` path, ignore the
      entire directory in Git, preserve public-base → Private-overlay merge
      precedence, and prove public-only operation when the directory is absent.
      Completed: `Private/` is ignored and removed from the Git index while all
      seven local files remain in place for iCloud sync. Both the local Private
      mode and a temporary public-only snapshot passed all 21 release checks.
- [x] **PUB-03 — Publish complete sanitized examples.** Create fictional
      example files for every private overlay, remove author identifiers, and
      prove the public engine can scan, plan, validate, and report when no
      author-owned `Private/` directory is present.
      Completed: `examples/private/` now contains fictional manifest, account,
      Chrome, Dock, preference, and keyboard templates. The public-only
      rehearsal completed 21/21 hermetic checks with no `Private/` directory.
- [ ] **PUB-04 — Audit the complete Git history.** Scan all reachable commits
      for secrets, account identifiers, private URLs, machine paths, decrypted-
      package provenance, and personal/organization data; manually classify
      findings, rotate exposed credentials where required, and perform a
      reviewed `git filter-repo` rewrite of the current repository. Preserve a
      verified private backup; remote force-push remains separately confirmed.
- [ ] **PUB-05 — Add open-source governance.** Obtain an explicit license
      decision—Apache-2.0 is the recommended candidate—then add the license,
      required third-party notices, security policy, contribution guide, code
      of conduct, and changelog. Until then, do not call the repository open
      source.
- [ ] **PUB-06 — Build public onboarding.** Add audience and support scope,
      supported macOS/architecture matrix, prerequisites, ten-minute read-only
      quick start, private-overlay setup, permissions, known limitations,
      uninstall/rollback, and troubleshooting without personal assumptions.
- [ ] **PUB-07 — Lock the public safety and issue contract.** Keep dry-run and
      exact confirmations, prohibit secret/private-state uploads, add issue and
      responsible-disclosure guidance, and define safe redacted diagnostics for
      public support.
- [ ] **PUB-08 — Complete RC-15 Release Manifest.** Bind the candidate version,
      commit, schema/policy hashes, supported platform matrix, local validation,
      benchmark summary, known limitations, and artifact provenance without
      authorizing commit, tag, release, or publication.
- [ ] **PUB-09 — Rehearse an independent anonymous clone.** Clone the exact
      sanitized candidate without private credentials, run all hermetic checks
      and the read-only quick start, and prove that no personal overlay is
      required, fetched, generated, or committed.
- [ ] **PUB-10 — Execute the visibility transaction only after confirmation.**
      Prepare a recoverable private archive and rollback; show the exact remote,
      candidate commit, history strategy, and settings diff; obtain explicit
      authorization; change visibility once; verify anonymous web/Git access,
      repository metadata, and post-publication privacy checks.

- [x] Capacities data migration: user confirmed the migration/retention
      decision is complete and Capacities has been deleted. Do not delete any
      remaining preserved support data during a generic app scan.
- [x] After user confirmation, remove only `/Applications/Capacities.app` and
      preserve Capacities support data for a separate cleanup decision.
- [x] Run the read-only Capacities migration preflight and record candidate data
      locations, sizes, file counts, and extensions without reading document
      contents.
- [x] Implement a read-only `scripts/macos_permissions.py` inventory that
      records direct capability checks and writes only a dated
      `state/permissions-*.json`; TCC categories still require visible review.
- [x] Implement the read-only allowlisted export half of
      `scripts/macos_preferences.py`; applying and verifying each desired
      policy remains a separate follow-up task.
- [x] Add reviewed apply/verify handlers for `settings/system-preferences.yaml`;
      begin with Dock/Finder/appearance; keyboard and input sources remain
      device-specific and require their existing listener workflow.
- [x] Review the generated permission and preference baselines on this Mac,
      then promote only confirmed reusable policy—not raw machine state—into
      tracked settings. Confirmed policy remains limited to the existing
      `settings/system-preferences-values.json` allowlist and Dock/keyboard
      policy; no TCC grant is portable, so `settings/privacy.yaml` remains a
      requirements-and-manual-authorization policy only.
- [x] Grant Apple Events access to the terminal/skill host if a complete GUI
      Login Items inventory is required; then rerun the preference baseline.
      Resolved: the current skill execution host successfully queried System
      Events and read `Google Drive` and `GeminiAppLauncher`; the refreshed
      baseline now distinguishes GUI Login Items from LaunchAgents.
- [x] Review malformed `~/Library/LaunchAgents/com.local.keyremap.plist`; it
      appears to be an older keyboard mapping and may overlap with the K240
      listener. Preserve a backup before any user-approved cleanup.
      Resolved: the malformed XML was a stray backslash before `>` in the
      DOCTYPE line. Content was an unrelated JIS-keyboard `hidutil`
      UserKeyMapping (not the K240 receiver), already `not running`. User
      confirmed it is no longer needed; backed up to
      `~/Library/LaunchAgents/backups/` and disabled via the existing
      `.plist.disabled` rename convention.

## Full application permission and authorization inventory

- [x] Expand `scripts/macos_permissions.py` to inventory every detected app
      bundle from `/Applications`, `~/Applications`, system applications,
      WebCatalog apps, and PlayCover apps. CLI/helper applications, login
      items, background tasks, system extensions, VPN/network extensions, and
      privileged helper tools remain follow-up sources.
- [x] Add read-only discovery for Homebrew formulae/casks, LaunchAgents,
      LaunchDaemons, privileged helper tools, system extensions, network
      services, VPN connections, and background-task output. CLI identity
      mapping and per-component ownership review remain follow-up work.
- [x] Re-run System Extension discovery in an approved administrator context
      if the complete extension inventory is required; preserve the current
      OSSystemExtensionError instead of treating it as an empty result.
      Resolved: macOS administrator authorization returned `0 extension(s)`;
      the raw observation is in ignored `state/`.
- [x] Re-run Background Task Management discovery with visible administrator
      authorization if those records are required; do not automate elevation.
      Resolved: macOS administrator authorization returned real records for
      ZeroTier, SmartDNS, AdGuard VPN, Docker, Logi Options+, OrbStack,
      Google, Claude, Slack, TRAE, Tailscale, and other current/system items;
      the raw observation is in ignored `state/`.
- [x] Classify the current unmatched TCC clients into current helpers, system
      components, current identity variants, and legacy/unlisted items; keep
      genuinely unknown clients in `manual_review`.
- [x] For each application, record reusable identification and current
      evidence: name, bundle identifier, version, path, code-signing
      identifier/team, source, detected entitlement keys, requested permission
      category hints, observed authorization status, evidence method, and
      checked timestamp. Entitlement values are not persisted.
- [x] Cover the complete permission category matrix: Full Disk Access;
      Accessibility; Input Monitoring; Screen Recording; Automation/Apple
      Events; Files and Folders; Removable Volumes; Desktop/Documents;
      Downloads; Network Volumes; Camera; Microphone; Speech Recognition;
      Contacts; Calendars; Reminders; Photos; Bluetooth; Location Services;
      Motion & Fitness; and any additional category exposed by the current
      macOS release. Resolved: added `permission_category_matrix` to
      `settings/privacy.yaml`, including TCC categories, protected-folder
      subcategories, Developer Tools, and capability-only network access;
      added Location and Reminders service-name mappings to the scanner.
- [x] Separate three states instead of guessing: `verified_granted`,
      `verified_denied`, and `manual_verification_required`. macOS may not
      expose a supported read API for every TCC category, so an inaccessible
      TCC database must never become a false denial or grant.
- [x] Read the current system TCC database in read-only mode when macOS allows
      it, attach real per-service records to matching application bundle IDs,
      and preserve `no_record` as distinct from `verified_denied`.
- [x] Generate an App × observed-TCC-service matrix. Missing rows remain
      `no_record`; they are not converted into a false denial.
- [x] Reconcile entitlement permission hints with actual TCC records, keeping
      “requested without record” separate from “requested and denied”.
- [x] Add a machine-initialization permission summary grouped by service,
      denied/granted application, unmatched client count, and cleanup candidate.
- [x] Use `not_scanned` while a permission service has not yet been checked;
      never use `manual_verification_required` as a placeholder for missing
      implementation.
- [x] Add entitlement/code-signature inspection as capability evidence, but
      never treat a declared entitlement as proof that the user authorized it.
- [x] Record protected application access requirements for known workflows:
      Chrome profile audit, ChatGPT/Computer Use, K240 listener, Solaar,
      PlayCover, VPN clients, browser extensions, and developer tools in
      `settings/privacy.yaml`.
- [x] Add a report that groups missing or manually unverified permissions by
      application and by bootstrap phase, with a System Settings path and a
      concrete verification action for each item.
- [x] Keep all current application permission observations in ignored
      `state/permissions-*.json`; keep only reusable requirements and policy
      in tracked `settings/privacy.yaml`. Never copy the TCC database,
      credentials, tokens, MDM secrets, or private document contents.
- [x] Test the inventory on this M4B, review false positives, and define the
      new-Mac authorization checklist before adding any apply automation. The
      current host cannot read TCC, so all five sensitive categories remain
      `manual_verification_required` until a visible authorization and workflow
      test is completed.

## Complete system-preference and user-workstyle baseline

- [x] Capture the first preference slice with explicit allowlists for
      language/region, calendar, measurement units, 24-hour setting, input
      sources, architecture, memory, and storage capacity/free space. These
      are observed baseline values; applying locale/input changes remains
      separate.
- [x] Extend the preference allowlist to modifier keys, function-key behavior,
      text-input automation, dictation, and keyboard shortcuts. Text
      substitution contents are redacted; only counts and safe metadata are
      captured.
- [x] Capture Dock, Finder, desktop/window management, Mission Control/Spaces,
      Stage Manager, and screenshot preferences. Private screenshot paths are
      redacted.
- [x] Capture notification authorization summaries and Control Center/menu
      bar visibility/position settings without notification contents or Focus
      rule details.
- [x] Capture Focus/DND database presence and screen-lock/screensaver policy
      fields while keeping Focus rules and private schedules redacted.
- Deferred beyond 0.1.0 (`interface_limited`): capture sound input/output,
      display scaling, refresh rate, Night Shift, True Tone, sleep, battery,
      and remaining power policies.
      Partial observation: sleep/power policy, battery power source, audio
      device metadata, and interface-limited Night Shift/display effects are
      captured; current macOS execution context still does not expose actual
      volume, physical display resolution, refresh rate, or True Tone state.
- [x] Record display controller identity and explicitly preserve unavailable
      Night Shift/windowserver interfaces as interface-limited observations.
- [x] Capture audio input/output device metadata without recording content or
      storing device serial numbers.
- [x] Parse battery/AC sleep, display-off, hibernate, wake, and power
      management parameters into structured machine-local profiles.
- Deferred beyond 0.1.0 (`interface_limited`): capture current display
      identity/resolution and sound volume/mute state as machine-local
      observations without storing serial numbers. Power-management output is
      already captured.
- [x] Capture default applications and file/URL associations for browser,
      mail, terminal, editor, images, video, PDF, archives, SSH, Git, and
      common development file types. Store bundle identifiers, not volatile
      application paths.
      Resolved: expanded `launchservices_profile()` in
      `scripts/macos_preferences.py` into named categories (browser, mail,
      images, video, pdf, archives, ssh, editor_text) with explicit
      `system_default_no_override` status when macOS has no LSHandler
      override, plus a separate `custom_url_scheme_handlers` list (60 on this
      Mac) capturing every vendor-registered URL scheme and its bundle
      identifier. `terminal` and `git` have no LaunchServices content-type or
      URL-scheme surface and are recorded as intentionally excluded rather
      than missing.
- [x] Add a read-only LaunchServices association slice for common file types
      and URL schemes; broader associations remain to be reviewed because
      this Mac currently exposes only a partial handler set.
- [x] Capture login items, user LaunchAgents, system/background tasks,
      shell startup files, PATH/toolchain initialization, Homebrew taps,
      formulae/casks, Git identity/config policy, SSH config shape, and
      developer runtimes. Exclude private keys, tokens, host secrets, and
      machine-specific paths.
      Resolved: `scripts/macos_startup_items.py scan` covers login items (2),
      user LaunchAgents (4), and background tasks (76) in one dated
      `state/startup-items-*.json` record; `developer_environment_profile` in
      `scripts/macos_preferences.py` already covers shell/PATH/SSH-config
      shape/Git config keys/CLI runtime versions. Added `taps` (via
      `brew tap`) alongside existing `formulae`/`casks` in
      `non_app_components.homebrew` (`scripts/macos_permissions.py`) to close
      the one remaining gap. No private keys, tokens, or secrets are read.
- [x] Capture Shell/startup-file shape, PATH size, Git config key names,
      SSH config metadata, and available CLI versions without collecting
      identities, file contents, private keys, or tokens.
- [x] Capture network behavior needed for bootstrap: active interfaces,
      preferred DNS split policy, proxies, VPN/Tailscale/ZeroTier intent,
      firewall/Gatekeeper/FileVault posture, and SmartDNS configuration. Keep
      Wi-Fi passwords, VPN credentials, certificates, and private keys out of
      the repository. Resolved: administrator-authorized read-only baseline
      captured Ethernet/Thunderbolt Bridge/Wi-Fi/Tailscale services, local
      SmartDNS `127.0.0.1`, no HTTP/HTTPS/SOCKS proxy, disconnected Tailscale,
      VPN-client presence, SmartDNS running, Gatekeeper enabled, Firewall
      disabled, SIP enabled, FileVault Off, and no MDM enrollment.
- [x] Capture network service names, per-service DNS observations, proxy/VPN
      summaries, and presence of the tracked SmartDNS policy without storing
      credentials, certificates, private keys, or live address data.
- [x] Capture read-only Gatekeeper, Firewall, FileVault, SIP, MDM enrollment,
      and VPN-client presence status without changing security posture or
      collecting keys/certificates.
- [x] Capture Chrome profile names and email matching for continuity. Email
      is the identity key; profile directory numbers are machine-local.
- [x] Capture Chrome extension IDs/names/versions, Safari Web Clipper presence,
      and WebCatalog/PlayCover directory presence. Never export cookies,
      passwords, tokens, or browsing history.
- Deferred beyond 0.1.0 (`interface_limited`): capture reliable Chrome
      extension enabled state; the current Secure Preferences source exposes
      `null` for this field.
- [x] Capture default-browser routing and safe app-specific WebCatalog/PlayCover
      settings through read-only checks. Current state includes WebCatalog
      wrappers Notion/X and PlayCover settings for YouTube; browser sessions,
      Keychain data, app containers, and account state remain excluded.
- [x] Capture selected app-specific workstyle policies already documented by
      this skill: K240 mappings, Solaar usage, Claude Developer Mode, PlayCover
      YouTube settings, SmartDNS routing, Dock order, and startup listeners.
      Resolved: added `settings/app-workstyle.yaml` with safe portable fields,
      read/apply/verify contracts, and explicit exclusions for accounts,
      sessions, Keychain, app containers, IPA files, and device telemetry.
- [x] Define a portable-vs-machine-local classification for every preference:
      tracked desired policy, ignored current observation, interactive manual
      step, or deliberately excluded secret/private data.
- [x] Add `--check` drift reporting before adding more apply handlers. Each
      preference must have read, apply, verify, and rollback behavior; do not
      implement a blanket `defaults import`.
- [x] Run the expanded baseline on this M4B, review it manually, and promote
      only confirmed user preferences into tracked `settings/`. Keep raw
      snapshots in ignored `state/preferences-*.json`. Remaining unchecked
      preference items are intentionally unresolved or machine-specific.

## System-app preference persistence audit

These are candidate settings for the built-in macOS apps. Each item must first
be read-only inventoried on this Mac, then classified as portable policy,
machine-local observation, manual setup, or deliberately excluded. Do not
export account credentials, message/note/event contents, cookies, private
paths, or library databases.

- [x] Contacts: persist global person-name presentation preferences
      (`NSPersonNameDefaultDisplayNameOrder` and
      `NSPersonNameDefaultShortNameFormat`) separately from Person's
      `givenName`/`familyName` fields. Added to the preference allowlist and
      tracked desired values; iPhone display-order settings remain separate.
- [x] Calendar: inventory safe default-calendar policy, time-zone/display
      preferences, calendar visibility, declined-event display, travel
      advisories, and view range. The current profile uses the last selected
      calendar as default and shows the Monthly view in Asia/Tokyo. Account or
      calendar identifiers, event data, and alert database contents remain
      excluded; week-start/work-week and alert defaults need a separate
      documented read method.
- [x] Reminders: inventory the available preference domains for default
      list/account policy, list sort/group, and completed-item display. The
      current domains expose no safe portable scalar policy beyond
      machine-local window state; do not copy Reminders databases or account
      data. Revisit only if Apple exposes a documented preference API.
- [x] Mail: inventory safe composer/viewer/thread/sort policy and favorite
      mailbox behavior without exporting accounts, mailbox identifiers,
      messages, search terms, signatures, tokens, or private paths. Current
      account selection and signature content remain manual setup; alert
      defaults need a separate documented read method.
- [x] Safari: inventory safe startup/search/reader/sidebar/developer and
      extension policy without reading history, cookies, passwords, bookmarks
      contents, tab groups, website permissions, extension storage, or private
      download paths. Current Safari uses Apple's start page and Google search;
      extension enabled-state and download policy remain separate follow-ups.
- [x] Finder: extend the baseline for sidebar visibility, desktop disk icons,
      iCloud Desktop/Documents visibility, extension visibility, spring-loaded
      folders, and Trash policy. Recent items, search scopes, mounted-volume
      positions, tag contents, private paths, and window coordinates remain
      excluded; default folder view details remain a separate follow-up.
- [x] Notes: inventory safe account/folder/sort/display candidates and locked
      note behavior without reading note content, titles, attachments,
      account identifiers, or sharing metadata. The only portable scalar found
      is checklist auto-sort (currently disabled); account/folder policy is
      manual and Notes database data remains excluded.
- [x] Messages: inventory safe junk/request filtering, retention, attachment
      retention, and conversation-list Focus policy without reading message
      content, participants, attachments, transcript databases, or account
      identifiers. Notification/read-preview defaults need a separate
      documented read method.
- [x] Photos: inventory safe library/display policy, grid columns, zoom,
      launch-library chooser, and shared-library presence without exporting
      library paths, iCloud accounts, photo content, thumbnails, albums, faces,
      locations, or shared-library content. Library selection and iCloud sync
      remain manual setup on a new Mac.
- [x] Music/TV/Podcasts: inventory safe playback/download policy. Current
      domains expose only limited playback/download fields; library paths,
      purchase/account state, and media metadata remain excluded.
- [x] Preview/Quick Look/TextEdit: inventory high-value document-view fields.
      Preview exposes safe sidebar/alignment fields; TextEdit and Quick Look
      expose no safe scalar policy in the current allowlist. Recent files,
      document contents, paths, and window geometry remain excluded.
- [x] Shortcuts and Automator: inventory layout/automation presence only.
      Shortcut actions, names, counts, and private automation data are not
      exported; no safe Automator scalar policy was found.
- [x] App Store and Software Update: inventory safe UI/update-policy fields.
      The current domains expose no portable automatic-update policy; Apple ID,
      purchases, receipts, update identifiers, and account state remain excluded.
- [x] Add a generic, reviewed system-app preference inventory report that
      compares the allowlisted domains against tracked policy and keeps raw
      observations in ignored `state/`.
      See `references/system-app-preferences-audit.md`.

## Cross-machine bootstrap readiness

- [x] Add one documented read-only bootstrap entry point that runs baseline scan,
      Homebrew/app installation, permission checklist, preference apply, and
      final verification in dependency order. The current first phase runs
      scan/plan/inventory/check only; mutating phases remain gated separately.
- [x] Add a tracked-definition validation that proves tracked `settings/`
      and `references/` are sufficient without depending on this Mac's
      ignored `state/`; full install simulation remains environment-dependent.
- [x] Add account/license/manual-action checkpoints for App Store, browser
      profiles, VPNs, developer tools, and protected permissions without
      storing credentials or tokens in `settings/manual-actions.yaml`.
- [x] Add final drift and recovery reporting so a second Mac can be compared
      with the baseline and failed steps can be rerun safely through
      `scripts/bootstrap_verify.py`.

## CTO gap-audit backlog (2026-07-19)

A read-only audit of `settings/`, `references/`, `scripts/`, and
`components/README.md` against the "one-sync, ready-to-use Mac" mission
found domains with no file or script touching them at all. Logged here for
review before promoting any item into an implementation task.

### Must-do (real gaps against the existing mission, low risk, high value)

- [x] Write one end-to-end disaster-recovery runbook that chains scan →
      install → TCC/preference restore → verify into a single "Mac lost or
      wiped" sequence. Today only separate script entry points exist; no
      single document walks the full recovery path.
      Resolved: added [`references/disaster-recovery-runbook.md`](references/disaster-recovery-runbook.md),
      an 8-step sequence (pre-loss snapshot → repo retrieval → network →
      read-only scan → account/secrets-manager setup → app install → TCC/
      preference restore → device-specific config → final verify) that
      references existing scripts/docs by path rather than duplicating
      their content, plus a short "recovery incomplete" troubleshooting note.
- [x] Add a read-only Time Machine / backup precondition check before any
      destructive-adjacent script (Docker Desktop retirement, Capacities
      cleanup, TCC reset) runs. Warn if no valid backup is detected instead
      of silently proceeding. No script or settings file currently touches
      backups at all.
      Resolved: added `scripts/backup_precondition_check.py` (read-only;
      checks `tmutil destinationinfo`/`latestbackup`, warns if no
      destination, no completed backup, or the latest backup is older than
      35 days — matched to the user's ~monthly cadence). It explicitly notes
      iCloud file sync is not a full-system backup substitute. Wired as an
      advisory-only warning (never a hard block) into `docker_desktop_cleanup.py
      remove`, `capacities_cleanup.py --apply`, and
      `macos_permissions_cleanup.py --apply`; each script's own existing
      confirmation token/prompt remains the sole gate.
- [x] Define a dotfiles reproduction mechanism. `developer_environment_profile`
      only records shell startup file shape (byte counts/hashes), not how to
      actually restore those configs on a new Mac. Needs a reusable dotfiles
      repo + symlink strategy as the closing step of dev-environment bootstrap.
      Resolved: added `dotfiles/` (tracked source of truth, mirroring `$HOME`
      under `dotfiles/home/<relative-path>`, see `dotfiles/README.md` for the
      manual-review-before-tracking convention) and
      `scripts/dotfiles_sync.py` (`status` read-only preview, `link --apply`
      symlinks tracked files into `$HOME`, backing up any pre-existing
      non-symlink destination first). No user dotfiles are seeded yet — the
      user confirmed no existing dotfiles repo and no current tracked
      content, by design, to avoid committing unreviewed secrets from the
      live `~/.zshrc`/`~/.ssh/config`; population is a separate, deliberate
      per-file step.
- [x] Define an SSH/GPG key provisioning strategy. SSH config shape is
      captured (never key contents); GPG is not mentioned anywhere. Needs a
      documented "generate new key vs. import from key manager" procedure and
      verification step, never storing key material in the repo.
      Resolved: added [`references/ssh-gpg-provisioning.md`](references/ssh-gpg-provisioning.md),
      documentation-only (no script, no key material). Records that this Mac
      uses per-project `.pem` files outside `~/.ssh/` rather than a default
      identity, and has no GPG installed/used. Defines: retrieval procedure
      for project `.pem` keys on a new Mac, a `ssh-keygen` + `ssh-add
      --apple-use-keychain` procedure if a default identity is ever needed
      (matched to the user's declared system/iCloud Keychain secrets
      manager), an opt-in-only GPG commit-signing procedure, and a
      verification checklist.
- [x] Declare the authoritative password/secrets manager. `manual-actions.yaml`
      already implies manual sign-in flows everywhere but never states which
      manager (1Password/Keychain/etc.) is the source of truth, nor how
      access is restored on a new Mac.
      Resolved: added a `secrets_manager` block to
      `settings/manual-actions.yaml` declaring the macOS system/iCloud
      Keychain as the authoritative source (user confirmed no third-party
      manager is in use), with a `new_mac_recovery_steps` list, plus a new
      `secrets-manager-availability` checkpoint (phase: bootstrap) that
      every other sign-in checkpoint in the file now implicitly depends on.
      `scripts/bootstrap_validate.py` still passes (128 catalog apps, no
      missing required files).
- [x] Schedule the existing `--check` drift detection. `macos_preferences.py
      --check` and `bootstrap_verify.py` are both manually triggered today.
      Add an optional user-level LaunchAgent that runs a read-only drift
      check periodically (e.g. weekly) and writes to `state/`.
      Resolved: added `templates/drift-check.launchagent.plist` (weekly,
      Monday 09:00, `RunAtLoad: false`) and `scripts/drift_check_schedule.py`
      (`status` read-only, `install --apply`/`uninstall --apply`, both
      dry-run by default) following the same never-implicit-install
      convention as the existing K240 LaunchAgent. The agent only re-runs
      the skill's own existing read-only `--check`/`bootstrap_verify.py`
      commands and logs output; it changes nothing itself. Rendered plist
      validated with `plutil -lint` (a `&&` in the shell command needed
      XML-escaping — caught before install, not after).
- [x] Add a sandboxed dry-run mechanism for the full bootstrap.
      `bootstrap_validate.py` only checks internal consistency of tracked
      definitions; there is no way to actually exercise the full bootstrap
      against a fresh local admin account or VM without touching the
      production account.
      Resolved: added
      [`references/bootstrap-sandbox-dry-run.md`](references/bootstrap-sandbox-dry-run.md),
      documentation-only (user has no existing sandbox environment; no
      script/VM was set up). Documents three levels: (1) every mutating
      script's own default dry-run mode, already usable with zero setup;
      (2) a throwaway local admin account, with an explicit note on what it
      does and doesn't isolate (per-account state yes, `/Applications` and
      Homebrew no); (3) a full macOS VM via UTM/Tart for genuinely testing
      `--apply` code paths end to end. Includes a "dry run passed" checklist.
- [x] Define an uninstall/rollback plan for the skill's own footprint.
      Docker, Capacities, and TCC entries each have retirement workflows, but
      nothing enumerates what this skill itself has installed (K240
      LaunchAgent, binaries, backup files) if the user wants to abandon the
      whole bootstrap approach.
      Resolved: added `scripts/skill_footprint_inventory.py` (read-only;
      lists both known LaunchAgents, the Application Support/bin directory,
      the Logs directory, and any deployed dotfiles symlinks, with
      existence/size/loaded checks) and `scripts/skill_uninstall.py`
      (dry-run by default; `--apply` unloads LaunchAgents and moves them
      plus the support directory to timestamped `.removed-*` backups rather
      than deleting outright; logs are kept unless `--remove-logs` is
      passed; the repository itself is explicitly never deleted). Verified
      read-only against this Mac's real state: found the K240 LaunchAgent
      genuinely `loaded`, confirmed dry-run left it untouched.
- [x] Record this session's FDA host-process finding in
      `settings/privacy.yaml` as a named requirement: when this skill runs
      inside a Claude desktop local-agent/Cowork session, the process tree's
      host app is `Claude.app`, not Terminal.app or iTerm — granting Full
      Disk Access to a terminal app has no effect for that execution context.
      Resolved: added an `execution_host_note` under `permissions.
      full_disk_access` and a new `claude-desktop-local-agent-execution-host`
      entry under `workflow_requirements`, both documenting the
      `ps -p $$ -o pid,ppid,comm` parent-chain-walking verification method
      used to actually diagnose this during this session.
- [x] Add a Wi-Fi/network-connectivity bootstrap checkpoint as the very first
      manual-action item. `network_profile` only records service names/DNS/
      proxy/VPN presence after the fact; joining Wi-Fi on a genuinely new Mac
      is never recorded as a checkpoint, even though nothing else in the
      bootstrap (App Store, Homebrew, account sign-in) works without it.
      Resolved: added `wifi-network-connectivity` as the first checkpoint in
      `settings/manual-actions.yaml` (phase: bootstrap, ahead of
      `secrets-manager-availability`), and cross-linked it from Step 2 of
      `references/disaster-recovery-runbook.md`. `bootstrap_validate.py`
      still passes.

### Optional (valuable, lower priority than the must-do list)

- [x] Font management: custom font inventory and installation is not covered
      anywhere.
      Resolved: added `settings/fonts.yaml` (tracked desired-font list) and
      `scripts/macos_fonts.py` (read-only scan across `~/Library/Fonts`,
      `/Library/Fonts`, and system font directories). Running it found a
      real gap: JetBrains Mono is referenced by `~/.config/ghostty/config`'s
      `font-family` but is not actually installed on this Mac -- Ghostty has
      been silently falling back to a substitute font. Installing it
      (`brew install --cask font-jetbrains-mono`) is left as a separate,
      explicit step, not automated by this script.
- [x] Printer/scanner setup: not covered.
      Resolved: added `scripts/macos_printers.py` (read-only; `lpstat -p`/
      `lpstat -d`/`system_profiler SPPrintersDataType` scan, writes only a
      dated `state/printers-*.json`). Deliberately no tracked `settings/`
      file: unlike fonts or Dock order, a printer list reflects
      network/USB devices identified by LAN IP, which is a machine-local
      observation, not portable cross-machine policy, per this skill's
      existing tracked-vs-observed classification.
- [x] Write an iCloud-vs-skill boundary document clarifying what's already
      handled by iCloud sync (Photos, Notes, Safari bookmarks, etc.) versus
      what this skill must handle explicitly, to avoid duplicated effort.
      Resolved: added [`references/icloud-vs-skill-boundary.md`](references/icloud-vs-skill-boundary.md),
      documentation-only. Also calls out one real overlap worth flagging:
      this repository's files sync via iCloud Drive while its Git history
      does not, so concurrent editing across two Macs on both channels at
      once can conflict -- something no script here detects or resolves.
- [x] Capture menu bar app inventory and Notification Center widget layout.
      `notification_profile` only records authorization status today, not
      menu bar icon order or Today View widgets.
      Resolved: found `control_center_profile()` in `scripts/macos_preferences.py`
      already captures Control-Center-routed menu bar item visibility/order
      (Wi-Fi, Bluetooth, Focus, Display, Clock, etc.). Extended it with a
      `today_view_widget_count` (count only, since widget instances are
      opaque NSKeyedArchiver blobs not safely decodable) and an explicit
      `scope_note` documenting that third-party apps drawing their own
      NSStatusItem outside Control Center are not enumerable read-only from
      any single `defaults` domain. `--check` still reports 0 mismatches.
- [x] Define a browser bookmark migration strategy. Chrome profile matching
      exists, but bookmarks themselves (excluding passwords/history) have no
      scripted migration path today; manual only.
      Resolved: added [`references/browser-bookmark-migration.md`](references/browser-bookmark-migration.md),
      documentation-only by deliberate choice (Chrome Sync is the default
      path; manual export/import via `chrome://bookmarks` is the fallback
      when Sync is off for a profile). No script reads bookmark
      titles/URLs -- confirmed the per-profile `Bookmarks` JSON file exists
      across all seven tracked profiles on this Mac, but content stays
      untouched, consistent with this skill's existing browser-data policy.
- [x] Define a multi-Mac continuous sync strategy. The current design is
      "bootstrap one new Mac against the baseline," with no handling for
      keeping several Macs converged over time after initial bootstrap.
      Resolved: added [`references/multi-mac-continuous-sync.md`](references/multi-mac-continuous-sync.md),
      documentation-only. Clarifies that iCloud Drive already propagates
      tracked *files* across Macs automatically, but never their *effect*
      -- each Mac must still run its own `--check`/`--apply` (now automatable
      weekly via the item-6 drift-check LaunchAgent). Also lists which
      tracked values are legitimately per-Mac and should not be forced to
      converge (K240 profile, capacity-tier app selection).
- [x] Add a license-key reminder checklist. `manual-actions.yaml` explicitly
      forbids storing license keys, but there is also no checklist of which
      apps require manual activation, making it easy to miss one.
      Resolved: added `settings/license-reminders.yaml`, manually curated
      (confirmed the app catalog's source fields do not reliably indicate
      paid-vs-free status -- e.g. Notion/Zoom are official_url-sourced but
      free, Affinity is brew_cask-sourced but requires a paid license -- so
      no auto-derivation was attempted). Seeded with Affinity. Cross-linked
      from the `developer-licenses` checkpoint in
      `settings/manual-actions.yaml`. `bootstrap_validate.py` still passes.
- [x] Document a FileVault enable + recovery-key escrow procedure. Disk
      encryption is currently only read-only observed, with no "how to
      enable and safely escrow the recovery key" workflow.
      Resolved: added [`references/filevault-enable-and-recovery-key.md`](references/filevault-enable-and-recovery-key.md),
      documentation-only, consistent with the existing Gatekeeper-policy
      pattern in SKILL.md (explicit user action, visible Terminal for sudo,
      never automated). Found FileVault is currently **Off** on this Mac
      (`fdesetup status`, 2026-07-19) -- a real finding, not changed by this
      task. Documents both the Apple-Account-escrow path (recommended) and
      the manual-recovery-key path, and is explicit that no script here
      ever generates, displays, or stores the recovery key.
- [x] Add local lint/smoke checks across the growing script and catalog set (128+
      catalog entries, a dozen-plus Python scripts) to catch malformed
      files before they land — similar in spirit to the stray-backslash
      corruption found and fixed in `com.local.keyremap.plist` this session.
      Resolved by extending `tests/smoke.sh` to `py_compile` every
      `scripts/*.py` file and `plutil -lint` every LaunchAgent plist template,
      including rendered output. The previously added hosted
      `.github/workflows/smoke.yml` was removed after real runs proved that it
      added private macOS-runner billing/availability failure modes without
      validating the target Mac. Local macOS validation is the accepted
      0.1.0 quality gate; a unified local release-check remains part of RC-06.
- [x] Add a JSON Schema validation script for `references/app-catalog.json`
      (required fields, source consistency) as the catalog grows past 128
      entries, to prevent manual-edit data corruption.
      Resolved: added `scripts/validate_app_catalog.py` (hand-rolled, no
      jsonschema dependency; checks required fields, valid `tier` values,
      duplicate names, guide-file existence, at-least-one-source presence,
      and `app_store_url` shape) and wired it into `tests/smoke.sh`. Running
      it immediately found a real bug: 7 entries (LM Studio, Cherry Studio,
      Logi Options+, Solaar, Capacities, Foxglove, PlayCover Learning Apps)
      had `"tier": "option"` instead of `"optional"` -- confirmed via
      `scripts/macos_apps.py`/`audit_core_catalog.py` that only `tier ==
      "core"`/`"heavy"` are ever checked exactly, so this typo caused no
      runtime misbehavior, but was still a genuine schema violation. Fixed
      with a precise 7-line `sed` substitution (not a full JSON re-dump,
      which would have reformatted the entire 1974-line file). Validator now
      reports 0 errors across all 128 entries; `bootstrap_validate.py` still
      passes.
