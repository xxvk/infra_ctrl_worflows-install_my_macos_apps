# Public repository release readiness

## Contents

- [Purpose](#purpose)
- [Current blockers](#current-blockers)
- [Repeatable publication inventory](#repeatable-publication-inventory)
- [Target repository model](#target-repository-model)
- [Publication gates](#publication-gates)
- [Selected history strategy](#selected-history-strategy)
- [Visibility-change transaction](#visibility-change-transaction)
- [Non-goals](#non-goals)

## Purpose

Version 0.1.1 prepares the source repository for public discovery, cloning,
inspection, contribution, and safe personal reuse. Public source availability
is separate from declaring the product stable, shipping a native app, or
claiming that every Mac can be configured without manual authorization.

Changing GitHub visibility is the final transaction, not the first step. Until
all publication gates pass and the user explicitly authorizes that exact remote
change, the repository remains Private and `VERSION` remains unchanged.

## Current blockers

The `Private/` layer contains personal cross-Mac configuration, including
account identifiers. It now remains beside the engine for iCloud Drive sync and
is ignored by Git. Removing it from the current Git index is insufficient
because prior commits retain its contents. The repository also does not yet
contain a license, security policy, contribution guide, code of conduct, or
changelog.

Before publication, inspect both the current tree and all reachable history for
credentials, identifiers, private URLs, machine paths, decrypted-package
provenance, personal profile names, and organization-specific operational
details. A pattern scan is only one source of evidence; every flagged file and
history result needs classification.

## Repeatable publication inventory

Run the read-only PUB-01 inventory from the skill root:

```bash
./bin/macomrade diagnostics publication
```

The command inventories the tracked tree, reachable Git history, `Private/`
surface, governance files, large and binary files, generated artifacts,
third-party assets, and submodules. Its machine-local record contains only
paths, finding categories, and counts. It never stores matched text or secret
values, and a finding never authorizes publication, history rewriting, or a
visibility change.

Treat the result as an input to human classification rather than proof that a
repository is safe to publish. Run it again after every privacy-boundary,
history, fixture, governance, or artifact change.

## Target repository model

The public repository contains the reusable engine, schemas, scripts,
components, public policy, sanitized fixtures, documentation, and example
configuration. It must work without access to the author's personal overlay.

Personal cross-device configuration remains under `Private/` in the existing
iCloud Drive project directory. The whole directory is Git-ignored and no
second repository, submodule, or remote locator is used. The loader order
remains public base followed by the user's local Private overlay. A public-only
clone must operate without that overlay. Secrets continue to use Keychain or
another secret store and never enter Git or `Private/`.

Do not solve this boundary with Git encryption inside the public repository.
Encrypted blobs still create metadata, key-management, contribution, and
accidental-disclosure risks. Publish sanitized example files instead.

## Publication gates

0.1.1 is ready for a visibility decision only when all ten gates pass:

1. **Inventory and classification** — enumerate all tracked files, generated
   artifacts, submodules, large files, licenses, third-party assets, current
   personal data, and sensitive history findings.
2. **iCloud Private overlay** — ignore the in-place `Private/` directory in
   Git, preserve existing values, and support public-only operation when it is
   absent.
3. **Sanitized examples** — provide complete fictional examples for every
   required personal overlay and prove a clone works without author data.
4. **Tree and history privacy audit** — scan the full reachable history,
   manually classify findings, rotate any exposed credential, and select a
   reviewed history-cleaning or sanitized-new-origin strategy.
5. **Open-source governance** — add the explicitly selected license,
   third-party notices where required, `SECURITY.md`, `CONTRIBUTING.md`,
   `CODE_OF_CONDUCT.md`, and `CHANGELOG.md`.
6. **Public onboarding** — document audience, supported macOS/architecture,
   prerequisites, ten-minute read-only quick start, privacy model, manual
   permission boundaries, uninstall/rollback, and known limitations.
7. **Public safety contract** — make dry-run the default, keep destructive
   confirmations intact, prohibit secret collection, and publish responsible
   disclosure and issue-redaction guidance.
8. **Release artifact and provenance** — complete RC-15 and produce a
   reproducible manifest containing version, source commit, schemas, policy
   hashes, local test results, benchmark summary, known limitations, and
   artifact provenance.
9. **Independent public-clone rehearsal** — clone the exact sanitized candidate
   without private credentials, run all hermetic checks, exercise the read-only
   quick start, and confirm no Private file is required or generated in Git.
10. **Visibility transaction and read-back** — review backup and rollback,
    explicitly authorize the exact GitHub repository, change visibility once,
    verify anonymous web and Git access, inspect repository metadata, and
    immediately re-run public privacy checks.

## Selected history strategy

The owner selected an in-place `git filter-repo` rewrite rather than creating a
new public repository. The working copy remains in iCloud Drive. `Private/`
also remains physically in that directory for iCloud synchronization, but is
removed from the Git index and ignored as a whole.

The rewrite is a dedicated transaction after the current candidate has a clean
working tree:

```text
verify clean candidate and local Private files
→ create and independently verify a private backup bundle
→ clone the candidate into a non-iCloud temporary directory
→ remove Private/** from every reachable commit
→ replace reviewed personal identifiers in historical public-path blobs
→ preserve the owner-approved Git author and committer email metadata
→ expire reflogs and repack only the temporary rehearsal
→ run object, privacy, schema, release, and public-only checks
→ compare refs and commit counts
→ repeat the proven rewrite on the real repository
→ restore the origin remote explicitly
→ stop before any force-push
```

The final rehearsal and local rewrite processed all 39 reachable commits.
`Private/**`, reviewed personal account emails, Chrome profile labels, the
personal absolute home path, and the specific private IPA source domain were
removed or replaced. The owner explicitly approved retaining
`xxvk@outlook.com` and `noreply@github.com` in Git commit metadata. Fictional
test values and generic public safety documentation remain. `git fsck`, the
bounded privacy checks, and all 21 release checks passed after rewriting.

The pre-rewrite Git bundle and a separate Private configuration archive are
stored under machine-local Application Support with owner-only permissions.
The original `origin` URL was restored after `git filter-repo`. On 2026-08-14,
the cleaned `main` and `trae-dev` refs were pushed with exact
`--force-with-lease` expectations and read back from GitHub; no PR refs were
present. No GitHub visibility change, tag, or release has occurred.

History rewriting changed every affected commit ID. The local and remote branch
rewrite is complete. Any future history rewrite remains a separate explicit
authorization point and must use force-with-lease against verified remote refs.

The recommended license candidate is Apache-2.0 because it includes an express
patent grant, but choosing and adding a license remains a separate explicit
owner decision. Do not represent the repository as open source before a license
is actually present.

## Visibility-change transaction

The final external mutation follows:

```text
inspect remote and candidate commit
→ verify privacy and release evidence
→ confirm exact repository and visibility
→ change GitHub visibility
→ anonymous web/Git read-back
→ verify settings, topics, description, default branch, and release links
→ record the public commit and manifest
```

Prepare a recoverable private archive before any history rewrite or remote
replacement. A same-remote history rewrite and a sanitized new public origin
have different URL, stars, issue, redirect, and rollback implications; select
one only after the full-history audit. Never force-push or delete the current
private remote merely to simplify publication.

## Non-goals

- 0.1.1 does not publish the repository automatically.
- It does not make personal configuration public.
- It does not require hosted GitHub Actions; local macOS validation remains the
  release authority unless the user changes that policy separately.
- It does not claim App Store availability, stable 1.0 status, or completion of
  the externally blocked genuine Clean-Mac acceptance run.
- It does not accept secrets, private machine state, or support bundles in
  public issues.
