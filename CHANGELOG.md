# Changelog

All notable project changes will be recorded here. The format follows the
principles of Keep a Changelog, and version numbers follow Semantic Versioning.

## [Unreleased]

### Added

- Public-source release-readiness gates and a path/count-only privacy audit.
- Apache License 2.0, security policy, contribution guide, code of conduct, and
  third-party notice policy.
- Fictional public templates for personal configuration.
- Machine-role profiles, localization catalogs, App Adapter contracts,
  performance budgets, audit reports, and a low-noise drift monitor.

### Changed

- Personal `Private/` configuration is synchronized by iCloud Drive and ignored
  by Git; a public-only clone operates without it.
- Core Node.js and npm-global ownership is pinned to fnm-managed Node 24.
- Reachable Git history was rewritten to remove personal configuration and
  reviewed private identifiers before public release.

### Security

- Added a private reporting path and explicit public-issue redaction rules.
- Removed `Private/**`, reviewed account identifiers, profile labels, a personal
  home path, and a private package-source domain from reachable Git history.

No version has been tagged or published yet. `VERSION` remains the source of
truth for the 0.1.0 release-candidate baseline.
