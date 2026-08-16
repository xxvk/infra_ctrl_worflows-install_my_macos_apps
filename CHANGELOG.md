# Changelog

All notable project changes will be recorded here. The format follows the
principles of Keep a Changelog, and version numbers follow Semantic Versioning.

## [Unreleased]

### Added

- Safari-only BR-01 source verification with a machine-readable source
  contract, privacy-preserving capability inspector, official export/iCloud
  boundaries, and hermetic tests that prohibit internal bookmark-store reads.
- BR-02 browser-item Schema with opaque identity, browser/profile boundaries,
  lifecycle and conflict fields, and fail-closed Git/privacy combinations.
- Safari-only BR-03 fixture parser for explicit Bookmarks-and-Reading-List-only ZIP exports,
  including Safari 27's separate switches and HTML members, bounded AppleDouble
  metadata, legacy combined-member compatibility, and the verified
  Xcode/runtime beta selector mismatch;
  including Reading List separation, schema-checked private in-memory items,
  redacted count-only CLI output, and bounded hostile-archive rejection.
- BR-04 explainable URL normalization and duplicate review with an
  authority-backed tracking allowlist, signed/token URL blocking,
  structure-preserving proposals, identity-bounded groups, and count-only CLI
  output without merge or deletion authority.
- BR-05 browser taxonomy and Private decision memory with five stable built-in
  classes, user-defined classifications, time-bounded review dates,
  export-stable semantic fingerprints, identity-safe suppression, and redacted
  read-only CLI summaries.
- BR-06 safe transaction foundation with export-bound self-hashed plans,
  exact-confirmed atomic mode-0600 freeze, stale/tampered input rejection, and
  post-export count verification. Safari live apply remains explicitly blocked
  because current supported interfaces cannot transactionally mutate existing
  items and HTML import is additive.
- BR-07 six-stage browser routing through `macomrade`, with fixed redacted JSON
  summaries, private-input rejection, and accessible zh-Hans/ja/en terminal
  and static HTML reports. The apply route remains safely blocked and performs
  no Safari mutation.
- BR-08 Safari-only live-acceptance foundation with ten stable gates,
  repeat-run export/review/decision/plan checks, optional second-export
  verification, a formal redacted Schema, and a read-only macomrade route.
  Chrome and supported Safari mutation remain explicitly incomplete.
- Exact-confirmed Private Safari duplicate-review export with a registered
  Schema, duplicate-only payload, export-hash binding, atomic mode-0600 write,
  conflict refusal, redacted stdout, and no browser-write authority.
- A source-hash-bound Safari two-level organization compiler with a registered
  Private Schema, complete item accounting, reviewed duplicate outcomes,
  conservative non-mutating title suggestions, exact-confirmed mode-0600 sync,
  and organization-derived non-executable bookmark plans.
- An exact-confirmed Safari evidence importer that validates one explicit ZIP,
  derives a Git-ignored Private date/hash destination, preserves exact bytes,
  verifies source stability and destination hash/parser read-back, enforces
  mode `0600`, refuses conflicts, and emits only redacted counts.
- Conservative Safari organization reconciliation across export-hash and
  item-ID drift, with semantic/path/duplicate stability gates, redacted review
  counts, exact-confirmed versioned candidates, and no canonical switch or
  Safari-write authority.
- BR-10 personal knowledge gateway policy with a roughly 100-source capacity
  target, 70 Core and 30 trial slots, two-out/one-in above 100 followed by
  one-in-one-out, current-source evidence rules, and
  a redacted read-only audit of subdomain retirement pressure and new-source
  capacity.
- Exact-confirmed BR-10 Private wave persistence with source/fingerprint and
  evidence-date binding, same-host consolidation, two-out/one-in enforcement,
  mode-0600 atomic write, redacted output, and a non-executable migration-plan
  summary that preserves the Safari interface blocker.
- BR-10 manual Safari pilot contracts that preserve the immutable approved
  wave, freeze ten final exchange groups and an exact 16-item staging manifest
  only after confirmation, and verify Batch A, Batch B, and purge from explicit
  exports with Reading List and non-manifest drift protection. Safari and purge
  remain manual and unauthorized by the ledger.
- BR-10 full-gateway convergence and deterministic import-package contracts:
  bounded 90–110-source and 15-subdomain validation, original item/fingerprint
  binding, Private omitted-item recovery evidence, Reading List/archive
  exclusion, independent exact confirmations, and full HTML parse read-back
  without Safari mutation authority.
- Xcodes.app as a required Core Homebrew component, with guarded prerelease
  Xcode installation, selection, verification, credential, and rollback rules.

### Changed

- Replaced the stale third-party DeepSeek Harness Cask with a pinned community
  Tauri shell and separate-runtime contract. The alternate
  `anywhere-labs/deepseek-harness-desktop` v2.0.0 release is now explicitly
  blocked after migrated-profile plugin compatibility and interactive
  performance acceptance failed; this is a version-specific project policy,
  not a malware finding.
- Made Safari execution CLI-first for live reads through capability-probed
  `macos-data >= 0.8.0`, retained explicit exports for immutable evidence and
  Safari-owned HTML import for synchronized writes, and adopted the installed
  `macos-data 0.8.1` public local-only bookmark/folder CRUD contract as the
  first local-write choice without claiming iCloud convergence.
- Hardened Xcodes recovery for authenticated-download `HTTP 401` responses,
  Privileged Helper handoff, UI-versus-CLI activation ambiguity, and a bounded
  manual fallback for a root-owned obsolete Xcode bundle.
- Required exact-symbol header and compile checks before adopting beta
  SafariServices APIs; Safari's visible export menu remains the fallback when
  online documentation, the selected SDK, and the runtime disagree.
- Recorded the Xcode 27 Beta 5 SafariServices mismatch and Safari 27 MCP
  boundary: neither the AutoFill settings check nor page-debugging MCP is a
  bookmark or Reading List enumeration source.
- Defined the Private Safari source-evidence retention and future organization
  reconciliation boundaries: immutable hash-bound ZIP evidence, no implicit
  canonical overwrite, and re-review of changed or ambiguous items.

## [0.2.0] - 2026-08-14

### Added

- Public-source release-readiness gates and a path/count-only privacy audit.
- Apache License 2.0, security policy, contribution guide, code of conduct, and
  third-party notice policy.
- Fictional public templates for personal configuration.
- Public onboarding with a ten-minute non-mutating quick start, explicit
  public-only catalog mode, platform matrix, privacy boundary, rollback, and
  troubleshooting guidance.
- Structured bug and feature forms, a pull-request safety checklist, and a
  public/private support contract for responsible disclosure and diagnostic
  sharing.
- Deterministic, schema-validated release-manifest preview binding source,
  public policy, validation, benchmark, limitations, and source provenance
  while keeping all publication authority false.
- Credential-free, public-only exact-commit clone rehearsal covering the
  hermetic release gate, documented quick start, Private-overlay absence, and
  clean-clone read-back without authorizing publication.
- Machine-role profiles, localization catalogs, App Adapter contracts,
  performance budgets, audit reports, and a low-noise drift monitor.
- A memory-backed storage decision layer with two-level logical/allocated
  scanning, iCloud Foundation metadata, decision expiry, target-based planning,
  transaction-safe cache/archive/Trash workflows, Mole evidence import,
  weekly read-only review, five JSON Schemas, and three-language messages.
- Bounded read-only APFS, snapshot, VM/swap, Home, exact temporary-directory,
  and optional-App storage evidence; human absolute and relative free-space
  targets; and non-authorizing OS/App handoff candidates.

### Changed

- Advanced the repository source version and cumulative release contract from
  0.1.0 to the shipped 0.2.0 source release.
- Published the reviewed public source under annotated tag `v0.2.0`, resolving
  to commit `97b4118`; anonymous page, HTTPS clone, API metadata, privacy, and
  release-gate read-backs passed.
- Personal `Private/` configuration is synchronized by iCloud Drive and ignored
  by Git; a public-only clone operates without it.
- `MACOMRADE_PUBLIC_ONLY=1` can now suppress an existing local Private
  app-catalog overlay during public evaluation and clone rehearsals.
- Core Node.js and npm-global ownership is pinned to fnm-managed Node 24.
- Reachable Git history was rewritten to remove personal configuration and
  reviewed private identifiers before public release.
- Storage management now treats Mole as optional evidence rather than capacity
  authority and keeps public policy, iCloud Private intent, and exact
  machine-local observations in separate layers.

### Security

- Added a private reporting path and explicit public-issue redaction rules.
- Removed `Private/**`, reviewed account identifiers, profile labels, a personal
  home path, and a private package-source domain from reachable Git history.

Version 0.2.0 is published as source under an annotated tag. No GitHub Release
or packaged distribution was produced; `VERSION` remains the source of truth.
