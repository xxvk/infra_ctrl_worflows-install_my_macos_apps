# Redacted diagnostic bundle

## Contents

- [Purpose and scope](#purpose-and-scope)
- [Collected data](#collected-data)
- [Deterministic exclusions](#deterministic-exclusions)
- [Redaction and bounded logs](#redaction-and-bounded-logs)
- [Preview and export](#preview-and-export)
- [Verification and sharing boundary](#verification-and-sharing-boundary)

## Purpose and scope

Use `scripts/diagnostic_bundle.py` to prepare a small support artifact without
copying broad machine state. The collector is allowlist-based: it runs six
known read-only contract checks and hashes six known public policy files.
It never accepts an arbitrary input path, directory, log, or state record.

The ZIP has exactly three files:

- `diagnostics.json` — versions, checks, failure classes, public policy hashes,
  and the redaction summary;
- `redaction-report.json` — exclusions, counters, and the post-redaction
  verification assertion;
- `manifest.json` — size and SHA-256 for the two payload files plus the
  no-credentials/no-private-content contract.

## Collected data

The diagnostic payload contains:

- repository version, repository-local CLI version, guarded Git revision,
  macOS version, architecture, Python version, and Homebrew version;
- pass/fail/return code for the CLI, JSON Schema, configuration-layer,
  release-contract, mutation-contract, and bootstrap-definition checks;
- bounded stdout/stderr tails for those controlled commands;
- normalized failure classes such as `permission_denied`,
  `dependency_unavailable`, `contract_failure`, `timeout`, or
  `command_failed`;
- SHA-256 and byte size for public source, schema, mutation, release,
  operational-baseline, and privacy policies.

The Git revision is read only after `icloud_git_guard.py inspect` reports
`ready`. The bundle records only clean/dirty status and a change count, never
Git filenames or diff content. Because a dirty worktree may not match `HEAD`,
it also hashes the exact CLI, collector, schema, registry, and documentation
files that produced the bundle.

## Deterministic exclusions

Do not add broad directories or user-selected files to this collector. It
excludes:

- passwords, tokens, API keys, authorization headers, cookies, private keys,
  recovery codes, and other credentials;
- account names, emails, owners, usernames, hostnames, and session data;
- Private configuration values;
- machine-local scan, permission, preference, state, and application records;
- arbitrary filenames, document content, browser data, and user logs;
- the raw TCC database, TCC database path, and raw authorization rows.

Only repository-relative names of the six public allowlisted policy files are
included. Their contents are hashed but not copied.

## Redaction and bounded logs

Each stdout and stderr stream is limited to its last 4096 bytes before
redaction. The payload records original byte counts and whether truncation
occurred.

Structured secret/account/host fields are removed. Text redaction replaces
emails, common credential patterns, credential/account assignments, URL query
strings, home paths, temporary paths, and tracked `Private/` configuration
paths. A final recursive verifier rejects
the payload if any prohibited key, email, credential pattern, `/Users/` path,
URL query, or raw TCC marker remains.

Redaction counters report categories and quantities, never removed values.

## Preview and export

Preview is the default operational step:

```sh
./bin/macomrade diagnostics bundle \
  --output ~/Desktop/macomrade-diagnostics.zip
```

It writes nothing. Review the exact redacted diagnostics and redaction-report
payloads plus the check summary, failure classes, redaction counters, excluded
categories, file manifest, predicted ZIP size, and predicted SHA-256. The
displayed output path is redacted before it reaches preview JSON.

Export is a separate mutation:

```sh
./bin/macomrade apply diagnostic-bundle \
  --output ~/Desktop/macomrade-diagnostics.zip \
  --apply \
  --confirm "EXPORT REDACTED DIAGNOSTICS"
```

The output must be a new `.zip` in an existing directory. Export writes a
complete temporary sibling and creates the destination with an atomic hard
link, so a destination created during the export race is never overwritten.
It then removes the temporary name and never changes a source file.

## Verification and sharing boundary

After writing, the exporter reopens the ZIP, requires the exact three member
names, verifies every manifest byte count and SHA-256, parses
`diagnostics.json`, and repeats the sensitive-pattern scan. The command reports
the final ZIP hash and explicitly sets `publication_authorized` to false.

Successful export authorizes only local creation. Inspect the ZIP before
sharing it. Uploading, emailing, attaching to an issue, or publishing it always
requires a separate explicit user decision.
