# Machine-local runtime state

## Boundary

Runtime observations must not live inside the iCloud-synced repository. The
tracked `state/` directory is now only a compatibility locator containing
`README.md` and `locator.json`.

Resolve the active directory with:

```sh
python3 scripts/state_paths.py path
python3 scripts/state_paths.py info
```

Precedence is deterministic:

1. per-command `--state-dir PATH`;
2. `MACOMRADE_STATE_DIR`;
3. `~/Library/Application Support/macomrade/state/<hashed-machine-id>/`.

The machine ID is a short SHA-256-derived scope. The raw platform UUID is not
written to the path, repository, state records, or terminal output.

Browser transaction plans live below `browser/plans/`. They are exact
machine-local evidence, use mode `0600`, and may contain private item IDs,
fingerprints, folder paths, and an export path. Raw exports, URLs, titles,
cookies, sessions, and secrets are never copied into state. Browser plan CLI
summaries expose counts and status only.

Bootstrap commands export the resolved directory to child scripts so one run
cannot split its scans, plans, permission observations, and final report across
different locations. An explicitly supplied historical plan remains readable
from its old path.

## Legacy migration

Inspect without reading `dataless` payloads:

```sh
python3 scripts/migrate_state.py inspect
```

If required, request iCloud downloads in two phases:

```sh
python3 scripts/migrate_state.py materialize
python3 scripts/migrate_state.py materialize --apply
python3 scripts/migrate_state.py materialize --exact
python3 scripts/migrate_state.py materialize --exact --apply
```

Then preview and copy:

```sh
python3 scripts/migrate_state.py migrate
python3 scripts/migrate_state.py migrate --apply
```

The apply path:

- refuses to open a source still marked `dataless`, `offline`, or `archived`;
- hashes every source file with SHA-256 before copying;
- refuses to overwrite a different destination file;
- copies through a temporary sibling and atomically replaces only after hash
  verification;
- re-reads and hashes every destination file;
- writes a verified migration manifest only in the machine-local destination;
- never deletes source files.

## Source cleanup

Cleanup is a separate destructive transaction. Preview the exact confirmation
contract:

```sh
python3 scripts/migrate_state.py cleanup-source
```

Apply only after the verified manifest, file count, byte count, and destination
read-back have been reviewed:

```sh
python3 scripts/migrate_state.py cleanup-source \
  --confirm "REMOVE VERIFIED LEGACY STATE"
```

Immediately before deletion the command re-hashes both source and destination.
It removes only files bound to the reviewed manifest. Files created or changed
after migration are preserved and reported; the tracked compatibility locator
is never removed.

## Documentation notation

When existing documentation says “state record” or uses
`<machine-local-state>/...`, it means the directory returned by
`scripts/state_paths.py path`, not the repository's compatibility `state/`
folder. Passwords, tokens, private keys, raw TCC databases, session material,
and private document contents remain prohibited even in machine-local state.
