# Safari personal knowledge gateway

## Purpose

BR-10 turns Safari bookmarks from an accumulated archive into a bounded,
renewable entry point for recurring knowledge acquisition. Safari is the
gateway, Reading List is the temporary inbox, and Obsidian remains the durable
knowledge source. A useful article, project note, or conclusion is promoted to
Obsidian rather than preserved indefinitely as a browser bookmark.

This work reuses the reviewed five-domain, fifteen-subdomain taxonomy in
[`browser-organization.md`](browser-organization.md). It does not add a third
semantic folder level and does not modify the current Private organization or
Safari profile.

## Capacity and renewal

The public policy is
[`settings/browser-gateway-policy.json`](../settings/browser-gateway-policy.json):

- maintain about 100 active recurring-source bookmarks, with a 90–110 operating
  range and a target of 100;
- reserve 70 Core slots and 30 trial slots across the 15 subdomains;
- review new sources after 45 days;
- prefer evidence from the latest 365 days when discovering candidates;
- while active bookmarks exceed 100, require at least two reviewed retirements
  for every new source; use one-in-one-out only at 100 or below;
- aim to retire about half of the current legacy set, but select individual
  removals only after evidence-based review.

Each subdomain should maintain a useful mixture of official/primary sources,
professional or research sources, expert/community sources, and data/tools.
The mixture is a selection lens, not a requirement to keep a weak source merely
to fill a category.

## Decision vocabulary

- `keep_gateway`: proven recurring source that belongs in the bounded Core.
- `trial_new`: recent candidate occupying a time-limited trial slot.
- `replace_by`: old source retained only until a reviewed successor is chosen.
- `promote_to_obsidian`: durable knowledge should move to Obsidian, not remain
  a gateway bookmark.
- `archive`: useful historical reference outside the active capacity.
- `delete`: obsolete, duplicate, low-signal, or single-use bookmark.
- `protected`: explicit user exception that capacity review cannot remove.

Selection weights total 100 and favor authority, recency, signal density,
recurring value, and personal relevance. Stale, duplicate, low-signal,
single-use, login-wall, and unverifiable-owner sources receive explicit
penalties. A score is evidence for review, never deletion authority.

## Read-only capacity audit

Run the aggregate audit against the Private organization fact source:

```sh
./bin/macomrade review browser-gateway \
  Private/browser/organization.json
```

The command validates both registered Schemas, counts only active bookmark
`move` decisions, and reports per-subdomain capacity, retirement pressure, and
room for new sources. It emits no URL, title, path, item identifier, or source
hash, writes nothing, and never authorizes Safari mutation.

The key distinction is:

- `current_over_target_count` is the simple reduction needed to reach 100;
- `retirement_review_count` also enforces subdomain caps;
- `new_source_capacity` fills underrepresented domains after that review.

Therefore retirement review can be larger than the net reduction. This is the
mechanism that creates actual information flow instead of only making the
existing collection smaller.

The current reviewed organization contains 282 active bookmarks. Under the
100-source policy, the aggregate audit identifies 196 old entries for review
and 14 available additions in underrepresented domains; applying both produces
the 100-source target. Wave 1 is an approved ledger, not a completed Safari
mutation. If its 20 retirements and 10 additions are completed manually, the
projected active count is 272. From that state, the quota model calls for 185
more retirement reviews and at most 13 additions: one in domain 11 and four
each in domains 21, 42, and 52.

Two-out/one-in is a minimum admission rule, not a requirement to keep adding
sources. Retirement-only waves are expected while converging from a legacy
collection. Re-audit after each manual wave and stop adding as soon as a domain
quota is full; the total must converge toward 100 instead of treating 110 as a
new normal.

## Staged workflow

1. Audit aggregate capacity and identify over/underrepresented subdomains.
2. Discover recent sources for the five priority domains: 11, 13, 22, 31, 42.
3. Compare candidates with existing sources using current evidence and record
   review-only replacement proposals in Private data.
4. Review old items individually as Core, promotion, archive, replacement, or
   delete candidates; titles alone are insufficient evidence.
5. Keep new sources in trial for 45 days, then promote or remove them.
6. Only after a supported or separately approved mutation workflow exists,
   prepare exact Safari operations with export-bound rollback evidence.

No public rule, scan, score, or capacity audit may directly edit Git policy,
Private decisions, Reading List, Obsidian, or Safari.

## Approved wave persistence

An individually reviewed wave may be persisted below
`Private/browser/gateway/` only through:

```sh
./bin/macomrade review browser-gateway-wave \
  Private/browser/organization.json \
  --spec /private/tmp/browser-gateway-wave-spec.json \
  --output Private/browser/gateway/wave-YYYY-MM-DD-NN.json
```

The applied form requires the wave-specific exact confirmation. It validates
the source organization, current item fingerprints, evidence dates, global
same-host consolidation, two-out/one-in ratio, Git-ignore boundary, destination
conflict, mode `0600`, Schema, and read-back. The persisted ledger contains
Private titles and URLs but emits only aggregate counts to stdout.

Render its current execution boundary with:

```sh
./bin/macomrade plan browser-gateway \
  Private/browser/gateway/wave-YYYY-MM-DD-NN.json
```

The plan is intentionally `blocked` while Safari has no supported exact item
write/rollback interface. Approval of the ledger is not approval to edit
Safari, delete a bookmark, or create an Obsidian note.

## Wave 1 manual pilot

The immutable approved Wave 1 is not edited when a later review changes an
archive/delete choice. A final `browser-gateway-pilot-v1` record instead names
the prior `wave_id` and canonical wave hash in `supersedes_wave_id` and
`supersedes_wave_sha256`. Freeze it only below `Private/browser/gateway/`:

```sh
./bin/macomrade review browser-gateway-pilot \
  Private/browser/organization.json \
  Private/browser/gateway/wave-YYYY-MM-DD-NN.json \
  --spec /private/tmp/browser-gateway-pilot-spec.json \
  --output Private/browser/gateway/pilot-YYYY-MM-DD-NN.json
```

The default is a count-only preview. Applied freeze requires exactly `FREEZE
BROWSER GATEWAY PILOT 1`, writes a mode-`0600` Git-ignored Private record
atomically, refuses a different existing destination, and leaves both Safari
execution flags false. It records the ten final exchange groups, four archive
targets, the exact 16-item temporary-removal manifest, required directories,
and all three checkpoint counts. It never edits Safari.

Before Batch A, preserve the original export with the existing evidence-import
transaction, then create a fresh Safari export containing only Bookmarks and
Reading List. Every checkpoint must compare three explicit inputs: the original
source export, the fresh semantic baseline, and the post-operation export.

```sh
./bin/macomrade verify browser-gateway-pilot \
  Private/browser/gateway/pilot-YYYY-MM-DD-NN.json \
  --checkpoint batch-1 \
  --source-export ~/Downloads/Safari-Export-original.zip \
  --baseline-export ~/Downloads/Safari-Export-baseline.zip \
  --current-export ~/Downloads/Safari-Export-after-batch-a.zip \
  --observed-on YYYY-MM-DD
```

Verification is read-only and aggregate-only. It requires semantic equality
between the original and fresh baseline, an unchanged 89-item Reading List,
all non-manifest bookmarks unchanged, every new source exactly once in its
target directory, and every moved old item unchanged except for its approved
directory. Expected bookmark counts are 316 after Batch A, 321 after Batch B,
and 305 after purge. A passed check reports the 45-day review date derived from
the actual observed date.

All 16 removal candidates first move to `98｜Wave 1
待删除（验证后清除）`. Permanent removal remains a separate manual Safari action
and requires the user's adjacent exact confirmation `PURGE BROWSER GATEWAY
PILOT 1`; remove only manifest-bound unchanged items, never clear any other
folder or Reading List. Verify the `purge` checkpoint afterward and remove the
empty temporary directory. The CLI does not interpret a frozen pilot or a
passed batch as purge authority.

The Redis adapter retirement has an additional gate: create and read back an
Obsidian Inbox note with `knowledge_status: inbox` and unverified boundaries
before staging its bookmark. A captured note is not a reviewed endorsement.

## Full-gateway convergence and import package

The manual ten-group pilot is not the final capacity target. The full-gateway
compiler binds a reviewed keep list to the original organization item IDs and
fingerprints, incorporates the immutable pilot additions, and adds only
evidence-backed trial sources needed to reach every subdomain quota:

```sh
./bin/macomrade review browser-gateway-convergence \
  Private/browser/organization.json \
  Private/browser/gateway/pilot-YYYY-MM-DD-NN.json \
  --spec /private/tmp/browser-gateway-convergence-spec.json \
  --output Private/browser/gateway/convergence-YYYY-MM-DD-NN.json
```

Preview emits counts only and writes nothing. Persistence requires the exact
confirmation `FREEZE PRIVATE BROWSER GATEWAY CONVERGENCE 1`. The ledger keeps
all omitted old-bookmark dispositions as Private recovery evidence, preserves
the Reading List count, and requires the reviewed active total to remain inside
the public 90–110 range without exceeding any subdomain quota. It grants no
Safari or package authority.

## Per-folder display order

Do not use alphabetical title order as an importance proxy. Bind a separate
`browser-gateway-order-v1` Private ledger to the exact convergence hash before
generating an import package. Every active source must appear exactly once in
one folder with a contiguous `display_rank` and one of these ordered tiers:

1. `pinned` — at most three personally important entries per folder;
2. `core` — recurring long-term entry points;
3. `monitor` — news, research, and update sources;
4. `trial` — time-limited sources awaiting the 45-day review;
5. `low_frequency` — retained but rarely used sources.

Use title order only as a proposal tie-breaker before review. Persistence
requires an explicit complete order spec and the exact confirmation `FREEZE
PRIVATE BROWSER GATEWAY ORDER 1`:

```sh
./bin/macomrade review browser-gateway-order \
  Private/browser/gateway/convergence-YYYY-MM-DD-NN.json \
  --spec /private/tmp/browser-gateway-order-spec.json \
  --output Private/browser/gateway/order-YYYY-MM-DD-NN.json
```

Preview emits only folder, item, and tier counts. A frozen order remains mode
`0600`, Git ignored, non-authorizing, and independent from Safari. Reject a
missing or duplicated source, wrong folder, non-contiguous rank, tier reversal,
more than three pinned entries, convergence drift, or a different destination.

A frozen convergence ledger can deterministically produce one Netscape HTML
package containing exactly the frozen active ordinary bookmarks. Keep the
five-domain taxonomy in the ledger, but emit only the 15 subdomain folders as
one package level. Safari 27's observed import behavior places those top-level
package folders directly under its system `Favorites` collection:

```sh
./bin/macomrade plan browser-import \
  Private/browser/gateway/convergence-YYYY-MM-DD-NN.json \
  --order Private/browser/gateway/order-YYYY-MM-DD-NN.json \
  --output Private/browser/imports/safari-gateway-YYYY-MM-DD-NN.html
```

The applied form requires `GENERATE PRIVATE SAFARI IMPORT PACKAGE`. It writes
one mode-`0600`, Git-ignored Private file and reparses every URL, title and
folder against the frozen convergence ledger, then compares the exact item
sequence with the frozen order ledger. Reading List and archive entries are
never included. Package generation does not open Safari, clear existing
bookmarks, or authorize import. Clearing ordinary bookmarks and importing the
full file remain separately confirmed live actions after a fresh backup.

## Verified Safari full-replacement cutover

The following supervised runbook was accepted on macOS 27 beta with Safari 27
on 2026-08-15. Revalidate the UI structure and export semantics after a Safari
or macOS upgrade; this evidence does not establish a stable Safari write API.

1. Create a fresh Safari export containing only Bookmarks and Reading List.
   Preserve it as mode `0600` Git-ignored Private evidence, then parse it before
   changing Safari.
2. Bind a separate adjacent confirmation to the exact package and expected URL
   count. Package generation and an earlier ledger freeze are not live-mutation
   authority.
3. Open **Bookmarks -> Edit Bookmarks**. Remove user-created root bookmarks and
   folders, then remove the children of `Favorites`. Do not try to delete
   Safari-owned containers such as `Favorites` itself. Empty system containers
   under `Tab Group Favorites` may be undeletable and are not ordinary bookmark
   URLs.
4. Before every destructive UI action, refresh the accessibility state and
   prove that the exact ordinary-bookmark rows are selected. If selection,
   focus, or the enabled command is ambiguous, stop. Never operate on Reading
   List.
5. Import the deterministic Netscape HTML package through Safari's file import.
   The package must expose `11`–`53` as its only folder level and must not encode
   an additional `Favorites` folder. Safari places those folders directly under
   the existing system `Favorites`, making them visible from the blank/start
   page. Allow the bookmark model and UI to refresh before reading state or
   issuing a second action; a delayed refresh is not permission to repeat the
   import.
6. Export Bookmarks and Reading List again, preserve the export as mode `0600`
   Git-ignored Private evidence, and perform exact parser-based comparison.

Safari's visible counts are not the acceptance authority. In the accepted
99-URL run, the import dialog reported 119 bookmarks because the package also
contained 20 folders, while the later export UI displayed 121 objects after
including Safari-owned containers. The parser correctly reported 99 ordinary
bookmark URLs. Treat these UI counts only as diagnostic observations.

Acceptance is fail-closed and requires all of the following:

- ordinary bookmark count and unique-URL count equal the frozen ledger;
- the multiset of URL, title, and physical one-level subdomain folder exactly
  equals the ledger's final path component;
- every post-import path is exactly `Favorites -> <subdomain>`; Safari's
  inherent leading `Favorites` root is removed only for package/ledger
  comparison, not rewritten in source evidence;
- each folder's post-import URL/title sequence exactly equals the frozen
  `display_rank` order; equal membership with the wrong order is a failure;
- the Reading List URL-and-title multiset is exactly unchanged before and
  after, rather than merely retaining the same count;
- the post-import export is Private, mode `0600`, Git ignored, and parser
  readable.

The accepted live result was 99 unique ordinary bookmarks and an unchanged
89-item Reading List. Computer Use remains a supervised fallback for this
user-confirmed cutover; it is not an unattended or transaction-safe Safari
mutation interface.
