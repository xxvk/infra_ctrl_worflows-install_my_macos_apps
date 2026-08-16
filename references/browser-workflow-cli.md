# Browser workflow CLI and reports

## Status and scope

BR-07 exposes the Safari bookmark and Reading List workflow through the stable
repository-local `macomrade` command. Each route delegates to the existing
browser script, preserves argument order and exit status, and adds no mutation
flag, confirmation, credential, or privilege.

The JSON emitted by these routes is the fact source. It contains aggregate
counts and stable status identifiers only. The shared audit renderer can turn
those summaries into Simplified Chinese, Japanese, or English plain-terminal
and static HTML views.

## Stable routes

| Route | Compatibility command | Capability |
| --- | --- | --- |
| `scan browser-capabilities` | `browser_sources.py inspect-safari` | Select CLI-first live reads without emitting private items |
| `scan browser` | `safari_export.py inspect` | Count bookmarks and Reading List items in one explicit export |
| `review browser` | `browser_lifecycle.py review-safari-export` | Build a memory-aware review queue |
| `review browser-duplicates` | `browser_review.py export-private-duplicates` | Preview or exact-confirm one duplicate-only Private review artifact |
| `review browser-organization` | `browser_organization.py compile-safari-export` | Preview or exact-confirm one complete Private taxonomy and decision source |
| `review browser-evidence` | `browser_evidence.py import-safari-export` | Preview or exact-confirm one immutable Private Safari export copy |
| `review browser-reconciliation` | `browser_reconciliation.py reconcile-safari-export` | Compare source drift or exact-confirm one versioned organization candidate |
| `review browser-gateway` | `browser_gateway.py audit-organization` | Audit aggregate active capacity, retirement pressure, and room for recent sources |
| `review browser-gateway-wave` | `browser_gateway.py sync-wave` | Preview or exact-confirm one approved Private two-out/one-in wave ledger |
| `review browser-gateway-convergence` | `browser_gateway_convergence.py freeze` | Preview or exact-confirm one Private 90–110-source convergence ledger |
| `review browser-gateway-order` | `browser_gateway_order.py` | Preview or exact-confirm one complete convergence-bound display order |
| `plan browser-gateway` | `browser_gateway.py plan-wave` | Render an approved wave as a redacted non-executable migration plan |
| `plan browser-import` | `browser_gateway_convergence.py generate-import` | Preview or exact-confirm one deterministic bounded Private HTML package |
| `plan browser` | `browser_transactions.py plan-safari-export` | Preview or exact-confirm freeze a private plan |
| `apply browser` | `browser_transactions.py apply-live-safari` | Recheck drift, then stop at the unavailable supported write interface |
| `verify browser` | `browser_transactions.py verify-post-export` | Compare expected counts with a second explicit export |
| `history browser` | `browser_lifecycle.py inspect-ledger` | Validate private decision memory and emit counts |

`plan browser` is mutation-capable only because its underlying `--apply` mode
can freeze one mode-`0600` plan in machine-local state. It still requires the
exact `FREEZE BROWSER PLAN` confirmation and never writes Safari.
`apply browser` remains read-only and returns `blocked` with
`supported_item_write_interface_unavailable` after a successful preflight;
it is never the live-write route.
`scan browser-capabilities` probes only Safari metadata plus `macos-data`
version/root help. When `macos-data >= 0.8.0` exposes its Safari read commands,
live list/query/get work is CLI-first. When installed `macos-data >= 0.8.1`
also exposes guarded bookmark/folder CRUD, **that CLI is the direct local-only
write route for bookmark and folder organization** — see the CRUD contract
below. The export-bound `apply browser` bridge remains blocked until it can
map and verify a frozen plan safely, and is not used for live organization.
`scan browser` remains the immutable-export route. An installed older binary
does not inherit capability from a newer source checkout. Use
`MACOS_DATA_CLI=/path/to/macos-data` explicitly when a reviewed build should
take precedence over PATH.

### Local-only CLI CRUD (default write path)

With `macos-data >= 0.8.1`, bookmark and folder organization runs through the
guarded CRUD commands. Input is strict JSON on `--stdin` (or `--input`).
Dry-run is the default; copy `sourceSHA256Before` into `expectedSourceSHA256`
for `--apply`. **Safari must be fully quit** before any apply. Deletes require
the exact confirmation phrase. Every result reports `syncStatus=local_only`:
the user triggers the final iCloud synchronization by reopening Safari.

```sh
# create one bookmark
printf '%s' '{"parentID":"<folder-id>","index":0,"title":"Example","url":"https://example.com"}' \
  | macos-data safari bookmarks create --stdin --format json

# edit: dry-run first for the source hash, then apply with it
printf '%s' '{"id":"<bookmark-id>","title":"Updated","expectedSourceSHA256":"<dry-run-hash>"}' \
  | macos-data safari bookmarks edit --stdin --apply --format json

# move one bookmark
printf '%s' '{"id":"<bookmark-id>","parentID":"<target-folder-id>","index":0,"expectedSourceSHA256":"<dry-run-hash>"}' \
  | macos-data safari bookmarks move --stdin --apply --format json

# delete one bookmark (exact phrase)
printf '%s' '{"id":"<bookmark-id>","expectedSourceSHA256":"<dry-run-hash>"}' \
  | macos-data safari bookmarks delete --stdin --apply \
      --confirm "DELETE SAFARI BOOKMARK" --format json
```

Folder operations mirror the bookmark set (`folders create|rename|move|delete`,
delete confirmation `DELETE SAFARI FOLDER`, empty folders only). Never
interpret a successful local read-back as iCloud synchronization; the user
decides when Safari reopens and syncs.

### Sorting bookmarks (move + index)

Bookmark ordering inside a folder is the same guarded `bookmarks move`
operation with a different target index — **no separate reorder command or
extension is needed**. `bookmarks move` and `folders move` require
`{"id", "parentID", "index"}`; moving an item to a new `index` within its own
folder is how order is changed, and moving across folders also places the item
at the requested position. The engine removes the node and inserts it at
`childIndex` with cycle detection, writable-folder validation, and an
untouched-node preservation check.

```sh
# dry-run: returns sourceSHA256Before
printf '%s' '{"id":"<bookmark-id>","parentID":"<same-folder-id>","index":0}' \
  | macos-data safari bookmarks move --stdin --format json

# apply: same payload plus the dry-run hash
printf '%s' '{"id":"<bookmark-id>","parentID":"<same-folder-id>","index":0,"expectedSourceSHA256":"<dry-run-hash>"}' \
  | macos-data safari bookmarks move --stdin --apply --format json
```

Sorting rules that keep a reorder safe:

- **Plan the full desired order first**, then emit one move per item with its
  target `index`. Execute moves in **descending index order** (last position
  first) so earlier moves never shift the target positions of later ones.
- Each move is an independent guarded transaction: dry-run → hash → apply →
  read-back. A `readback_confirmed` verification means the plist round-trip
  passed; the moved item is present at its requested position.
- Unspecified items naturally fill the remaining slots; a full reorder must
  therefore list **every** bookmark of the folder, not only the items that
  move to the front.
- Ordering is `local_only` until the user reopens Safari; never claim that a
  reordered local plist has synchronized to other devices.
- IDs are stable across Safari quits (verified), but re-run `bookmarks list`
  to refresh the id map before planning a large reorder.
`review browser-duplicates` is preview-only by default. Its applied mode writes
one schema-validated JSON below `Private/browser/`, requires the exact
`EXPORT PRIVATE BROWSER REVIEW` confirmation, creates mode `0600`, refuses a
different existing destination, emits only counts to stdout, and never writes
Safari.
`review browser-organization` follows the same non-Safari-write boundary and
requires `SYNC PRIVATE BROWSER ORGANIZATION`. It asserts complete item
coverage, reviewed counts, taxonomy targets, duplicate membership, source
hash, mode `0600`, and `execution_authorized: false`.
`review browser-evidence` derives a hash-bound destination below
`Private/browser/evidence/`. Applied import requires
`IMPORT PRIVATE BROWSER EVIDENCE`, preserves exact source bytes, verifies the
copy by hash and parser read-back, and never prints the path or hash.
`review browser-reconciliation` carries forward only unambiguous semantic
fingerprints, exact path rules, and stable duplicate membership. It writes no
candidate by default. Applied candidate persistence requires `WRITE PRIVATE
BROWSER RECONCILIATION CANDIDATE` and never switches the canonical file.
`review browser-gateway` is always read-only. It validates the public capacity
policy and Private organization, then emits only per-subdomain counts. It never
prints a URL, title, path, item ID, or source hash and grants no Safari authority.
`review browser-gateway-wave` writes only after its exact confirmation. The
mode-`0600` Private ledger binds every proposed source to current evidence and
active retirement fingerprints, remains non-executable, and does not change
the canonical organization or Safari.
`review browser-gateway-pilot` supersedes but never overwrites the approved
wave. It freezes the final ten exchange groups, exact staging manifest and
three expected checkpoints after `FREEZE BROWSER GATEWAY PILOT 1`; stdout is
aggregate-only and Safari remains manual. `verify browser-gateway-pilot`
compares explicit original, baseline and current Safari exports for Batch A,
Batch B or purge, rejecting Reading List, target, count, partial-group and
non-manifest drift without writing any state.
`review browser-gateway-convergence` binds retained legacy item fingerprints,
pilot sources, current trial evidence and subdomain quotas into one reviewed
90–110-source total. Its mode-`0600` Private ledger keeps omitted-item
dispositions and the Reading List preservation contract but grants no Safari
authority. `review browser-gateway-order` requires explicit contiguous ranks
for every active source, limits each folder to three pinned entries, enforces
the tier sequence, and writes only after `FREEZE PRIVATE BROWSER GATEWAY ORDER
1`. `plan browser-import` requires both frozen ledgers, writes only after its
independent exact confirmation, and reparses the deterministic HTML against
their membership and sequence;
the package contains neither Reading List nor archive entries, flattens the
conceptual domain/subdomain taxonomy into 15 direct subdomain folders for the
system `Favorites` collection, and is not import authorization.

## Commands

Save each redacted JSON summary to an explicitly selected local file when a
human-readable report is needed:

```sh
./bin/macomrade scan browser-capabilities

MACOS_DATA_CLI=/path/to/macos-data \
  ./bin/macomrade scan browser-capabilities

./bin/macomrade scan browser ~/Downloads/Safari-Bookmarks.zip \
  > /tmp/browser-scan.json

./bin/macomrade review browser ~/Downloads/Safari-Bookmarks.zip \
  --ledger Private/browser/decision-ledger.json \
  --as-of 2026-08-14 \
  > /tmp/browser-review.json

./bin/macomrade review browser-duplicates ~/Downloads/Safari-Bookmarks.zip \
  --output Private/browser/safari-duplicate-review.json

./bin/macomrade review browser-duplicates ~/Downloads/Safari-Bookmarks.zip \
  --output Private/browser/safari-duplicate-review.json \
  --apply --confirm "EXPORT PRIVATE BROWSER REVIEW"

./bin/macomrade review browser-organization ~/Downloads/Safari-Bookmarks.zip \
  --spec /private/tmp/browser-organization-spec.json \
  --output Private/browser/organization.json

./bin/macomrade review browser-evidence ~/Downloads/Safari-Bookmarks.zip \
  --exported-on 2026-08-15

./bin/macomrade review browser-evidence ~/Downloads/Safari-Bookmarks.zip \
  --exported-on 2026-08-15 \
  --apply --confirm "IMPORT PRIVATE BROWSER EVIDENCE"

./bin/macomrade review browser-reconciliation \
  Private/browser/organization.json \
  ~/Downloads/Safari-Bookmarks-new.zip \
  --reconciled-on 2026-08-16

./bin/macomrade review browser-gateway \
  Private/browser/organization.json

./bin/macomrade review browser-gateway-convergence \
  Private/browser/organization.json \
  Private/browser/gateway/pilot-YYYY-MM-DD-NN.json \
  --spec /private/tmp/browser-gateway-convergence-spec.json \
  --output Private/browser/gateway/convergence-YYYY-MM-DD-NN.json

./bin/macomrade review browser-gateway-order \
  Private/browser/gateway/convergence-YYYY-MM-DD-NN.json \
  --spec /private/tmp/browser-gateway-order-spec.json \
  --output Private/browser/gateway/order-YYYY-MM-DD-NN.json

./bin/macomrade plan browser-import \
  Private/browser/gateway/convergence-YYYY-MM-DD-NN.json \
  --order Private/browser/gateway/order-YYYY-MM-DD-NN.json \
  --output Private/browser/imports/safari-gateway-YYYY-MM-DD-NN.html

./bin/macomrade review browser-gateway-pilot \
  Private/browser/organization.json \
  Private/browser/gateway/wave-YYYY-MM-DD-NN.json \
  --spec /private/tmp/browser-gateway-pilot-spec.json \
  --output Private/browser/gateway/pilot-YYYY-MM-DD-NN.json

./bin/macomrade verify browser-gateway-pilot \
  Private/browser/gateway/pilot-YYYY-MM-DD-NN.json \
  --checkpoint batch-1 \
  --source-export ~/Downloads/Safari-Export-original.zip \
  --baseline-export ~/Downloads/Safari-Export-baseline.zip \
  --current-export ~/Downloads/Safari-Export-after-batch-a.zip \
  --observed-on YYYY-MM-DD

./bin/macomrade plan browser ~/Downloads/Safari-Bookmarks.zip \
  --operations Private/browser/operations.json \
  > /tmp/browser-plan-preview.json

./bin/macomrade plan browser ~/Downloads/Safari-Bookmarks.zip \
  --organization Private/browser/organization.json \
  > /tmp/browser-plan-preview.json

./bin/macomrade plan browser ~/Downloads/Safari-Bookmarks.zip \
  --operations Private/browser/operations.json \
  --apply --confirm "FREEZE BROWSER PLAN"

./bin/macomrade apply browser \
  ~/Library/Application\ Support/install-macos-apps/state/<machine>/browser/plans/<plan-id>.json \
  ~/Downloads/Safari-Bookmarks.zip

./bin/macomrade verify browser \
  ~/Library/Application\ Support/install-macos-apps/state/<machine>/browser/plans/<plan-id>.json \
  ~/Downloads/Safari-Bookmarks-after.zip \
  > /tmp/browser-verify.json

./bin/macomrade history browser \
  Private/browser/decision-ledger.json \
  > /tmp/browser-history.json
```

Private exports, operations, ledgers, and frozen plans stay outside Git. Shell
redirection is an explicit local choice; `macomrade` does not silently persist
scan, review, apply, verify, or history output.

## Localized presentation

Render any supported redacted browser summary:

```sh
./bin/macomrade diagnostics report /tmp/browser-review.json \
  --format tui --lang zh-Hans

./bin/macomrade diagnostics report /tmp/browser-verify.json \
  --format html --lang ja --output /tmp/browser-verify.html
```

The renderer accepts only these fixed summary kinds:

- `safari_export_redacted_summary`;
- `browser_review_redacted_summary`;
- `browser_lifecycle_redacted_summary`;
- `browser_transaction_redacted_summary`;
- `browser_transaction_apply_summary`;
- `browser_transaction_verification_summary`;
- `browser_history_redacted_summary`.

It copies only allowlisted integer, boolean, and fixed-status aggregate fields.
Raw parser output, frozen plans, unknown browser document kinds, and any input
that does not explicitly declare private content absent and execution
unauthorized are rejected. Reports never contain an export path, URL, title,
folder, account/profile reference, item ID, fingerprint, operation detail,
ledger note, or browser-write authority.

## Accessibility and mutation boundary

The terminal view uses plain text without ANSI or color dependence. Static
HTML has one semantic main region, headings, row headers, a textual status
label, no script, no remote asset, and no telemetry. Locale changes affect
human labels only; route names, JSON fields, action IDs, status IDs, and exact
confirmation phrases remain stable English identifiers.

BR-07 completes workflow exposure, not live Safari mutation. BR-06 remains
open until a supported interface provides stable item identity, exact
move/merge/archive/delete operations, recovery, drift checks, interruption
safety, browser-visible read-back, and rollback verification.

BR-08 Safari-only repeat-run and optional post-export acceptance is exposed as
`macomrade verify browser-acceptance`; see
[`browser-live-acceptance.md`](browser-live-acceptance.md).

If a later Safari export has a different hash, `plan browser --organization`
must stop. Do not edit the stored hash or reuse export-bound item IDs by hand.
Preserve both exports and follow the reconciliation contract in
[`browser-organization.md`](browser-organization.md). Versioned candidate
generation is supported; canonical promotion and rollback acceptance remain
pending work, not hidden compatibility behavior.
