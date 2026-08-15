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
      capability; and keep `VERSION` at `0.1.0` until a later version change is
      separately authorized.
      Resolved: added one canonical 28-row JSON matrix with all four
      classifications, 12 evidence-backed supported capabilities, and explicit
      behavior boundaries. The validator originally bound the matrix to
      `VERSION=0.1.0`; the separately authorized 0.2.0 bump generalized that
      contract to bind the matrix to the current Semantic Version and matching
      roadmap status while retaining
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
- [x] **RC-15 — Generate a Release Manifest automatically.** Bind version,
      commit, schema versions, catalog/config hashes, supported macOS and
      architecture matrix, test/benchmark results, known limitations, and
      artifact provenance into a reproducible manifest; generating it does not
      authorize committing, tagging, pushing, or publishing.
      Completed on 2026-08-14: added a Draft 2020-12 release-manifest schema,
      tracked fixture, deterministic generator, stable diagnostics route, and
      release-gate validation. A real preview bound 14 schemas, 10 public
      inputs, all 22 hermetic checks, and a passing five-operation benchmark.
      Its only blocker was the expected dirty worktree containing this
      uncommitted implementation. Commit, tag, push, release, and visibility
      authority all remained false.

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

- [x] **Runtime cleanup — migrate legacy npm-global ownership.** The Core
      contract uses fnm Node 24. Exact registry-pinned `wp-studio` and
      `wrangler` packages were installed under the active fnm runtime; command
      paths, versions, required local binaries, login-shell resolution, and
      non-mutating account-status paths were read back successfully. The
      superseded fnm runtime was measured and removed only after exact user
      confirmation. Machine-specific versions, sizes, and execution evidence
      remain in machine-local state rather than tracked component guides.
- [x] **Runtime disposition — preserve the current non-Core npm globals.** The
      owner chose to keep both Vercel CLI and `k6-html-reporter` without
      migration or removal. Vercel remains authenticated and usable from the
      normal fnm Node 24 login shell even though its package is stored under
      Homebrew's npm prefix. Homebrew's unversioned Node remains separate for
      formula-owned Gemini CLI, Mermaid CLI, and TypeScript launchers.
- [ ] **Runtime account follow-up — repair only when the related service is
      needed.** Wrangler's prior token is expired; run an interactive
      `wrangler login` only before Cloudflare account work. WordPress Studio
      CLI found legacy configuration while the GUI app is absent; preserve it
      until the owner explicitly chooses reset or reconnection. Neither state
      blocks Core package verification.

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
      unauthorized. Manual path-level classification and the selected history
      rewrite were subsequently completed under PUB-04.
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
- [x] **PUB-04 — Audit the complete Git history.** Scan all reachable commits
      for secrets, account identifiers, private URLs, machine paths, decrypted-
      package provenance, and personal/organization data; manually classify
      findings, rotate exposed credentials where required, and perform a
      reviewed `git filter-repo` rewrite of the current repository. Preserve a
      verified private backup; remote force-push remains separately confirmed.
      Completed locally on 2026-08-14: all 39 reachable commits were rewritten;
      `Private/**`, seven personal account-email values, twelve Chrome profile
      names, the personal home path, and the specific private IPA source domain
      were removed or replaced. The owner explicitly approved retaining the
      Git author/committer emails. `git fsck`, privacy checks, and all 21 release
      checks passed. The verified pre-rewrite Git bundle and Private archive
      remain in machine-local Application Support. On 2026-08-14, `main` and
      `trae-dev` were updated with exact `--force-with-lease` expectations and
      read back successfully; no PR refs were present. Repository visibility
      remained unchanged at this gate and was changed later under PUB-10.
- [x] **PUB-05 — Add open-source governance.** Obtain an explicit license
      decision—Apache-2.0 is the recommended candidate—then add the license,
      required third-party notices, security policy, contribution guide, code
      of conduct, and changelog. Until then, do not call the repository open
      source.
      Completed on 2026-08-14: the owner selected Apache-2.0. `LICENSE`,
      `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `CHANGELOG.md`,
      and `THIRD_PARTY_NOTICES.md` are present and enforced by bootstrap and
      publication-audit tests. Visibility remained unchanged at this gate and
      was changed later under PUB-10.
- [x] **PUB-06 — Build public onboarding.** Add audience and support scope,
      supported macOS/architecture matrix, prerequisites, ten-minute read-only
      quick start, private-overlay setup, permissions, known limitations,
      uninstall/rollback, and troubleshooting without personal assumptions.
      Completed on 2026-08-14: added `references/public-onboarding.md`, a
      README entry point, bootstrap coverage, and three documentation
      contracts. Live rehearsal found that an author checkout could still load
      its local Private app-catalog overlay, so `MACOMRADE_PUBLIC_ONLY=1` and a
      regression test were added. A repeated scan and plan wrote only temporary
      state, produced no private account prompts, and made no system changes.
- [x] **PUB-07 — Lock the public safety and issue contract.** Keep dry-run and
      exact confirmations, prohibit secret/private-state uploads, add issue and
      responsible-disclosure guidance, and define safe redacted diagnostics for
      public support.
      Completed on 2026-08-14: added structured redacted bug and feature forms,
      disabled blank issues, added a pull-request safety checklist, and linked
      README, contribution, and security entry points to one tested public
      support contract. Diagnostic preview, exact local export, archive review,
      and separate sharing approval remain distinct; no repository command
      uploads, emails, or publishes an artifact.
- [x] **PUB-08 — Complete RC-15 Release Manifest.** Bind the candidate version,
      commit, schema/policy hashes, supported platform matrix, local validation,
      benchmark summary, known limitations, and artifact provenance without
      authorizing commit, tag, release, or publication.
      Completed on 2026-08-14 through RC-15. Preview is reproducible for the
      same evidence set, writes no artifact, exposes exact blockers, and cannot
      authorize any Git or GitHub mutation. Regenerate after committing the
      candidate so `dirty_worktree` can clear before PUB-09.
- [x] **PUB-09 — Rehearse an independent anonymous clone.** Clone the exact
      sanitized candidate without private credentials, run all hermetic checks
      and the read-only quick start, and prove that no personal overlay is
      required, fetched, generated, or committed.
      Completed on 2026-08-14 with a repeatable credential-free local clone
      harness. It requires a clean exact commit, forces public-only mode with a
      fresh HOME and external temporary state, runs the full release gate plus
      the documented quick start, and fails on a Private overlay, personal
      output markers, or clone drift. Genuine anonymous GitHub access was
      subsequently verified under PUB-10.
- [x] **PUB-10 — Execute the visibility transaction only after confirmation.**
      Prepare a recoverable private archive and rollback; show the exact remote,
      candidate commit, history strategy, and settings diff; obtain explicit
      authorization; change visibility once; verify anonymous web/Git access,
      repository metadata, and post-publication privacy checks.
      Completed on 2026-08-14 after explicit owner authorization. Commit
      `f490fe4028e04f7513708f029ba57b360c320a80` was pushed and read back from
      `main`, and the existing GitHub repository changed from Private to Public.
      An isolated no-credential environment received HTTP 200, anonymously
      cloned the full repository at the exact commit, found no `Private/`,
      passed `git fsck --full` and all 23 release checks, and read back public
      API metadata. The post-publication audit found zero current/history
      Private files; all five pattern categories were manually classified as
      approved public contact details, fictional fixtures, or safety-policy
      terminology. No tag, GitHub Release, version bump, or package publication
      was performed.

### Post-publication follow-ups

- [x] **PUB-F01 — Review the public repository name before renaming it.**
      Evaluate whether
      `infra_ctrl_worflows-install_my_macos_apps` should be retained or replaced,
      including the apparent `worflows` spelling, public discoverability,
      memorability, scope accuracy, and alignment with the `macomrade` CLI and
      the still-undecided product name. Compare candidate names and check GitHub,
      package-manager, domain, App Store, and trademark collisions where
      relevant. Before any rename, inventory and plan updates for the Git remote,
      parent-repository submodule URL/path, badges, documentation links, clone
      examples, issue/release links, local checkouts, redirects, and automation;
      define rollback and anonymous web/HTTPS Git read-back. A completed review
      does not authorize changing the GitHub repository name.

      Review snapshot on 2026-08-14: recommend `xxvk/macomrade`. The current
      name is long, narrower than the repository's actual lifecycle scope, and
      contains the apparent `worflows` spelling error. `macomrade` already owns
      the stable CLI and public documentation identity; `macomrade-macos` and
      `macomrade-bootstrap` add redundant scope, while the superseded
      `mac-comrade` spelling is less compact. Refreshed exact-name checks found
      no GitHub repository or account, Homebrew formula/cask, npm, PyPI,
      crates.io, RubyGems, or Japan Mac App Store collision; `.com` and `.net`
      RDAP returned not found. These are point-in-time technical checks, not
      trademark or domain-registration clearance. Apple's published trademark
      guidance requires separate caution before treating the name as a product
      or App Store identity.

      The rename surface is bounded: five files in this repository contain the
      current public URL/name, and the parent repository `.gitmodules` contains
      the submodule URL. The local submodule path may remain unchanged. GitHub
      redirects normal web and Git traffic after a rename, but the old name must
      not be reused; GitHub Action references do not redirect. This repository
      currently has no checked-in Actions workflow. If authorized, update the
      child `origin`, parent `.gitmodules`, public clone examples, README and
      issue-form links; run the release gate; push both repositories as separate
      transactions; then verify new and redirected pages plus anonymous HTTPS
      clone/fetch.

      Completed on 2026-08-14 after explicit owner authorization. GitHub renamed
      the existing Public repository to `xxvk/macomrade` while retaining `main`,
      description, topics, and repository settings. Both the new and redirected
      old page returned HTTP 200, and anonymous HTTPS Git returned the same
      `cf19842` commit from both URLs. The child remote, public links, clone
      example, and parent `.gitmodules` working-tree URL were updated; the local
      submodule directory remains unchanged. The documentation commit
      `9afd3ea` was pushed through the new origin, then a no-credential clone
      from the new URL passed all 23 checks with no `Private/` or worktree drift;
      the old Git URL resolved to the same commit. The parent `.gitmodules`
      update remains uncommitted because that file already contains a separate
      staged `agent-recipes` change. No tag, Release, package, product-name, or
      App Store identity was created.

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

## 0.2.0 — Memory-backed storage management

- [x] **ST-01 — Freeze schemas, layered policy, and CLI contracts.** Added five
      registered JSON Schemas, public and fictional Private policies, stable
      scan/review/plan/apply/verify/history routes, non-authorizing inheritance,
      exact action classes, and fixture-first contract tests.
- [x] **ST-02 — Add the Foundation metadata and eviction helper.** The checked-in
      Swift source reads iCloud/volume metadata and exposes bounded inspect,
      local-copy eviction/download, and manifest-returning Trash operations;
      its compiled binary and module cache remain machine-local.
- [x] **ST-03 — Build the two-level storage fact scanner.** Quick scans retain
      root aggregates; deep scans expand only threshold-crossing roots. Logical
      and allocated bytes, sparse files, hard-link deduplication, symlink and
      mount boundaries, cloud placeholders, inaccessible paths, and clone
      uncertainty have explicit contracts.
- [x] **ST-04 — Implement decision memory and cross-Mac intent.** The local
      ledger supports all eight decisions, expiry and rematerialization rules,
      duplicate suppression, and separately confirmed promotion of patterns to
      Git-ignored Private policy without inheriting execution authority.
- [x] **ST-05 — Implement target and benefit-curve planning.** Plans bind scans,
      fingerprints, hashes, volume targets, low-risk/reversible curves, and the
      minimum action set for compact 50 GiB or expanded 100 GiB free space.
- [x] **ST-06 — Implement iCloud and proven-cache transactions.** iCloud
      eviction requires uploaded/no-conflict/not-downloading/current allocation
      evidence; cache purge requires a public rule with regeneration proof.
- [x] **ST-07 — Implement archive, Trash, purge, and restore.** Archive validates
      an explicit Private target, capacity, write/read and content hash before
      Trash staging. Purge and restore are limited to unchanged manifest-bound
      paths; whole-Trash deletion is impossible.
- [x] **ST-08 — Add Mole evidence, weekly scan, history, and three locales.**
      Mole imports are idempotent evidence only. Weekly quick scan is read-only,
      low-battery/cooldown aware, and notifies only below target or for at least
      5 GiB of new high-confidence candidates.
- [x] **ST-09 — Complete performance and live-Mac acceptance.** Ran storage
      cold/warm budgets, compile/inspect the Swift helper from machine-local
      state, and prove the two known iCloud samples remain low-local-allocation
      non-recommendations without materialization. The samples measured
      3,194,806,686/2,496,489,148 logical bytes but only 876,544/970,752
      allocated bytes, with zero estimated reclaim and `eligible: false`.
      Corrected benchmark RSS to use per-sample macOS `time -l`; both storage
      operations then passed time, RSS, output, and state-growth budgets.
- [x] **ST-10 — Complete docs and full release checks.** Registered 19 schema
      formats and 33 mutation contracts; updated skill routing, operator docs,
      Mole boundary, tests, roadmap, localization, bootstrap, and release
      manifest inputs. Hermetic release checks passed 23/23 and current-Mac
      read-only checks passed 24/24. A hanging `sfltool dumpbtm` call gained a
      30-second fail-closed timeout. At that checkpoint `VERSION` remained
      0.1.0; commit, version, tag, push, and release remained separately
      unauthorized.
- [x] **ST-11 — Harden policies from the first live cleanup campaign.** Fixed
      verify records so later unrelated free-space changes cannot inflate an
      earlier transaction. Added the Mole scan cache to the proven public
      allowlist and added dynamically proven Git artifacts with ignored,
      untracked, rebuild-manifest, inactive-cwd, fingerprint, and apply-time
      recheck gates. Documented iCloud, uv, Android AVD, WebCatalog X, and TRAE
      runtime boundaries; registered proprietary App storage as 0.6 Adapter
      work instead of broadening generic deletion.
- [x] **ST-12 — Close the post-campaign storage visibility gap.** Added bounded
      read-only APFS/snapshot/VM, Home, protected-system, exact `/private/tmp`,
      and optional-App facts; keep OS/App opportunities as non-executable
      handoffs; added explicit relative and absolute human-size targets; capped
      terminal summaries; and made incomplete Home traversal fail closed as
      `partial`. Hermetic tests, schemas, bounded benchmarks, live quick/deep
      scans, a live relative-target plan, and the 23-check release gate passed.
      Exact paths and measurements remain only in machine-local state. After
      separate authorization, `VERSION` and the cumulative acceptance matrix
      advanced to 0.2.0; the source release was committed and published under
      annotated tag `v0.2.0` on 2026-08-14. No package or GitHub Release was
      produced, and genuine Clean-Mac acceptance remains externally deferred.

## 0.3.0 — Browser bookmarks and reading lists

These tasks implement the committed 0.3.0 roadmap after the 0.2.0 storage and
decision-memory foundation is available. They do not authorize reading private
browser data or modifying a live profile before the relevant preview and
confirmation contracts exist.

- [x] **BR-01 — Verify supported read-only data sources.** Document current
      Safari bookmark/Reading List and Chrome bookmark interfaces, profile and
      account boundaries, required permissions, native sync behavior, and the
      supported export fallback. Do not rely on cookies, history, passwords,
      session databases, or undocumented cloud credentials.
      Safari slice now prefers `macos-data >= 0.8.0` for bounded live
      bookmark/Reading List list/query/get operations and keeps a user-mediated
      Safari export as the immutable evidence, recovery, and acceptance source.
      Added capability probing, adapter/version priority, official export and
      iCloud/profile boundaries, and explicit rejections for direct skill
      access to the internal plist, Apple Events enumeration, WebDriver,
      `SSReadingList`, and the unverified Web Extension Bookmarks API. Chrome
      verification remains open by user choice, so BR-01 is not complete.
- [x] **BR-02 — Define the browser-item schema and privacy boundary.** Model
      source browser/profile, collection, canonical URL, title, tags, intended
      lifecycle, confidence, decision expiry, and conflict evidence. Keep
      private URLs, account mappings, exports, and observations out of tracked
      public configuration.
      Added the registered `browser-item` v1 Schema, fictional fixture, and
      fail-closed privacy combinations. Identity is opaque rather than a bare
      URL hash; cross-profile merge authority is always false; canonicalization
      remains explicitly unevaluated until BR-04. The layer contract reserves
      tracked source for policy and synthetic fixtures, `Private/browser/` for
      user-approved synchronized content, and machine-local state for paths,
      fingerprints, counts, parse errors, and transaction evidence. Xcode 27
      Beta 5 verification also records that neither its limited
      `SFSafariSettings` API nor Safari MCP can enumerate personal bookmark
      data.
- [x] **BR-03 — Build fixture-first read-only adapters.** Add sanitized Safari
      and Chrome fixtures and tests before implementing live inventory. A scan
      must preserve browser/profile boundaries and make zero browser changes.
      Safari slice completed: the preferred live adapter is the public
      `macos-data` Safari read CLI; the evidence fallback uses a fully fictional Netscape Bookmarks HTML
      fixture and a bounded parser for an explicitly supplied Bookmarks-and-Reading-List-only
      ZIP. It separates the exact `com.apple.ReadingList` folder, validates
      every private in-memory result against `browser-item` v1, leaves URL
      canonicalization unevaluated, emits only redacted counts, performs no
      write, and rejects extra data classes, path traversal, links, encryption,
      compression bombs, size excess, malformed HTML, and content leaks.
      Chrome remains deferred by user choice, so BR-03 is not complete.
- [x] **BR-04 — Implement explainable URL normalization and duplicate review.**
      Remove only proven tracking parameters, retain semantically meaningful
      parameters, avoid cross-identity merges, and show the evidence behind
      every duplicate group.
      Added an authority-backed public allowlist, fail-closed signed/token and
      ambiguous-URL guards, byte/order/repeat-preserving private proposals, and
      exact/canonical/title/collection evidence. Duplicate grouping is bounded
      by browser/profile/account identity; Safari CLI output is count-only and
      all results remain review-only with `execution_authorized: false`.
- [x] **BR-05 — Add taxonomy and decision memory.** Support inbox, project,
      reference, read-later, archive, and user-defined classifications; suppress
      unchanged reviewed items until their next review date.
      Added five stable built-in classifications with public review intervals,
      Private custom definitions and decision history, semantic fingerprints
      that survive export/item-ID churn, and a review queue that suppresses only
      unique unchanged matches inside one identity boundary. Changed, expired,
      ambiguous, and cross-account items re-enter review. The engine and CLI are
      read-only; persistence and presentation are exposed through BR-07 without
      creating implicit write authority.
      The current Safari export also has a reviewed two-level organization
      compiler and formal Private Schema. Its dry-run proves 400 unique items:
      282 active moves, seven archives, 22 bookmark deletions, two Reading List
      duplicate deletions deferred, and 87 Reading List items deferred. Private
      persistence remains an exact-confirmed mode-0600 transaction independent
      from Safari mutation authority.
- [x] **BR-06 — Add export, plan, and transaction-safe apply.** Produce a
      restorable pre-change export, exact move/merge/archive/delete preview,
      item-scoped confirmation, interruption-safe execution, rollback where
      supported, and browser-visible read-back.
      Safe foundation completed: added an export-bound, self-hashed private plan
      Schema; exact item/fingerprint/count operations; additive-recovery warning;
      exact-confirmed atomic mode-0600 machine-local freeze; stale/tampered-plan
      rejection; and count-only verification against a second explicit Safari
      export. `plan browser --organization` now derives exactly the bookmark
      move/archive/delete operations while excluding Reading List and title
      suggestions. Live apply remains incomplete and fail-closed: Apple exposes
      user-mediated export/import and Reading List addition, but no supported
      API to enumerate and transactionally move, merge, archive, or delete
      existing Safari items. The macos-data 0.8.1 local-plist feasibility path
      has local atomic-write/read-back evidence but no public ordinary-bookmark
      mutation command or verified cross-device sync. Importing HTML appends
      bookmarks and is not exact rollback. Accessibility/UI automation is not
      accepted as generic item CRUD; Safari-owned deterministic import remains
      the synchronized full-replacement route.
- [x] **BR-07 — Expose the workflow through macomrade and accessible reports.**
      Add scan, review, plan, apply, verify, and history routes with redacted
      JSON plus localized HTML/TUI presentation.
      Completed with the six lifecycle routes plus a metadata-only
      `scan browser-capabilities` route, stable
      redacted summary kinds, fixed-field zh-Hans/ja/en terminal and semantic
      static HTML rendering, and rejection of raw/private browser documents.
      `apply browser` intentionally reports the BR-06 supported-interface
      blocker and performs no Safari mutation.
- [x] **BR-08 — Complete live multi-profile acceptance.** Verify Safari and
      Chrome behavior on representative profiles, repeat-run idempotency,
      conflict handling, backup restoration, and all 0.3.0 acceptance gates.
      Safari-only acceptance foundation completed: ten stable BA gates,
      repeat-run export/review/decision/plan checks, optional second-export
      verification, Schema-validated redacted output, and a read-only
      `macomrade verify browser-acceptance` route. Safari 27 live UI verification
      also corrected the export policy to select the separate Bookmarks and
      Reading List switches and accept both a combined HTML layout and Safari
      27's observed separate `Bookmarks.html`/`ReadingList.html` layout with
      bounded AppleDouble metadata; on
      build `26A5406e`, the documented `SFSafariSettings` export selector is
      absent from both Xcode 27 Beta 5 SDK and runtime, so the visible Safari UI
      remains the fail-closed fallback. A real explicit Safari export now
      passes BA-01 through BA-05 without persisting private content. Its 400
      items produce five review-only duplicate groups containing ten items.
      A new schema-validated `review browser-duplicates` route can preview and,
      only after exact confirmation, write those candidates to one mode-0600
      Git-ignored `Private/browser/` artifact while keeping stdout redacted.
      BR-08 remains open because Chrome remains deferred by user choice;
      decision/operation/post-export evidence has not been supplied; and the
      supported Safari write/rollback interface remains unavailable.
- [x] **BR-09 — Preserve source evidence and reconcile organization drift.**
      Add an exact-confirmed, atomic, hash-verified importer for original Safari
      export ZIPs under `Private/browser/evidence/`. Then add a fixture-first
      reconciliation command that compares old and new exports, inherits only
      unambiguous path/fingerprint decisions, returns changed membership to
      review, writes a separate versioned candidate, and switches the canonical
      organization only after a fresh exact confirmation. Preserve the prior
      organization and evidence; never inherit execution authority or overwrite
      a different canonical file implicitly.
      Evidence-import foundation completed: `review browser-evidence` validates
      the source ZIP, derives a date/hash Private destination, previews only
      aggregate counts, and exact-confirmed apply atomically preserves bytes
      with mode `0600`, Git-ignore and parser/hash read-back. BR-09 remains open
      after adding read-only organization comparison, conservative fingerprint,
      exact-path and stable-duplicate inheritance, review blocking, and an
      exact-confirmed versioned-candidate write below `Private/browser/versions/`.
      Canonical switching and rollback acceptance remain incomplete and must be
      a separate transaction.
- [x] **BR-10 — Operate Safari as a renewable personal knowledge gateway.**
      Keep Safari as a bounded recurring-source gateway, Reading List as a
      temporary inbox, and Obsidian as durable knowledge. Preserve the reviewed
      five-domain/fifteen-subdomain structure while keeping about 100 active
      bookmarks: a 90–110 operating range, with 70 Core and 30 time-limited
      trial sources at a nominal total of 100. While above 100, require at least
      two reviewed retirements per new source, then use one-in-one-out at 100 or
      below; review new sources
      after 45 days; and require current, attributable evidence before proposing
      a source discovered in the latest 365 days.
      The public `browser-gateway-policy` Schema, 15-domain quota, seven-decision
      vocabulary, selection weights, privacy boundary, and read-only
      `review browser-gateway` aggregate audit are complete. Remaining work:
      Wave 1 now records ten current sources and twenty reviewed retirements in
      a source-bound, mode-0600, Git-ignored Private ledger; its redacted plan
      projects 282 to 272 and remains blocked from Safari execution. At that
      projected state, quota convergence requires 185 further retirement
      reviews and no more than 13 additions, reaching 100; retirement-only
      waves are allowed and expected. The manual Wave 1 pilot contract is now
      implemented: a registered Private Schema, exact-confirmed non-authorizing
      freeze, immutable-wave supersession, two five-group checkpoints, exact
      16-item temporary-removal manifest, aggregate three-export verification,
      Reading List/non-manifest drift rejection, and 45-day review-date output.
      The Redis promotion prerequisite is captured as an unreviewed Inbox note.
      The original source evidence and reviewed pilot are now persisted. A
      full-gateway convergence compiler, registered Private Schema, stable CLI
      routes, bounded 90–110-source quota checks, omitted-item recovery ledger, and
      deterministic Reading-List-free HTML package generator are implemented.
      After the latest user review, the real-data candidate reaches 99 as 73
      retained legacy sources, 10 pilot sources, and 16 evidence-backed trials;
      the internal IP and duplicate Open Robotics community entry are omitted,
      while LINE Developers documentation is added. The convergence ledger is
      now frozen and the deterministic package is generated. A separately
      confirmed supervised live-Mac cutover preserved fresh pre-import evidence,
      cleared only ordinary bookmarks, imported the full package, and preserved
      a post-import export. Parser read-back proved 99 unique ordinary bookmark
      URLs with an exact URL/title/normalized-folder match and an unchanged
      89-item Reading List URL/title multiset. Safari UI counts were not used as
      acceptance evidence because they also include folders and system objects.
      Post-import use identified one projection correction: keep the five
      domains only as governance metadata, emit the 15 active subdomains as one
      physical folder level, and require every imported path to be exactly
      `Favorites -> <subdomain>` so the folders are directly available on
      Safari's blank/start page. The generator and parser contract now enforce
      this layout without encoding a duplicate `Favorites` folder.
      A separate hash-bound display-order contract is now implemented because
      alphabetical title order does not represent personal importance. It
      requires complete 99-item coverage, contiguous per-folder ranks, the
      pinned/core/monitor/trial/low-frequency tier order, no more than three
      pinned sources per folder, mode `0600`, Git ignore, and both authority
      flags false. The import generator now refuses to operate without this
      frozen order and verifies exact item sequence. A first 15-folder proposal
      previews 45 pinned, 17 core, 20 monitor, five trial, and 12 low-frequency
      entries; it remains temporary and unfrozen pending user review.
      Remaining work: run the 45-day trial lifecycle; continue later replacement
      and retirement waves; and connect only a separately authorized, supported
      Safari mutation/rollback path if Apple exposes one. The verified supervised
      cutover does not unblock `apply-live-safari` or grant unattended authority.
      No score or capacity result authorizes deletion.

**0.3.0 scope note (2026-08-16):** All BR-01 through BR-10 are checked as
complete within the approved **Safari-only** scope. Chrome remains
`deferred_by_user`; Safari item write/rollback is `interface_limited` (BA-08,
no supported Apple API); canonical organization switching remains fail-closed
by design pending a separate exact-confirmed transaction; and the 45-day
gateway trial lifecycle plus post-change second-export evidence (BA-09)
remain open. These boundaries are recorded in
`references/release-acceptance-matrix.json` (SUP-23, LIM-07, DEF-04, DEF-05).
`VERSION` is 0.3.0 with roadmap status `release_candidate`; no tag, GitHub
Release, or genuine clean-Mac acceptance run exists.

## 0.6.0 — Application-specific storage adapters

The generic 0.2 storage engine may aggregate these roots but must not mutate
them. Every adapter below must first define ownership, account/cloud effects,
supported vendor cleanup, rollback, sparse/allocated-byte behavior, and live
read-back. Machine paths and sizes remain machine-local.

- [ ] **AD-01 — Productize the WeChat storage adapter.** Preserve message
      databases and unsynchronized media; distinguish attachments, downloads,
      thumbnails, mini-program data, logs, and caches; prefer WeChat's visible
      storage manager and never raw-delete the container tree.
- [ ] **AD-02 — Reconcile the Claude runtime adapter with current layouts.**
      Audit `claude-code-vm`, `claude-code`, `Claude Extensions`, and legacy
      `vm_bundles` without assuming equivalent semantics. Detect sparse images,
      running `vfkit`/agent processes, and feature impact before extending the
      existing exact-confirmation VM transactions.
- [ ] **AD-03 — Define a Kimi runtime adapter.** Classify the `daimon-share`
      and `daimon` runtime separately from logs and proven caches. Do not call
      the embedded runtime disposable merely because it is large; require app
      relaunch, account, and feature read-back for any cleanup proposal.
- [ ] **AD-04 — Define a Mail storage adapter.** Use supported mailbox/account
      operations and distinguish message databases, downloaded attachments,
      search indexes, caches, and server-retained content. Never raw-delete the
      Mail library or infer server recoverability from account type alone.
- [ ] **AD-05 — Define a Photos storage adapter.** Treat the Photos library as
      protected, account for iCloud Photos and Optimize Mac Storage, and keep
      local-copy optimization distinct from deleting assets or Recently
      Deleted. Any photo deletion requires visual item review and belongs to
      the 0.7 workflow.

## 0.8.0 — WeChat group lifecycle

These tasks implement the committed 0.8.0 roadmap independently from the
0.6.0 WeChat storage adapter. Message content, membership graphs, and group
identifiers are private data; no task below authorizes database decryption,
message sending, or silent shared-state changes.

- [ ] **WG-01 — Audit supported WeChat interfaces and constraints.** Determine
      what the current macOS client can expose through visible UI, supported
      exports, accessibility, and user-driven handoff. Record unsupported
      operations instead of patching or decrypting WeChat databases.
- [ ] **WG-02 — Define the privacy and shared-impact threat model.** Classify
      group names, member lists, account identifiers, activity observations,
      annotations, and message-derived data; define what remains Private,
      machine-local, transient, or prohibited.
- [ ] **WG-03 — Define the group-lifecycle schema.** Model purpose, category,
      user role, attention policy, retention intent, confidence, next review,
      proposed action, reversibility, and whether other members can observe the
      action.
- [ ] **WG-04 — Build a fixture-first read-only inventory adapter.** Use
      fictional groups and deterministic tests; prove that scan mode sends no
      messages and changes no membership, name, notification, pin, or history.
- [ ] **WG-05 — Add taxonomy, review queues, and decision memory.** Support
      work, project, customer, family, community, information feed, temporary,
      and archive categories plus user-defined policy and review expiry.
- [ ] **WG-06 — Publish an exact write-capability and risk matrix.** Separate
      local annotations from mute, pin, rename/remark, leave, dissolve,
      invite/remove-member, and history operations; require item-scoped
      confirmation for every supported mutation.
- [ ] **WG-07 — Implement supported GUI actions and manual handoffs.** Use
      visible automation only where reliable, stop at credentials or security
      confirmation, and return a precise manual step for unsupported actions.
- [ ] **WG-08 — Add read-back, audit, and privacy-safe reporting.** Verify live
      WeChat-visible results without retaining message bodies or sensitive
      payloads in tracked files or diagnostic bundles.
- [ ] **WG-09 — Complete live acceptance without social side effects.** Test
      read-only inventory first, then owner-approved low-risk settings on test
      groups; prove repeat-run idempotency and all 0.8.0 acceptance gates before
      enabling consequential membership actions.

## 0.9.0 — iPhone intelligence and Home Screen lifecycle

These tasks implement the committed iPhone Mirroring roadmap. They authorize
neither hidden iPhone data extraction nor app/content deletion. Device pairing,
passcodes, Apple Account prompts, purchases, and security confirmations remain
visible user handoffs.

- [ ] **IM-01 — Audit the current iPhone Mirroring capability surface.** Verify
      supported macOS/iOS versions, hardware, region, same-account continuity,
      proximity, connectivity, selected-device behavior, notification policy,
      supported gestures, and unavailable camera/microphone or app operations.
- [ ] **IM-02 — Define the iPhone privacy and evidence model.** Classify device
      metadata, app names, screenshots, OCR, folders, account mappings, storage
      summaries, notifications, and in-app content as public policy, Private,
      machine-local, transient, or prohibited.
- [ ] **IM-03 — Define schemas for inventory, desired layout, and restore maps.**
      Model device role, App Library/Home Screen presence, pages, folders, Dock,
      widgets, Focus-linked pages, notification intent, proposed action,
      confidence, reversibility, and visual read-back evidence.
- [ ] **IM-04 — Build fixture-first read-only screen inventory.** Use fictional
      screenshots and deterministic accessibility/OCR fixtures before live
      inspection; prove that inventory opens no private app content and makes
      no taps, drags, settings changes, installations, or removals.
- [ ] **IM-05 — Design role-based app grouping and layout planning.** Support
      portable taxonomy plus per-device overrides, explain every grouping,
      preserve accepted decisions, and distinguish moving/hiding an icon from
      offloading or deleting its app.
- [ ] **IM-06 — Add a transaction-safe visible organization workflow.** Create
      a pre-change restore map, preview small exact batches, require explicit
      confirmation, execute supported drags/folder changes through iPhone
      Mirroring, stop on visual drift, and reconcile interrupted batches.
- [ ] **IM-07 — Add operational intelligence and notification review.** Capture
      only allowlisted visible OS/update, storage, app, and notification-policy
      summaries; keep private payloads and raw identifiers out of reports and
      require a separate confirmation for every settings mutation.
- [ ] **IM-08 — Complete live-device acceptance and restore testing.** Validate
      read-only inventory first, then owner-approved low-risk layout changes;
      prove idempotency, before/after read-back, manual handoffs, and practical
      restore of the prior Home Screen organization.
