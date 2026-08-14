# Memory-backed storage lifecycle

## Contents

- [Contract](#contract)
- [Configuration and state](#configuration-and-state)
- [Commands](#commands)
- [Facts and scanning](#facts-and-scanning)
- [Live Mac and OS boundaries](#live-mac-and-os-boundaries)
- [Decision memory](#decision-memory)
- [Planning](#planning)
- [Transactions](#transactions)
- [Mole evidence](#mole-evidence)
- [Weekly scan](#weekly-scan)
- [Validation](#validation)

## Contract

Use macomrade as a storage decision layer, not as a second disk-usage display.
Optimize for actual local free space and stop as soon as the measured volume
reaches its target. `compact` targets 50 GiB free and `expanded` targets
100 GiB; `auto` selects `expanded` at 512 GiB total capacity and above. A
Private override may select another byte target.

Mole remains an optional candidate explorer and historical evidence source.
Neither Mole's displayed size nor imported history is capacity authority or
execution authorization. The macomrade fact layer keeps logical bytes,
allocated bytes, estimated reclaimable bytes, staged bytes, and measured
reclaimed bytes separate.

Do not route WeChat, Claude, or another proprietary application database
through this generic lifecycle. Aggregate `~/Library/Application Support` for
visibility only and hand application-owned data to an App Adapter.

## Configuration and state

Use three layers:

1. `settings/storage-policy.json` contains public thresholds, roles, scan
   roots, provider boundaries, protected paths, and cache regeneration proof.
2. `Private/storage-policy.json` contains personal path patterns, archive
   targets, and target overrides. It is iCloud-synced and Git-ignored.
3. The resolved machine-local state contains exact paths, sizes, scans,
   decisions, plans, Mole evidence, transaction manifests, and verification.

Start a personal policy from
[`examples/private/storage-policy.json`](../examples/private/storage-policy.json).
Private rules may classify, rank, archive, protect, and suppress repeated
questions on another Mac. They always retain `execution_authorized: false`.
Secrets, provider tokens, document content, and raw private filenames never
belong in a tracked export.

All five storage contracts are registered Draft 2020-12 JSON Schemas:

- policy;
- scan and candidate;
- decision ledger;
- frozen plan;
- apply and verify transaction records.

## Commands

Run the workflow in order:

```sh
./bin/macomrade scan storage --mode quick
./bin/macomrade scan storage --mode deep
./bin/macomrade review storage --candidate ID --decision keep_local
./bin/macomrade review storage --candidate ID --decision keep_local --apply
./bin/macomrade plan storage --target auto
./bin/macomrade plan storage --target +10GiB
./bin/macomrade plan storage --target-free 80GiB
./bin/macomrade apply storage PLAN --action-class safe_cache \
  --confirm 'PURGE APPROVED REGENERABLE CACHES'
./bin/macomrade apply storage PLAN --action-class safe_cache --apply \
  --confirm 'PURGE APPROVED REGENERABLE CACHES'
./bin/macomrade verify storage APPLY_RECORD
./bin/macomrade history storage
```

`scan`, `plan`, and `history` do not clean. `review` writes a machine-local
non-authorizing decision only when `--apply` is present. `apply` performs no
storage mutation without both `--apply` and its exact action-class
confirmation. The dispatcher never adds either argument.

Use `--root PATH` to scan an external disk or NAS explicitly. They are never
default scan roots. Third-party File Provider content is read-only in 0.2.0;
perform its local-copy action in the provider's supported UI.

`--target +10GiB` requests ten additional GiB above the scan's current free
space. `--target-free 80GiB` requests an absolute free-space floor. Binary
`KiB`/`MiB`/`GiB`/`TiB`, decimal `KB`/`MB`/`GB`/`TB`, raw bytes, role names,
and `auto` are distinct recorded target requests; a plan never silently
converts an additional-reclaim request into a role target.

## Facts and scanning

The Python orchestrator collects metadata without following symbolic links or
crossing an unrequested filesystem. It deduplicates hard links by device and
inode. Sparse files retain distinct logical and allocated size. APFS clone
exclusive ownership is not publicly attributable through this implementation,
so clone-sensitive candidates carry reduced confidence.

For clone-sensitive trees, even a successful deletion does not prove that the
displayed allocated bytes were exclusively reclaimable. Keep the pre-cleanup
tree measurement as evidence, but calculate reclaimed capacity only from the
same volume's free-byte readings around the transaction. Normal filesystem
activity may make that delta slightly negative; in that case credit zero and
record the difference as measurement noise. Chrome code-sign clones require
the app-specific recovery flow in
[`application-maintenance.md`](application-maintenance.md), not generic cache
purging.

Application-managed libraries such as `.photoslibrary`, `.photolibrary`,
`.musiclibrary`, `.imovielibrary`, and `.fcpbundle` are hard protected facts,
not generic user folders. A tree containing a `.git` repository marker is also
hard protected. Private policy cannot convert either class directly into an
iCloud, archive, or Trash action; use the owning App Adapter or a separately
reviewed source-control workflow.

The checked-in Swift Foundation helper is compiled into machine-local state;
the binary is never tracked. It reads iCloud upload, upload-in-progress,
download, conflict, allocation, resource-identifier, volume, and capacity
metadata. It never opens a dataless file. Its mutation surface is restricted
to Foundation's local-copy eviction, local-copy download request, and
manifest-returning Trash operation.

[`FileManager.evictUbiquitousItem(at:)`](https://developer.apple.com/documentation/foundation/filemanager/evictubiquitousitem%28at%3A%29)
removes an iCloud item's local copy without deleting its cloud copy. Verify
[`ubiquitousItemDownloadingStatusKey`](https://developer.apple.com/documentation/foundation/urlresourcekey/ubiquitousitemdownloadingstatuskey),
upload completion, and unresolved conflicts before eviction.

Quick scan records volume and configured root aggregates plus read-only APFS,
snapshot, VM/swap, protected-system, and Home overview facts. Mole may provide
the bounded Home overview, but it remains labeled `mole_evidence_only` and is
never capacity authority. Deep scan expands only an aggregate that crosses the
candidate threshold, then classifies its immediate children. It also performs
one bounded Home top-level allocated-size traversal and records exact
threshold-crossing `/private/tmp` directories and installed optional Apps as
`manual_handoff` candidates. A handoff is never eligible for a generic storage
transaction, even after a retention decision; it must be routed to the owning
workflow or App uninstaller.

Defaults are Desktop, Documents, Downloads, Movies, Pictures, and known
Homebrew/npm/pnpm/uv/Mole/Gradle/Puppeteer/node-gyp/Playwright/Xcode caches.
The full machine-local JSON retains all findings; tracked scan policy retains
up to 50 summary candidate IDs, while the console renders the first 20 compact
candidates and 20 Home facts. Any denied or incomplete deep traversal
sets `system_facts.status: partial` without exporting raw error paths.

Deep scan still expands a threshold-crossing aggregate when the aggregate is
review-only, and retains its threshold-crossing children as review proposals.
Expansion is evidence collection, not execution eligibility.

Candidate thresholds are allocated bytes of at least 100 MiB, or cloud logical
bytes of at least 1 GiB with small local allocation. The latter is useful
placement evidence but is not a high-value reclaim target when local
allocation is already below 100 MiB.

Deep mode also has a separate developer-artifact proof path for
`node_modules`, `.next`, `.turbo`, `.parcel-cache`, Gradle `build`/`.gradle`,
and Maven `target`. A directory is eligible only when all of these remain true:

- its owning Git repository ignores the exact path;
- `git ls-files` finds no tracked file below it;
- the project has a matching lockfile or build manifest from which the
  directory can be regenerated;
- no running process has its working directory anywhere inside that project;
- allocated bytes cross the normal candidate threshold.

The same evidence is recomputed immediately before deletion. If `lsof` cannot
provide process working directories, the artifact fails closed. Do not add a
generic `dist` rule: release output and hand-built artifacts are too ambiguous.

## Live Mac and OS boundaries

Use APFS container capacity, not a recursive directory total, as the free-space
authority on a live Mac:

```sh
df -k /
diskutil apfs list
diskutil apfs listSnapshots /
sysctl vm.swapusage
```

`diskutil apfs list` identifies the actual capacity consumed by System,
Preboot, Recovery, Data, and VM volumes. `df` supplies the before/after reading
for the mounted target volume. `du` remains path evidence only: APFS clones,
sparse files, hard links, sealed snapshots, and Preboot cryptex content can
make recursive totals differ materially from exclusive reclaimable capacity.
`tmutil listlocalsnapshots /` is not a substitute for the APFS snapshot query;
a sealed update snapshot may appear only through `diskutil`, and a snapshot
reported as non-purgeable is never a cleanup candidate.

Treat `/System/Volumes/VM` as OS-managed runtime state. Record both the VM
volume allocation and `vm.swapusage`. A normal reboot can shrink swap and
release unlinked files still held by old processes, but that is temporary
headroom: swap grows again under memory pressure and must not be credited as a
durable storage decision. Re-scan after reboot before claiming measured
reclaim.

Do not manually remove Preboot, Recovery, sealed snapshots, `/private/var/db`,
Spotlight/CoreSpotlight, Biome, CloudKit, or
`/System/Volumes/Data/System/Library/AssetsV2`. For a large system asset,
identify and visibly read back the owning feature first. Disabling Apple
Intelligence, Siri, dictation, translation, voices, or another system feature
is a feature mutation requiring its own explicit approval; only the measured
post-change volume delta counts. The absence of a usable feature toggle, such
as Apple Intelligence being unavailable because Mac and Siri languages do not
match, means the asset is not an executable proposal.

Inspect `/private/tmp` by exact directory, owner, age, and provenance. Require
that `lsof +D EXACT_PATH` and related process checks find no user before
proposing removal. Never allowlist or empty `/private/tmp` as a whole. A
preview, dependency audit, or installer tree is still review-only until its
creating workflow is identified and the exact directory is frozen in a plan.

App-owned storage keeps its app boundary during OS triage:

- Photos libraries remain protected. Read **Photos → Settings → iCloud**;
  when **Optimize Mac Storage** is already selected, the library is not a
  high-confidence reclaim target. Never delete library internals.
- Mail databases remain protected. Read each account's **Mail → Settings →
  Accounts → Account Information → Download Attachments** policy. Changing
  `All` to `Recent` may reduce future/local attachment retention, but it is a
  separately authorized preference change and its benefit is measured only
  afterward. Do not delete `~/Library/Mail` internals.
- An app runtime that is documented as re-downloadable is still ineligible
  while the app, helper, or current agent task uses it. Reclaim that will return
  on the next launch or task is labeled transient, not durable.
- Xcode and Command Line Tools are distinct capabilities. Never delete SDKs or
  `/Library/Developer` subtrees directly; uninstall the owning product through
  its component workflow and preserve a valid `xcode-select` target.
- An installed optional App is a removal opportunity, not a safe-cache
  candidate. Record the App bundle's allocated bytes, catalog component, and
  guide as a `manual_handoff`; use the app-management workflow to inspect user
  data, uninstall source, container cleanup, and rollback separately.

For a requested amount beyond the role target, show two curves: measured
immediate headroom (including transient swap/runtime effects) and durable
reclaim (files, applications, or retained data that will not automatically
return). Never combine the two to imply a permanent result.

## Decision memory

Use only these stable decisions:

```text
keep_local
cloud_on_demand
archive
review_after
safe_cache
delete_after_backup
protected
unknown
```

`protected` remains active until explicitly replaced. `keep_local` is reviewed
after 180 days and `safe_cache` after 30 days. `review_after` requires an ISO
date. `cloud_on_demand` returns to review when materialization or another
fingerprint change occurs. An unchanged candidate remains suppressed before
its review deadline.

An unreviewed ordinary file or iCloud item has `action_class: review`,
`eligible: false`, and zero estimated reclaimable bytes. Its non-authorizing
`proposed_action_class` may explain the likely next choice, but it never enters
a frozen executable plan. Only an explicit reusable rule such as
`safe_cache`, `cloud_on_demand`, `archive`, or `delete_after_backup` can promote
the corresponding class after review; even then, the rule is not execution
authorization.

To promote reviewed local decisions into personal cross-Mac intent, inspect
the ledger first and use the separate exact confirmation:

```sh
./bin/macomrade apply storage "$LEDGER" --action-class decision_sync \
  --confirm 'SYNC STORAGE DECISIONS'
./bin/macomrade apply storage "$LEDGER" --action-class decision_sync --apply \
  --confirm 'SYNC STORAGE DECISIONS'
```

This writes only personal patterns and decisions to `Private/`; it removes
machine measurements and never grants future execution.

## Planning

A frozen plan binds its source scan, plan hash, path fingerprint, inode, size,
cloud state, target volume, and free-space target. It shows:

1. a low-risk curve for iCloud local-copy eviction and proven regenerable
   caches;
2. a reversible curve for archive and Trash staging;
3. the minimum ordered action set needed to reach the target.

Filter ineligible and low-confidence candidates before ranking actual
reclaimable allocation. Staging a source in Trash is not a measured reclaim.
Never combine estimated, staged, or measured values under one `saved` field.
Protected app libraries, source repository trees, and unreviewed proposals are
never members of the minimum action set.

## Transactions

Execute exactly one action class per command. Use only these confirmation
strings:

```text
REMOVE ICLOUD LOCAL COPIES
PURGE APPROVED REGENERABLE CACHES
ARCHIVE VERIFIED STORAGE ITEMS
MOVE STORAGE ITEMS TO TRASH
PURGE MANIFEST BOUND TRASH ITEMS
RESTORE STORAGE ITEMS
SYNC STORAGE DECISIONS
```

Immediately before each action, recheck the plan hash and candidate identity.
Stop on replacement, size change, inode change, cloud drift, or insufficient
archive capacity. After every completed item, remeasure volume free space. If
the target is reached, stop the remaining list and require a new scan and plan.

For iCloud, require uploaded, not uploading, no unresolved conflict, not
downloading, and nonzero local allocation. For cache purge, require a public
allowlist rule with regeneration proof, or the complete dynamic Git-artifact
proof above. Cache purge has no content-level rollback. Mole's own
`~/.cache/mole` is an allowlisted regenerable scan cache; clearing it may make
the next Mole analysis slower and removes local acceleration/history evidence,
but not user files or Mole's tracked protection policy.

For archive, require a Private destination that is online and has enough
capacity. Verify a write/read probe, copy the source, and compare metadata and
content hashes before staging the source in Trash. Refuse an existing
destination.

Trash operations retain the exact resulting Trash path and recovery mapping.
Permanent purge is a second command against that apply record; it removes only
unchanged manifest-bound items and never empties the whole Trash:

```sh
./bin/macomrade apply storage APPLY_RECORD --action-class trash_purge --apply \
  --confirm 'PURGE MANIFEST BOUND TRASH ITEMS'
```

Restore an unpurged manifest with:

```sh
./bin/macomrade apply storage APPLY_RECORD --action-class restore --apply \
  --confirm 'RESTORE STORAGE ITEMS'
```

Time Machine freshness is warning evidence, not a purge bypass or hard block.
The precise frozen manifest and exact purge confirmation remain mandatory.

An apply record owns the before/after measurement for that transaction.
`verify` must preserve those values and write the later volume reading as
`observed_free_bytes_at_verify`; it must never credit unrelated cleanup that
happened after apply. Once measured free space reaches the role target, stop
the remaining actions and create a new scan and plan.

## Mole evidence

Import Mole's supported history interface only:

```sh
./bin/macomrade history storage --import-mole
```

This invokes `mole history --json`. A user-provided Mole analyze JSON may be
imported with `--import-mole-json FILE`. Never call a private executable from
Mole's Cellar. Imports are content-addressed and idempotent, marked
`evidence_only`, and never infer a retention decision or authorization.

## Weekly scan

The default remains manual. An external weekly scheduler may call:

```sh
./bin/macomrade scan storage --mode quick --weekly
```

The weekly mode is read-only. It skips on low battery, deduplicates unchanged
candidate fingerprints, and honors a one-week notification cooldown. Notify
only when free space is below target or at least 5 GiB of new high-confidence
reclaimable allocation appears. It never invokes apply.

## Validation

Run:

```sh
python3 -m unittest tests.test_storage_lifecycle
./bin/macomrade verify schemas
./bin/macomrade diagnostics benchmark --operation storage_scan --operation storage_plan
python3 scripts/release_check.py
```

Live acceptance must also compile the Swift helper, inspect the two known
iCloud samples without materializing them, and prove that their multi-GiB
logical size but sub-MiB local allocation does not become a high-value reclaim
recommendation. It must run both a quick system-fact scan and a deep handoff
scan, retain the complete record machine-locally, cap terminal summaries, and
surface partial traversal rather than claiming complete coverage. A live run
is integration evidence, not authorization to offload, uninstall, archive,
Trash, purge, or restore anything.
