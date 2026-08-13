# Public repository release readiness

## Contents

- [Purpose](#purpose)
- [Current blockers](#current-blockers)
- [Repeatable publication inventory](#repeatable-publication-inventory)
- [Target repository model](#target-repository-model)
- [Publication gates](#publication-gates)
- [Independent clone rehearsal](#independent-clone-rehearsal)
- [Selected history strategy](#selected-history-strategy)
- [Visibility-change transaction](#visibility-change-transaction)
- [Non-goals](#non-goals)

## Purpose

Version 0.1.1 prepared the source repository for public discovery, cloning,
inspection, contribution, and safe personal reuse. The owner explicitly
authorized the final visibility transaction on 2026-08-14. Public source
availability is separate from declaring the product stable, shipping a native
app, or claiming that every Mac can be configured without manual authorization.

Changing GitHub visibility remains a separately authorized final transaction,
not a side effect of validation. The completed transaction did not change
`VERSION`, create a tag, or create a GitHub Release.

## Current blockers

PUB-01 through PUB-10 are complete. Commit
`f490fe4028e04f7513708f029ba57b360c320a80` is public on `main`; anonymous page,
HTTPS Git, repository API, default-branch, license, object-integrity,
public-only configuration, and 23-stage release-gate read-backs passed on
2026-08-14. No `Private/` file exists in the public tree or reachable history.

There is no remaining blocker to public source access. This does not clear the
separate genuine Clean-Mac acceptance requirement, promote 0.1.0 from
`release_candidate`, or authorize a version bump, tag, GitHub Release, package,
or App Store submission.

Continue to treat the repeatable publication scan as evidence requiring human
classification. A passing pattern scan is necessary but cannot by itself
authorize publication.

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

## Independent clone rehearsal

Run PUB-09 only from a clean candidate commit:

```sh
./bin/macomrade diagnostics public-clone
```

The harness first runs the iCloud Git preflight and refuses a dirty source. It
then creates a non-local temporary clone of the exact commit, assigns a fresh
temporary HOME and state directory, disables Git credential prompts and
inherited global configuration, removes credential-bearing environment
channels, and forces `MACOMRADE_PUBLIC_ONLY=1`. Inside that clone it runs the
complete hermetic release check and every command in the documented read-only
quick start. It fails if a `Private/` directory appears, the clone becomes
dirty, or command output contains an email address or absolute macOS user-home
path.

The summary is written under the machine-local
`public-clone-rehearsals/` state directory and contains no command output,
credentials, personal paths, or publication authority. Temporary clone files
are removed after the run. Before publication, local `file://` transport is an
honest credential-free isolation rehearsal, not anonymous GitHub proof. After
publication, repeat the same boundaries through unauthenticated HTTPS as part
of the visibility-transaction read-back.

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
present. The later PUB-10 transaction made the existing repository public
without another history rewrite. No tag or GitHub Release has been created.

History rewriting changed every affected commit ID. The local and remote branch
rewrite is complete. Any future history rewrite remains a separate explicit
authorization point and must use force-with-lease against verified remote refs.

The owner selected Apache-2.0. `LICENSE`, `SECURITY.md`, `CONTRIBUTING.md`,
`CODE_OF_CONDUCT.md`, `CHANGELOG.md`, and `THIRD_PARTY_NOTICES.md` are present
and checked by the bootstrap and publication-audit contracts. This completed
the governance gate before PUB-10; governance validation did not itself change
repository visibility or authorize a release.

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

The owner explicitly authorized this transaction on 2026-08-14 for
`xxvk/infra_ctrl_worflows-install_my_macos_apps`. The exact candidate
`f490fe4028e04f7513708f029ba57b360c320a80` was pushed and read back from
`refs/heads/main`; GitHub reported `PUBLIC`. An isolated environment with a
fresh HOME, no GitHub token, disabled credential prompts, and no global Git
configuration received HTTP 200 from the repository page and cloned the full
HTTPS repository. Its HEAD matched the candidate, `Private/` was absent, the
worktree remained clean, `git fsck --full` passed, and all 23 hermetic checks
passed.

The anonymous GitHub API read-back reported `private: false`, visibility
`public`, default branch `main`, and Apache-2.0. Issues and Projects were
enabled; Wiki was disabled; homepage was empty. A post-publication optimization
then added the reviewed safety-first macOS lifecycle description and eleven
discoverability topics covering macOS setup/automation, Homebrew,
configuration management, developer tooling, Python, Codex, and bootstrap.
The path/category-only audit found zero current or historical `Private/` files.
Its five pattern categories were manually classified as the approved public
contact email, fictional test/example emails and paths, a synthetic token
fixture, credential-redaction fixtures/documentation, and decrypted-IPA safety
terminology without a tracked private source URL.

On 2026-08-14, after a separate exact-name collision and migration review, the
owner explicitly authorized renaming the public repository from
`xxvk/infra_ctrl_worflows-install_my_macos_apps` to `xxvk/macomrade`. GitHub
preserved visibility, `main`, description, topics, Issues, Projects, and the
Apache-2.0 license result. Anonymous page and HTTPS Git checks passed on the new
URL; the old page redirected to the new repository and the old Git URL returned
the same `main` commit. The old name must not be reused because doing so would
break GitHub's redirect. No product-name, trademark, tag, Release, package, or
local-directory rename was implied.

Prepare a recoverable private archive before any history rewrite or remote
replacement. A same-remote history rewrite and a sanitized new public origin
have different URL, stars, issue, redirect, and rollback implications; select
one only after the full-history audit. Never force-push or delete the current
private remote merely to simplify publication.

## Non-goals

- Repository automation does not publish or change visibility automatically;
  the completed 0.1.1 transaction was explicitly authorized.
- It does not make personal configuration public.
- It does not require hosted GitHub Actions; local macOS validation remains the
  release authority unless the user changes that policy separately.
- It does not claim App Store availability, stable 1.0 status, or completion of
  the externally blocked genuine Clean-Mac acceptance run.
- It does not accept secrets, private machine state, or support bundles in
  public issues.
