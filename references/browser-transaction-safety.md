# Browser transaction safety

## Current support boundary

BR-06 has a transaction-safe planning and verification foundation. Live reads
prefer the public `macos-data >= 0.8.0` Safari adapter, and the installed
`macos-data >= 0.8.1` guarded bookmark/folder CRUD is the **default local-only
write path** for bookmark and folder organization. The planning implementation
can:

- parse one explicitly supplied, verified, unencrypted Bookmarks-and-Reading-List-only Safari
  export;
- bind exact item-scoped `move`, `merge`, `archive`, and `delete` intent to the
  export hash, item fingerprints, identity boundary, and expected counts;
- preview without writing, or freeze one self-hashed plan to mode-`0600`
  machine-local state after exact confirmation;
- reject export drift, changed or missing items, malformed targets,
  cross-identity or self merges, conflicting destinations, and plan tampering;
- compare a second explicit export with the frozen expected fingerprint counts.

`macos-data` 0.8.1 ships guarded atomic mutation of ordinary bookmarks and
folders as a stable public CLI. **That CLI is the default execution route for
live organization** (see the CRUD contract below), not the export-bound
`apply-live-safari` planner bridge, which remains blocked at
`supported_item_write_interface_unavailable` and performs no write.
Accessibility or UI automation is not accepted as a generic transaction-safe
item CRUD substitute.

### Local-only CRUD contract (default live-write path)

With `macos-data >= 0.8.1`, run `bookmarks create|edit|move|delete` and
`folders create|rename|move|delete` directly:

- **Safari must be fully quit** before any write; the CLI fails closed
  otherwise (`local bookmark writes require Safari fully quit`).
- Dry-run is the default and returns `sourceSHA256Before`; `--apply` carries
  that value as `expectedSourceSHA256` and succeeds only when private
  recovery, atomic swap, and read-back all pass.
- Deletes require exact typed confirmation (`DELETE SAFARI BOOKMARK` /
  `DELETE SAFARI FOLDER`); folder deletion accepts an empty folder only.
- Every result reports `syncStatus=local_only`. Local plist edits do not sync
  to iCloud automatically; **the user triggers the final iCloud
  synchronization by reopening Safari**. Never interpret a local read-back as
  iCloud convergence, and never connect the export-bound planner to live CRUD
  automatically.

### Sorting contract (move + index)

Reordering bookmarks inside a folder uses the same guarded `bookmarks move`
operation; there is no separate reorder path. `move` requires
`{"id", "parentID", "index"}` and performs remove-then-insert at the requested
`childIndex` under the same safety gates (cycle detection, writable folder,
untouched-node preservation, dry-run → `expectedSourceSHA256` → apply →
`readback_confirmed`).

Transaction rules for a safe reorder:

- Define the complete desired order for the folder first; a partial list only
  moves those items and leaves unspecified items in the remaining slots.
- Emit one move per item and execute in **descending index order** so earlier
  moves do not invalidate later target positions.
- Each move is an independent guarded transaction with its own dry-run hash;
  never reuse a hash from a previous move.
- Verify by `readback_confirmed` per move; confirm the final full order by a
  fresh `bookmarks list` read-back.
- Ordering is `local_only` until the user reopens Safari; a reordered plist is
  not iCloud convergence.

For a synchronized full-library replacement (whole-library reorganize), the
fallback write path is the deterministic HTML package plus Safari-owned
import. Computer Use may operate that bounded UI after explicit
authorization, but CLI read-back and a fresh export—not UI object counts—must
verify the result.

## Supervised full-replacement cutover

A full replacement has been operationally verified as a supervised recovery
workflow: preserve and parse a fresh pre-change export, obtain a separate exact
confirmation, clear only ordinary bookmarks, import one deterministic package,
then preserve and exactly compare a post-change export. The accepted live-Mac
run produced 99 unique ordinary bookmark URLs and preserved the exact 89-item
Reading List URL-and-title multiset.

This runbook does not change the supported interface boundary. UI focus and
selection can drift, Safari-owned containers cannot necessarily be deleted,
and Safari's visible import/export counts include folders or system objects.
Therefore:

- abort on ambiguous focus, selection, enabled action, or UI refresh state;
- never infer success from Safari's visible object count;
- use parser equality for URL, title, the direct `Favorites -> <subdomain>`
  folder path, and Reading List;
- require exact per-folder sequence equality with the convergence-bound display
  order; set equality alone does not prove ranking success;
- never repeat an action merely because the accessibility refresh is delayed;
- keep `apply-live-safari` blocked and grant no reusable unattended authority.

Detailed operator steps and count semantics live in
`references/browser-knowledge-gateway.md`.

## Private operation input

The operations JSON is private input and must remain outside Git. It is an
array whose entries use an item ID from the parsed export:

```json
[
  {
    "action": "move",
    "item_id": "bri_private_item_id",
    "target_collection": ["Archive"]
  }
]
```

Rules are fail-closed:

- `delete` has no target;
- `move` and `archive` require a non-empty `target_collection` and no target
  item;
- `merge` requires a different `target_item_id` inside the same
  browser/profile/account identity boundary;
- one item can be a source only once, and a merge target cannot also be a
  planned source.

## Workflow

Validate the fictional tracked example:

```sh
python3 scripts/browser_transactions.py validate-plan \
  tests/fixtures/schema_contract/browser-transaction-plan-v1.json
```

Preview one explicit private export and operations file. Preview writes
nothing and prints counts and status only:

```sh
python3 scripts/browser_transactions.py plan-safari-export \
  ~/Downloads/Safari\ Export.zip \
  --operations Private/browser/operations.json
```

Freeze the exact plan into the resolved machine-local state directory:

```sh
python3 scripts/browser_transactions.py plan-safari-export \
  ~/Downloads/Safari\ Export.zip \
  --operations Private/browser/operations.json \
  --apply \
  --confirm "FREEZE BROWSER PLAN"
```

The only mutation above is the atomic plan write below
`browser/plans/<plan-id>.json`. Repeating the same write is idempotent; a
different payload at the same destination is refused.

Before any manual edit, verify that the source export and planned items have
not drifted:

```sh
python3 scripts/browser_transactions.py verify-preapply \
  ~/Library/Application\ Support/install-macos-apps/state/<machine>/browser/plans/<plan-id>.json \
  ~/Downloads/Safari\ Export.zip
```

The live command deliberately stops at the interface boundary:

```sh
python3 scripts/browser_transactions.py apply-live-safari \
  ~/Library/Application\ Support/install-macos-apps/state/<machine>/browser/plans/<plan-id>.json \
  ~/Downloads/Safari\ Export.zip
```

After manually making the reviewed changes in Safari, create a second
Bookmarks-and-Reading-List-only export and verify expected counts:

```sh
python3 scripts/browser_transactions.py verify-post-export \
  ~/Library/Application\ Support/install-macos-apps/state/<machine>/browser/plans/<plan-id>.json \
  ~/Downloads/Safari\ Export-after.zip
```

All CLI summaries omit export paths, item IDs, fingerprints, URLs, titles, and
folder names.

## Recovery and privacy contract

The source export is evidence and a recovery aid, not an exact rollback
artifact. Safari's HTML import appends imported bookmarks after existing
bookmarks; it cannot prove restoration of the exact pre-change graph. A frozen
plan therefore records `manual_import_additive` and
`exact_rollback_supported: false`.

Plans are private machine observations. They may contain the exact export path,
item IDs, fingerprints, identity references, and folder paths. They remain in
machine-local state with mode `0600` and must never enter Git, `Private/`, HTML
reports, diagnostics, or terminal summaries. Raw exports, URLs, titles,
cookies, and sessions are not copied into state.

## Mutation contract

`browser.plan-freeze` is the only registered mutation in this BR-06
foundation. It follows `check -> dry-run -> exact confirmation -> apply ->
read-back` and never writes Safari. The exact phrase is:

```text
FREEZE BROWSER PLAN
```

BR-06 remains open until a supported interface can satisfy all of these gates:

1. stable enumeration and identity for existing bookmarks and Reading List;
2. exact move, merge, archive, and delete semantics;
3. a restorable pre-change backup with documented recovery limits;
4. immediate drift checks and item-scoped confirmation;
5. interruption-safe execution and idempotent retry;
6. browser-visible read-back plus rollback verification;
7. hermetic negative tests and a live-Mac acceptance run.

## Authority evidence

- Apple documents user-mediated Safari data export and its supported data
  categories: <https://developer.apple.com/documentation/safariservices/importing-data-exported-from-safari>.
- Apple documents that importing an HTML bookmarks file adds imported items
  after existing bookmarks: <https://support.apple.com/en-gb/guide/safari/ibrw1015/mac>.
- Safari Services exposes Reading List addition, but does not document an API
  for enumerating and transactionally mutating existing bookmark items:
  <https://developer.apple.com/documentation/safariservices>.
- Safari MCP is for web-development automation and explicitly cannot access
  personal Safari data such as bookmarks or Reading List:
  <https://webkit.org/blog/18136/introducing-the-safari-mcp-server-for-web-developers/>.
