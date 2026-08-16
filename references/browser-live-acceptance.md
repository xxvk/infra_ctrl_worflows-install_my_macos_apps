# Browser live acceptance

## Scope

BR-08 currently supports a Safari-only, read-only acceptance run from one
explicit Bookmarks-and-Reading-List-only Safari export. Chrome remains `deferred_by_user` and
Safari bookmarks/Reading List retain their verified
`shared_across_profiles` model. This is not evidence for Chrome profiles and
does not turn Safari's unavailable item-write interface into a supported
capability.

The tracked ten-gate contract is
[`browser-acceptance.json`](browser-acceptance.json). The redacted result uses
[`browser-acceptance-v1.schema.json`](../schemas/browser-acceptance-v1.schema.json).

## Commands

Validate the hermetic contract and fictional example:

```sh
./bin/macomrade verify browser-acceptance validate
```

Run the minimum live acceptance from one explicitly supplied private export:

```sh
./bin/macomrade verify browser-acceptance inspect-live \
  ~/Downloads/Safari-Bookmarks.zip
```

Add decision-memory and transaction-plan checks only when the corresponding
private inputs have been reviewed:

```sh
./bin/macomrade verify browser-acceptance inspect-live \
  ~/Downloads/Safari-Bookmarks.zip \
  --ledger Private/browser/decision-ledger.json \
  --operations Private/browser/operations.json \
  --as-of YYYY-MM-DD
```

After a separately reviewed manual Safari change, provide a second explicit
Bookmarks-and-Reading-List-only export:

```sh
./bin/macomrade verify browser-acceptance inspect-live \
  ~/Downloads/Safari-Bookmarks.zip \
  --operations Private/browser/operations.json \
  --post-export ~/Downloads/Safari-Bookmarks-after.zip
```

The command emits JSON to standard output and persists nothing. Save or render
that redacted summary only through an explicit shell destination:

```sh
./bin/macomrade verify browser-acceptance inspect-live \
  ~/Downloads/Safari-Bookmarks.zip > /tmp/browser-acceptance.json

./bin/macomrade diagnostics report /tmp/browser-acceptance.json \
  --format tui --lang zh-Hans
```

## Gates

| Gate | Evidence |
| --- | --- |
| `BA-01` | Safari capability metadata supports user-mediated export and reads no private items |
| `BA-02` | Explicit ZIP satisfies the Bookmarks-and-Reading-List-only export contract |
| `BA-03` | Two parses produce equal counts, opaque item order, and semantic fingerprints |
| `BA-04` | Every item preserves the Safari shared-profile, null account/profile boundary |
| `BA-05` | Two normalization and duplicate-review passes are identical |
| `BA-06` | Optional Private decision ledger is valid and produces an identical queue twice |
| `BA-07` | Optional operations produce an identical plan twice and pass immediate preflight |
| `BA-08` | Live apply remains `interface_limited` and performs no write |
| `BA-09` | Optional second export matches the planned post-state fingerprint counts |
| `BA-10` | Chrome acceptance remains explicitly deferred by the user |

Gate status is one of `passed`, `deferred`, `interface_limited`, `failed`, or
`not_run`. Overall `partial` is expected while Chrome is deferred or Safari
live apply remains interface-limited. A partial result must never be presented
as complete 0.3.0 acceptance.

## Privacy and recovery boundary

The acceptance runner opens only the explicit export path supplied on the
command line. It never discovers or reads the internal Safari bookmark plist,
fetches bookmark URLs, follows links, starts Safari, creates an export, imports
bookmarks, freezes a plan, modifies the browser, or writes state.

Private item IDs, fingerprints, URLs, titles, folders, profile/account
references, artifact hashes, input paths, operation details, duplicate groups,
ledger notes, and gate-internal comparisons stay in memory. Output contains
only Safari version/build metadata, aggregate counts, stable gate IDs/statuses,
and stable reason IDs. The live summary is ephemeral machine evidence and is
not Git-authorized.

HTML import remains additive rather than exact rollback. `BA-09` proves only
that a separately supplied post-export matches the frozen expected counts; it
does not prove exact browser rollback. Recovery and live-write gates remain the
BR-06 blocker described in
[`browser-transaction-safety.md`](browser-transaction-safety.md).
