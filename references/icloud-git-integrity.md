# iCloud-aware Git integrity and recovery

## Contract

This repository intentionally remains in iCloud Drive. Relocating it is not a
supported remediation. The repository therefore treats File Provider
materialization as part of the Git safety boundary.

An iCloud placeholder is not evidence that a Git object was deleted or
corrupted. Before any Git-dependent workflow, use
[`scripts/icloud_git_guard.py`](../scripts/icloud_git_guard.py). The guard:

- resolves a normal `.git` directory or a submodule/worktree `gitdir:` pointer;
- checks the working tree and the resolved Git object store;
- reads BSD File Provider flags without opening `dataless` payloads;
- blocks Git when a required file is `dataless`, `offline`, or `archived`;
- validates local pack, index, reverse-index, `HEAD`, and config structure;
- never deletes, evicts, repairs, resets, commits, or rewrites Git data.

## Keep the repository downloaded

In Finder, select the top-level `XVK_PM` repository, Control-click, and choose
**Keep Downloaded**. This is a user-visible File Provider preference; the
skill does not emulate Finder's private pinning interfaces.

Verify the current local result:

```sh
cd workflows/infra_ctrl_worflows/install_my_macos_apps
python3 scripts/icloud_git_guard.py inspect --repo .
```

`status: ready` confirms that every currently required path is local and
structurally readable. It does not prove that iCloud will never evict the
folder later, so rerun the preflight before Git-dependent operations. A
persistent Finder **Keep Downloaded** selection remains
`manual_verification_required`; absence of `dataless` is the supported CLI
verification.

## Materialize without relocating

Start with a plan:

```sh
python3 scripts/icloud_git_guard.py materialize --repo .
```

The default plan collapses unavailable loose/packed objects into one request
for the resolved Git `objects/` directory. This avoids issuing hundreds of
individual requests. Review the exact command and then apply:

```sh
python3 scripts/icloud_git_guard.py materialize --repo . --apply
python3 scripts/icloud_git_guard.py inspect --repo .
```

The implementation capability-checks Apple's tools at runtime. Older macOS
releases expose `fileproviderctl materialize`; newer releases may retain a
stale manpage while removing that command, in which case the script uses
`brctl download`. Run as the signed-in user, never with `sudo`.
Materialization downloads a local copy; it never calls `evict`.

If a grouped request completes but the next inspection still reports a small
number of unavailable items, preview and then apply the exact fallback:

```sh
python3 scripts/icloud_git_guard.py materialize --repo . --exact
python3 scripts/icloud_git_guard.py materialize --repo . --exact --apply
python3 scripts/icloud_git_guard.py inspect --repo .
```

Do not start `--exact` for a large result until the grouped retry has had time
to finish and iCloud reports no active download.

## Read-only Git verification

After and only after preflight reaches `ready`:

```sh
python3 scripts/icloud_git_guard.py verify --repo . --timeout 300
```

The command sets `GIT_OPTIONAL_LOCKS=0` and runs:

1. `git status --short`
2. `git diff --check`
3. `git fsck --full`

A dirty working tree is allowed by `git status`; malformed whitespace reported
by `git diff --check`, unreadable objects, command timeout, or non-zero
`git fsck` blocks verification. Dangling-object notices can be informational
when `git fsck` still exits successfully.

Exit codes:

- `0` — inspection/verification passed, or a materialization plan/request was
  produced successfully;
- `2` — Git remains blocked by unavailable or unverified data;
- `3` — materialization/recovery input is invalid or the Apple tool failed.

## Recovery when materialization cannot restore Git

Do not delete, reset, repack, or run Git repair commands against the canonical
iCloud copy. Use a copy-first recovery:

1. Stop repository writes on every Mac and allow iCloud synchronization to
   settle.
2. Preserve the current repository as a dated recovery copy. Renaming or
   replacing the canonical folder requires explicit user confirmation.
3. Clone the known remote with `--recurse-submodules` into the same intended
   iCloud parent, using a temporary sibling name.
4. Run `inspect`, apply materialization if needed, and run `verify` against the
   fresh clone.
5. Compare and copy only reviewed uncommitted working files from the preserved
   copy. Never copy its damaged `.git` directory.
6. Switch the verified clone into the canonical path only after explicit
   confirmation and read-back. Keep the recovery copy until the user confirms
   the working tree and remote history are complete.

If no trusted remote exists, stop. iCloud sync is not a substitute for a valid
Git remote or backup, and the guard must not invent missing history.
