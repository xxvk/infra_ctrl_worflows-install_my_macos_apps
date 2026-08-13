# Release manifest

## Purpose

`scripts/release_manifest.py` creates a deterministic JSON description of one
release-candidate input set. It binds the repository version and roadmap
status, exact source commit and worktree status, registered schema versions and
hashes, public catalog/configuration hashes, platform support matrix, hermetic
release-check summary, latest available machine-local benchmark summary, known
limitations, and source-only artifact provenance.

The manifest contains no timestamp, machine name, state path, Private value,
credential, or arbitrary log. Given identical repository files, commit,
worktree state, release result, and benchmark input, it produces identical JSON
and `manifest_sha256`.

## Commands

Validate the implementation, schema, and fixture:

```sh
python3 scripts/release_manifest.py validate
```

Generate the current preview through the stable CLI:

```sh
MACOMRADE_PUBLIC_ONLY=1 ./bin/macomrade diagnostics release-manifest
```

Preview prints JSON only. `--output /path/release-manifest.json` records output
intent in the preview but deliberately writes nothing. A future publication
transaction may persist the exact reviewed manifest through a separately
registered and confirmed mutation; PUB-08 does not introduce that authority.

## Candidate status

The generated status is `candidate` only when the worktree is clean, the
hermetic release check passes, and the supplied or latest machine-local
benchmark comparison passes. Otherwise it is `review_required` with explicit
blockers. A missing benchmark is honest evidence absence, not a fabricated
pass.

The authority object always keeps commit, tag, push, GitHub Release, and
visibility change false. A candidate manifest is evidence for a later decision
and never performs or authorizes that decision.

## Artifact provenance

The current repository distributes source only. The preview produces no DMG,
PKG, ZIP, Homebrew formula, App Store build, tag, or GitHub Release. Binary
provenance, signing, notarization, and package hashes must be added only when a
future release actually produces those artifacts.
