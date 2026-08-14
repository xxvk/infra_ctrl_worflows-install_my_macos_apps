# Changelog

All notable project changes will be recorded here. The format follows the
principles of Keep a Changelog, and version numbers follow Semantic Versioning.

## [Unreleased]

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
  0.1.0 to the 0.2.0 release candidate without creating a commit, tag, package,
  or GitHub Release.
- The reviewed source repository is now public at candidate commit `f490fe4`;
  anonymous page, HTTPS clone, API metadata, privacy, and release-gate
  read-backs passed. This did not create a tag or GitHub Release.
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

No version has been tagged or packaged yet. `VERSION` is the source of truth
for the cumulative 0.2.0 release-candidate baseline.
