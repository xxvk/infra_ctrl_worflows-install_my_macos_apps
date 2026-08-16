# Browser taxonomy and decision memory

## Scope

BR-05 adds a classification and review-memory layer over private browser items.
It decides when an unchanged item should be shown again; it does not alter
Safari or Chrome, rewrite an export, confirm a canonical URL, or authorize a
merge, move, archive, or deletion.

The tracked public policy is
[`settings/browser-lifecycle-policy.json`](../settings/browser-lifecycle-policy.json).
The personal ledger belongs at `Private/browser/decision-ledger.json`, is
optional, iCloud-synced, and Git-ignored. Copy the fictional structure from
[`examples/private/browser-decision-ledger.json`](../examples/private/browser-decision-ledger.json)
without reusing its IDs or values.

Validate the public policy or an explicit private ledger with:

```sh
python3 scripts/browser_lifecycle.py validate-policy
python3 scripts/browser_lifecycle.py inspect-ledger \
  Private/browser/decision-ledger.json
```

Both commands are read-only. Ledger inspection emits counts only.

## Taxonomy

The five stable built-in classifications and default review intervals are:

| Classification | Intent | Review after |
| --- | --- | ---: |
| `inbox` | Newly collected and not yet organized | 7 days |
| `project` | Supports active work | 90 days |
| `reference` | Durable material expected to remain useful | 180 days |
| `read_later` | Intentionally deferred reading | 30 days |
| `archive` | Retained but not active | 365 days |

These are review intervals, not deletion schedules. A decision may provide a
later explicit ISO date. It must always be after the decision date.

User-defined classifications use a Private `bcx_...` ID, label, review period,
and active/retired status. Labels and notes are personal content. Retiring a
classification preserves historical decisions but prevents new ones.

## Private fingerprint

The lifecycle engine computes a private SHA-256 fingerprint from the identity
boundary, item type, proposed/confirmed canonical URL when available (otherwise
the original URL), title, collection, sorted tags, and read state. It excludes
the export artifact reference, source-position namespace, and `item_id`, so an
unchanged item can survive a new Safari export.

The fingerprint is not an anonymous public identifier: it is derived from
private browser content and must remain in the Private ledger or machine-local
memory. It is never printed by the CLI, diagnostics, or public report.

## Suppression decision

An item is suppressed only when all conditions hold:

1. an active decision matches the exact item ID, or exactly one active decision
   has the same private fingerprint;
2. browser, profile scope/reference, and account reference are identical;
3. the semantic fingerprint is unchanged;
4. the review date is still in the future.

Changed content returns with reason `item_changed`. Expired decisions return as
`review_due`. No match returns as `unreviewed`. Multiple fallback matches return
as `ambiguous_memory`. A matching URL or fingerprint in another account/profile
never inherits the decision.

Recording a replacement decision in memory marks the previous active decision
for the same item and identity as `superseded`; history is retained. The BR-05
module does not write the updated ledger. BR-07 must expose reviewed persistence
through macomrade without printing labels, notes, URLs, item IDs, fingerprints,
or paths.

## Safari review command

An explicit Safari Bookmarks-and-Reading-List-only export can be compared with an explicit
ledger:

```sh
python3 scripts/browser_lifecycle.py review-safari-export \
  /private/path/to/Safari\ Export.zip \
  --ledger Private/browser/decision-ledger.json \
  --as-of 2026-08-14
```

The export parser and BR-04 normalizer run in memory. Output contains only
queued/suppressed counts and stable reason names. It performs no write and does
not retain parsed items.

## Private duplicate review artifact

The aggregate review deliberately does not print the titles, URLs, folders, or
item IDs needed for a human duplicate decision. Produce a dry-run first:

```sh
./bin/macomrade review browser-duplicates \
  /private/path/to/Safari\ Export.zip \
  --output Private/browser/safari-duplicate-review.json
```

The preview prints only group/item counts and writes nothing. After reviewing
the exact destination, an explicit `--apply --confirm "EXPORT PRIVATE BROWSER
REVIEW"` creates one mode-`0600` JSON below `Private/browser/`. The artifact is
bound to the export SHA-256, includes only duplicate candidates and their
decision evidence, is Git-ignored and iCloud-synced, and always retains
`execution_authorized: false`. It is not a decision ledger and does not alter
Safari.
