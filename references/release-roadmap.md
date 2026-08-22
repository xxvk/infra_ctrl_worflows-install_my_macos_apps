# Release roadmap

## Contents

- [Product direction](#product-direction)
- [Version policy](#version-policy)
- [0.1.0 — reproducible Mac baseline](#010--reproducible-mac-baseline)
- [0.1.1 — public source release readiness](#011--public-source-release-readiness)
- [0.2.0 — memory-backed storage management](#020--memory-backed-storage-management)
- [0.3.0 — browser bookmarks and reading lists](#030--browser-bookmarks-and-reading-lists)
- [0.4.0 — notes lifecycle](#040--notes-lifecycle)
- [0.5.0 — SSH key lifecycle](#050--ssh-key-lifecycle)
- [0.6.0 — application-specific storage adapters](#060--application-specific-storage-adapters)
- [0.7.0 — photo review and cleanup](#070--photo-review-and-cleanup)
- [0.8.0 — WeChat group lifecycle](#080--wechat-group-lifecycle)
- [0.9.0 — iPhone intelligence and Home Screen lifecycle](#090--iphone-intelligence-and-home-screen-lifecycle)
- [1.0.0 — native macOS product](#100--native-macos-product)
- [Product idea pool](product-ideas.md)

## Product direction

Build a local-first macOS operating and data-lifecycle system that makes a new
Mac ready after one repository sync and keeps the machine useful over time.
Optimize for actual local free space, reduced repeated decisions, reversible
operations, and explainable recommendations. A large logical file, cache, or
cloud placeholder is never sufficient evidence for deletion.

Use five evidence layers:

1. **Portable policy** — reviewed intent that can be synced to another Mac.
2. **iCloud-synced private configuration** — user-approved personal
   identifiers, account mappings, names, and preferences under Git-ignored
   `Private/`, synchronized by the surrounding iCloud Drive folder.
3. **Long-term local memory** — prior decisions and measured outcomes on one
   Mac; ignored by Git unless the user explicitly promotes a reusable rule.
4. **Short-term observation** — current size, age, allocation, synchronization,
   process, and access evidence.
5. **Protected secrets, sessions, and private payload content** — passwords,
   tokens, private keys, raw authorization databases, session material, and
   private document contents are never persisted in the repository; inspect
   only the minimum metadata required for the workflow.

Every destructive workflow follows:

```text
inspect → classify → preview → confirm → apply → measure → verify → remember
```

## Version policy

`VERSION` is the repository version source of truth. Use Semantic Versioning:

- `0.MINOR.0` adds a planned capability or changes a pre-1.0 workflow contract.
- `0.MINOR.PATCH` fixes or documents the current minor version without adding a
  new product domain.
- `1.0.0` is the first stable native macOS product release.

Roadmap status has six values:

- **shipped** — implemented and represented by current repository artifacts.
- **release_candidate** — the intended version baseline is implemented, but
  release gates remain open; it is not yet a released or tagged version.
- **committed** — accepted scope, not yet complete.
- **proposed** — recommended direction requiring user approval.
- **undecided** — a version slot exists, but no product scope is assigned.
- **candidate** — idea pool; not assigned to a release.

A version is complete only when its scripts and schemas validate, dry-run and
verification paths exist for destructive operations, machine state remains
outside tracked configuration, documentation matches behavior, and a release
commit may be tagged.
Creating a tag, commit, GitHub release, or App Store submission always requires
separate user authorization.

## 0.1.0 — reproducible Mac baseline

Status: **release_candidate**

The intended 0.1.0 capability baseline is implemented and has been exercised
on three already-configured Macs, but release engineering and clean-machine
acceptance gates remain open. It must not be described as released, tagged,
packaged, or publicly distributed.

The 0.1.0 baseline includes:

- persistent Core/Option component catalog with delivery-source, dependency,
  account, permission, capacity, and verification metadata;
- read-only application inventory, capacity-aware planning, controlled
  Homebrew installation, source-mismatch reporting, and post-install checks;
- repository-local `macomrade` CLI routing scan, plan, apply, verify, drift,
  diagnostics, and migration while retaining script compatibility;
- Draft 2020-12 JSON contracts for catalog, settings, Private overlay, plan,
  state, and diagnostics, with validation-before-use and reversible v0/v1
  migration tooling;
- allowlisted redacted diagnostic ZIPs with bounded logs, failure classes,
  public policy hashes, preview manifests, and verified guarded export;
- tracked desired policy separated from ignored per-machine observations;
- reusable macOS permission requirements plus read-only application, TCC,
  helper, service, extension, and background-task inventory;
- allowlisted system preference capture, comparison, and explicitly approved
  application for supported preferences;
- Dock order, startup items, fonts, printers, keyboard/HID, Chrome profile,
  DNS/SmartDNS/VPN, developer environment, and operational-baseline workflows;
- shared Python Core, Android developer environment, shell environment, and
  Homebrew dependency-upgrade policy;
- App Store, official website, WebCatalog, PlayCover, GUI/CLI, account, and
  privileged-installer deployment rules;
- app-specific inspection or cleanup workflows for Capacities, Claude VM,
  Docker Desktop, OpenClaw, duplicate bundles, and shared Group Containers;
- disaster recovery, backup preconditions, and continuous multi-Mac sync
  references;
- documentation-only browser-bookmark migration and SSH/GPG provisioning
  guidance, plus the iCloud-versus-repository boundary;
- frontmatter, app-catalog, bootstrap, and final drift validation.
- repeatable machine-local resource benchmarks, localized accessible audit
  reports, and a low-noise read-only drift monitor with opt-in scheduling.

The release-candidate artifact map is:

| Capability | Primary artifacts |
| --- | --- |
| App inventory, plan, install | `references/mac-app-catalog.json`, `components/`, `scripts/macos_apps.py` |
| Unified CLI | `bin/macomrade`, `scripts/macomrade.py`, `references/macomrade-cli.md`, `references/cli-identity.json` |
| JSON contracts and migration | `schemas/`, `references/schema-registry.json`, `scripts/schema_contract.py`, `references/schema-and-migration.md` |
| Redacted diagnostics | `scripts/diagnostic_bundle.py`, `schemas/diagnostic-bundle-v1.schema.json`, `references/redacted-diagnostic-bundle.md` |
| Bootstrap and drift | `scripts/bootstrap_macos.py`, `scripts/bootstrap_validate.py`, `scripts/bootstrap_verify.py` |
| Performance, reporting, and monitor | `scripts/performance_benchmark.py`, `scripts/audit_report.py`, `scripts/drift_monitor.py` |
| iCloud-backed Git integrity | `scripts/icloud_git_guard.py`, `references/icloud-git-integrity.md`, `tests/test_icloud_git_guard.py` |
| Machine-local runtime state | `scripts/state_paths.py`, `scripts/migrate_state.py`, `state/locator.json`, `references/machine-local-state.md` |
| Permissions | `settings/privacy.yaml`, `scripts/macos_permissions.py`, `scripts/macos_permissions_cleanup.py` |
| Preferences and workstyle | `settings/`, `scripts/macos_preferences.py` |
| Dock, startup, Chrome, keyboard | `scripts/macos_dock.py`, `scripts/macos_startup_items.py`, `scripts/chrome_profiles.py`, `scripts/keyboard-config-logi-k240.swift` |
| Cleanup workflows | `scripts/capacities_cleanup.py`, `scripts/claude_vm_cleanup.py`, `scripts/docker_desktop_cleanup.py`, `scripts/openclaw_cleanup.py`, `scripts/scan_group_containers.py` |
| Portability and recovery guidance | `references/disaster-recovery-runbook.md`, `references/multi-mac-continuous-sync.md`, `references/browser-bookmark-migration.md`, `references/ssh-gpg-provisioning.md` |
| Integrity audits | `scripts/audit_component_frontmatter.py`, `scripts/audit_core_catalog.py`, `scripts/validate_app_catalog.py` |
| Clean-Mac release acceptance | `references/clean-mac-acceptance.json`, `references/clean-mac-acceptance-status.json`, `scripts/clean_mac_acceptance.py` |

The canonical current behavior classification is the machine-validated
[`release-acceptance-matrix.json`](release-acceptance-matrix.json). It is a
cumulative contract bound to the current `VERSION`: `supported` rows require
existing evidence; `interface_limited`, `deferred`, and `excluded` rows define
boundaries that must not be represented as supported. Run
`python3 scripts/validate_release_contract.py` to verify the matrix, current
version, and matching roadmap status together. This 0.1.0 section remains the
historical baseline description after later version bumps.

The accepted release backlog is tracked under
[`TODO.md`](../TODO.md#010-release-candidate-work). P0 tasks block a validated
release candidate, P1 tasks block changing this status to `shipped`, and P2
tasks are accepted 0.1.x enhancements that do not block 0.1.0. The repository
will remain in iCloud Drive; iCloud-aware integrity protection is therefore a
release requirement rather than repository relocation. A genuine Clean-Mac
acceptance run remains a P1 gate and is externally deferred until suitable
unused hardware is available.

## 0.1.1 — public source release readiness

Status: **release_candidate**

Implementation status: **ST-01 through ST-10 completed and locally accepted on
2026-08-14.** This marks the capability implementation as a release candidate,
not a version change or release at that checkpoint. It did not authorize a
commit, tag, push, GitHub Release, packaged CLI, or publication action.

Execution: **all ten public-source gates completed on 2026-08-14**. The
existing GitHub repository is public at candidate commit `f490fe4`; anonymous
page, HTTPS Git, API metadata, privacy, and 23-stage release-gate read-backs
passed. No tag or GitHub Release was created by that transaction.

Prepare this repository for safe public discovery and reuse without exposing
the author's personal cross-Mac configuration. This is a patch release because
it packages, documents, and governs the existing 0.1 capability domain rather
than adding a new product domain.

The public repository will contain the reusable engine, policy, schemas,
sanitized fixtures, component guides, and example configuration. Current
personal files remain in the same iCloud Drive project under Git-ignored
`Private/`; no second repository is introduced. Removing them from the current
Git index is not sufficient: reachable Git history must be audited and safely
rewritten before publication.

0.1.1 includes ten publication gates covering tracked/history privacy,
iCloud Private isolation, sanitized examples, open-source governance,
onboarding, safety, RC-15 release provenance, independent public-clone
rehearsal, and a separately authorized visibility transaction with anonymous
read-back. The complete contract is
[`public-release-readiness.md`](public-release-readiness.md).

This scope did not change repository visibility, `VERSION`, release tag, or the
local-validation policy by itself. Public GitHub visibility was applied later
as the final explicitly authorized transaction after all gates passed.

## 0.2.0 — memory-backed storage management

Status: **shipped**

Release status: **ST-01 through ST-12 completed, locally accepted, committed,
and published on 2026-08-14.** `VERSION` is 0.2.0. The public source release is
the annotated `v0.2.0` tag resolving to commit `97b4118`. No GitHub Release,
packaged distribution, or completed genuine Clean-Mac acceptance run exists.

Build an independent stateful, policy-driven storage decision layer above
Mole. Mole remains an optional interactive explorer and read-only historical
evidence source; macomrade owns classification, physical-allocation evidence,
planning, transaction safety, measurement, and verification.
The existing 0.1.0 Mole whitelist is a static protection policy only. The
stateful decision ledger, independent physical-size accounting, repeat-review
suppression, and measured cleanup history begin in 0.2.0.

### Storage model

Represent every candidate with:

- logical bytes, allocated bytes, purgeable/reclaimable estimate, and measured
  bytes reclaimed;
- local, cloud-only, hybrid, clone, compressed, sparse, hard-linked, or unknown
  storage state;
- owner application/project/account and last meaningful access/change;
- short-term or long-term retention horizon;
- desired action: `keep_local`, `cloud_on_demand`, `archive`, `review_after`,
  `safe_cache`, `delete_after_backup`, `protected`, or `unknown`;
- confidence, evidence, risk, rollback, and required confirmation.

Never use Mole's displayed logical size as the expected reclaimed space.
In particular, detect iCloud/File Provider placeholders using allocation blocks
and filesystem flags such as `dataless`; distinguish **Remove Download** from
deleting an iCloud item.

### Memory model

- Store reusable public rules in tracked `settings/storage-policy.json` and
  personal intent/targets in Git-ignored `Private/storage-policy.json`.
- Store scans, temporary decisions, observed paths, actual sizes, access times,
  and cleanup outcomes in machine-local `storage-*.json` records.
- Remember a decision with an expiry/review date so the same unchanged item is
  not repeatedly presented.
- Promote a local decision into synced policy only after explicit review.
- Never sync private filenames, document contents, cloud tokens, or credentials
  merely to provide memory.

### Planned workflow

Provide these deterministic stable commands:

```text
macomrade scan storage
macomrade review storage
macomrade plan storage
macomrade apply storage
macomrade verify storage
macomrade history storage
```

The first implementation must:

1. import Mole's supported JSON history without trusting its size value as
   physical usage or inferring a decision;
2. calculate logical and allocated bytes independently;
3. classify iCloud placeholders and protected model/project paths;
4. suppress unchanged, previously decided candidates until their review date;
5. preview exact actions and expected reclaimable bytes;
6. execute only one frozen action class per command with its exact typed
   confirmation;
7. remeasure the filesystem and record actual reclaimed bytes;
8. support rollback when the underlying operation is reversible.

### 0.2.0 acceptance gates

- The two validated iCloud folders under `~/Desktop/RUN_1stWorld` are reported
  as multi-gigabyte logical content but approximately megabyte-scale allocated
  content, and are not recommended as local-space deletion targets.
- Protected paths, including Hugging Face model assets, remain excluded.
- Re-running an unchanged scan does not ask the same resolved questions.
- Every reported saving distinguishes estimate from measured result.
- No automatic deletion occurs in scan, review, or plan mode.
- `compact` stops at 50 GiB free, `expanded` at 100 GiB, and every transaction
  stops early and replans when the actual target is reached.
- The Foundation helper is source-controlled but compiled only into
  machine-local state; only iCloud local-copy eviction is automated in 0.2.0.
- Trash staging remains distinct from measured reclaim, and permanent purge
  can touch only unchanged items bound to the same frozen manifest.
- Quick and deep scans surface read-only APFS/snapshot/VM, bounded Home,
  protected-system, exact temporary-directory, and optional-App evidence
  without converting OS or App ownership into generic deletion authority.
- Operators can request either a role target, an absolute free-space floor, or
  an explicit additional amount such as `+10GiB`; the frozen plan records the
  original target and mode.

The executable contract and operator procedure live in
[`storage-lifecycle.md`](storage-lifecycle.md). The storage tests, performance
budgets, live sample checks, and release gates passed before the separately
authorized version change to 0.2.0.

## 0.3.0 — browser bookmarks and reading lists

Status: **release_candidate**（Safari-only scope; Chrome deferred by user choice）

Release status: the Safari-only slice of the committed 0.3.0 scope is implemented
and locally validated. `references/browser-acceptance.json` records the
Safari-only live-acceptance contract with BA-01 through BA-05 passed on a real
Safari 27 export, BA-08 marked `interface_limited` (no supported Safari item
write/rollback API), and BA-10 deferred by user choice. Chrome remains
`deferred_by_user`; the 45-day gateway trial lifecycle (started 2026-08-14)
and post-change second-export evidence remain open. No tag, GitHub Release,
packaged distribution, or genuine clean-Mac acceptance run exists.

Implementation progress: the Safari-only slices of BR-01 and BR-03 plus all of
BR-02, BR-04, and BR-05 are complete. BR-02 registers the private browser-item Schema, opaque identity,
profile/account and collection boundaries, lifecycle/conflict fields, and
fail-closed Git/privacy combinations. BR-03 now parses only an explicitly
supplied Bookmarks-and-Reading-List-only Safari ZIP into schema-checked private in-memory items
and emits a redacted count-only summary. Live reads now prefer the public
`mpia >= 0.9.3` Safari adapter (renamed from `macos-data-cli`), while an
explicit Bookmarks-and-Reading-List-only Safari export remains the immutable
evidence, recovery, reconciliation, and acceptance source. The skill never
accesses the internal bookmark plist directly. `mpia 0.9.3` supplies the
guarded local-only bookmark/folder CRUD contract, but it has not proved
cross-device sync and is not yet bridged to frozen export plans. Selection is
gated on three independent checks — routes, Full Disk Access for the new
`com.xvk.mpia.cli` identity, and the adapter's ability to parse this Mac's
`Bookmarks.plist` — and any failing gate keeps the export path live. Chrome source
verification remains deferred by
user choice; BR-01 as a whole remains open. BR-04 adds authority-backed,
structure-preserving URL proposals and explainable duplicate groups that never
cross browser/profile/account identity or grant execution authority.
BR-05 adds public taxonomy and review-period policy plus a Private decision
ledger. Only a unique, unchanged semantic fingerprint inside the same identity
boundary is suppressed until its review date; personal labels, notes, and
fingerprints never enter Git.
BR-06 now has a safe partial foundation: a verified Safari export can bind a
self-hashed item-scoped plan, an exact-confirmed transaction can freeze it to
mode-0600 machine-local state, and a later explicit export can verify expected
fingerprint counts. Safari live apply remains unsupported because the current
official interfaces cannot enumerate and transactionally mutate existing
items; HTML import is additive rather than exact rollback. BR-06 therefore
remains open.
BR-07 exposes scan, capability selection, review, plan, apply, verify, and history through stable
`macomrade ... browser` routes. Their JSON remains authoritative and redacted;
the shared renderer accepts only fixed summary kinds and aggregate fields for
zh-Hans, ja, and en terminal or semantic static HTML output. Raw parses and
frozen plans are rejected. The apply route preserves the BR-06 fail-closed
interface blocker and grants no Safari write authority.
BR-08 now has a ten-gate Safari-only acceptance harness for explicit exports,
repeat-run inventory/review/decision/plan evidence, shared-profile identity,
optional second-export verification, and redacted Schema-validated output.
One real Safari 27 export passed BA-01 through BA-05 with 311 bookmarks and 89
Reading List items. Its five duplicate groups can be exported for human review
only through an exact-confirmed, schema-validated, mode-0600 artifact under
Git-ignored `Private/browser/`; stdout remains aggregate-only and the artifact
grants no execution authority. BR-08 and full 0.3.0 remain blocked by missing
reviewed decision/operation/post-export evidence, the Safari live-write and
rollback interface, and the user-deferred Chrome scope.

BR-10 adds the product-level information-flow objective above the existing
organization ledger: Safari is a bounded recurring-source gateway, Reading
List is a temporary inbox, and Obsidian owns durable knowledge. A registered
public policy allocates 70 Core and 30 trial slots across the existing 15
subdomains, targets about 100 active sources within a 90–110 operating range,
uses a 45-day trial, two-out/one-in while above 100, then one-in-one-out
renewal, and requires recent
source evidence. A read-only macomrade audit reports aggregate capacity,
retirement pressure, and room for new sources without revealing Private
content or changing Safari. Candidate discovery, per-item replacement review,
trial promotion, and supported live mutation remain incomplete. The first
approved wave is now preserved as a source-bound Private ledger with ten new
sources, twenty retirement decisions, projected active count 272, mode `0600`,
Git-ignore and Schema read-back; its migration plan remains explicitly blocked.

The capacity contract treats 100 as the admission boundary rather than the
upper operating bound: above 100, every new source requires at least two
reviewed retirements. A 90–110 range absorbs normal review timing, but 110 is
not an expansion target. The existing 282-item baseline requires 196 retirement
reviews and allows only 14 quota-filling additions; after the recorded Wave 1,
the corresponding remainder is 185 retirements and at most 13 additions.

The first manual execution pilot now has a registered Private contract and
stable CLI freeze/verification routes. It supersedes the immutable Wave 1
without modifying it, freezes ten exchange groups and a 16-item temporary
removal manifest, and verifies explicit source/baseline/checkpoint exports at
316, 321 and 305 bookmarks while requiring all 89 Reading List items and 291
non-manifest old bookmarks to remain unchanged. The implementation grants no
Safari or purge authority. Evidence import, pilot freeze, both manual batches,
the separately confirmed manifest-only purge, and 45-day trial results remain
live acceptance work.

The convergence layer now compiles the old organization, immutable pilot and
reviewed current-source spec into a bounded 90–110-source, 15-subdomain Private
ledger. Its deterministic HTML generator excludes Reading List and archive
content and verifies every URL, title and folder by read-back. The real-data
candidate currently resolves to 99 items: 73 retained legacy sources and 26
trials. Neither
the ledger nor the package has been persisted yet, and clearing/importing
Safari remains a separate destructive live-acceptance step.

Create a privacy-preserving information architecture and repeatable review
workflow for bookmarks and read-later items across Safari, Chrome, and their
separate profiles. Define item identity, canonical URL and title, duplicate and
tracking-parameter normalization, folder/tag taxonomy, inbox/project/reference
classification, stale-link review, archive/delete boundaries, profile/account
ownership, exports, and conflict handling before implementing writes.

The system should remember reviewed decisions so unchanged links are not
repeatedly presented. Portable rules may be tracked, but account identifiers,
private URLs, exported collections, and per-profile observations belong in the
Git-ignored Private layer or machine-local state according to their content.
Obsidian or another durable knowledge source may receive an explicitly
promoted item; browser collections are not silently treated as canonical
knowledge.

Do not ingest cookies, history, tokens, or private URLs by default. Prefer
browser-native sync and export APIs; require a redacted preview before any
merge, move, archive, or deletion.

This is distinct from the 0.1.0 documentation-only migration reference:
0.3.0 introduces reviewed classification and lifecycle behavior.

### 0.3.0 acceptance gates

- Inventory keeps browser, profile, account, and collection boundaries visible.
- URL normalization can identify duplicates without discarding meaningful
  query parameters or merging private and public identities.
- Every move, merge, archive, or delete plan has a restorable export and exact
  preview; scan and classification modes make no browser changes.
- Re-running an unchanged inventory suppresses already reviewed decisions
  until their configured review date.
- Post-apply verification reads the browser-visible result and reports any
  item that could not be reconciled.

## 0.4.0 — notes lifecycle

Status: **committed; rules to be designed**

Define canonical note ownership, inbox-to-knowledge flow, duplicate and
near-duplicate handling, attachment ownership, archive policy, backlinks,
metadata, retention, private-note boundaries, and cross-tool migration.
Preserve Obsidian/Markdown as the canonical durable source where applicable.
Do not reorganize or rewrite notes before the user approves the taxonomy and
conflict rules.

## 0.5.0 — SSH key lifecycle

Status: **committed; rules to be designed**

Inventory SSH identity metadata without reading or persisting private-key
content. Design host-to-key mapping, owner/purpose, creation and expiry,
rotation, revocation, backup/recovery evidence, file permission checks,
ssh-agent/Keychain behavior, duplicate-key detection, and remote verification.

Never commit private keys, passphrases, tokens, decrypted secret material, or
machine-specific secret paths. Prefer a new device-specific key over copying a
default private key when the remote service supports multiple keys.

## 0.6.0 — application-specific storage adapters

Status: **committed**

Add adapters for applications whose storage cannot be safely handled as a
generic cache. Each adapter declares ownership, databases, attachments,
downloaded media, cloud synchronization, retention, supported internal cleanup,
safe external cleanup, account impact, rollback, and verification.

This builds on the metadata-only 0.1.x Adapter SDK reference. 0.6.0 adds the
productized, application-aware storage policies, review flows, and measured
cleanup management that remain deliberately out of the current generic SDK.

WeChat is the priority adapter. It must distinguish message databases,
attachments, downloaded media, thumbnails, logs, mini-program data, and caches;
prefer WeChat's supported cleanup where available; never delete message history
or unsynchronized media based only on size.

## 0.7.0 — photo review and cleanup

Status: **committed; interaction rules to be designed**

Build a fast human-in-the-loop review workflow for old photos, screenshots,
duplicates, bursts, low-quality captures, and large videos. Use visual batches,
date/event/location grouping, favorites and album protection, iCloud Photos
state, Recently Deleted behavior, and measured local-space impact.

No model may permanently delete photos without a visible selection and final
confirmation. The design must account for iCloud deletions propagating to all
devices and distinguish Optimize Storage from deleting library assets.

## 0.8.0 — WeChat group lifecycle

Status: **committed; rules to be designed**

Create a private, local-first control plane for organizing WeChat groups by
purpose and lifecycle. The product should help classify groups such as work,
project, customer, family, community, information feed, temporary event, and
archive; record the user's role and intent; review pin and notification state;
identify inactive or duplicate-purpose groups; and maintain an actionable
queue for keep, mute, unpin, rename/remark, archive-reference, or leave.

This is not the 0.6.0 WeChat storage adapter. Version 0.6.0 manages local disk
usage owned by WeChat; 0.8.0 manages the user's communication topology and
attention. The two may share the App Adapter SDK and identity model, but their
plans, permissions, evidence, and confirmations remain separate.

Use supported WeChat interfaces, user-approved exports, or visible GUI
automation. Do not decrypt or patch WeChat databases, bypass application
security, ingest message bodies by default, send messages, or infer sensitive
relationships from content. Group names, member lists, account identifiers,
message-derived summaries, and activity snapshots are private data and must
not enter the public repository.

Leaving or dissolving a group, removing or inviting a member, deleting local
history, renaming a shared group, or changing a setting visible to other
members is never automatic. Each such action requires an exact preview,
separate confirmation, and visible read-back. The first release may remain a
read-only inventory and decision queue when WeChat exposes no reliable,
supported write interface.

### 0.8.0 acceptance gates

- A read-only inventory can associate each reviewed group with purpose,
  ownership/role, attention policy, retention intent, confidence, and next
  review date without storing message bodies in tracked files.
- Generic taxonomy and safety policy are portable; account and group identity
  mappings remain in the Git-ignored Private layer, while observations remain
  machine-local.
- The decision queue distinguishes private local annotations from actions that
  change shared WeChat state and explains who may observe each proposed action.
- Scan and plan modes send no messages and change no memberships, names,
  notifications, pins, or history.
- Every supported write is item-scoped, explicitly confirmed, read back from
  WeChat, and recorded without retaining sensitive payload content.
- Unsupported actions produce a manual handoff instead of database mutation or
  a false success result.

## 0.9.0 — iPhone intelligence and Home Screen lifecycle

Status: **committed; interface and organization rules to be designed**

Use Apple's iPhone Mirroring capability as a visible, user-controlled bridge
for collecting necessary iPhone operational intelligence and organizing the
iPhone Home Screen from a Mac. The product should help inventory user-approved
device and software state; understand the current placement of apps, pages,
folders, Dock items, widgets, and mirrored-notification policy; propose a
purpose-based taxonomy; and carry out reviewed moves and folder changes with
before-and-after visual verification.

The initial taxonomy should support work, communication, finance, travel,
media, creation, utilities, health, smart home, development/testing, occasional
use, and user-defined groups. It must distinguish app installation from Home
Screen placement: an app absent from a page may still exist in App Library,
and removing an icon is not the same as deleting the app. The desired layout
may vary by iPhone role and Focus mode rather than forcing one universal grid.

Treat iPhone Mirroring as a GUI interaction surface, not a device-management
API or unrestricted data source. Supported setup currently requires compatible
devices, the same Apple Account, nearby Wi-Fi and Bluetooth, a locked iPhone,
and regional availability. Pairing, device passcode, Apple Account prompts,
Trust This Computer, purchases, and other security confirmations remain visible
user handoffs. Camera and microphone workflows are outside the mirroring
surface. When the feature or an operation is unavailable, report a precise
manual iPhone step instead of using private frameworks, backups, jailbreaks,
database extraction, or accessibility bypasses.

Collect only allowlisted visible metadata needed for the approved workflow,
such as device role, OS/update readiness, storage summary, installed app name,
Home Screen location, folder label, Dock/widget placement, and notification
policy. Raw screenshots, OCR output, device identifiers, app/account mappings,
and layout observations are Private, transient, or machine-local according to
their sensitivity; none belongs in the public repository. Passwords, passcodes,
tokens, messages, photos, health records, financial content, browser sessions,
and private in-app payloads are prohibited collection targets.

Every layout mutation follows the repository transaction contract. Scan and
proposal modes make no iPhone changes. Before moving icons, creating or
renaming folders, changing pages, widgets, Dock items, Focus-linked pages, or
notification settings, preserve a visual/layout restore map, preview the exact
batch, and obtain explicit confirmation. Apply only small visible batches,
stop when the mirrored UI differs from the plan, and read back the final layout.
App deletion, offloading, installation, purchase, account changes, and content
mutation are separate actions and are never implied by screen organization.

### 0.9.0 acceptance gates

- A capability preflight verifies device/OS compatibility, selected iPhone,
  same-account continuity, proximity, connectivity, regional availability,
  authentication mode, and notification-mirroring policy without retaining a
  passcode or Apple Account secret.
- A read-only inventory can represent visible apps, App Library versus Home
  Screen presence, pages, folders, Dock items, widgets, and approved operational
  summaries while keeping screenshots and personal mappings out of Git.
- The proposed layout explains every grouping and distinguishes move, hide,
  remove-from-Home-Screen, offload, and delete; only move/folder/layout actions
  belong to the default 0.9.0 apply path.
- Scan, OCR, classification, and plan modes perform no taps, drags, settings
  changes, installs, removals, notification changes, or account actions.
- Each supported mutation has a pre-change restore map, item- or batch-scoped
  confirmation, visible execution through iPhone Mirroring, and visual
  read-back; interruption produces a reconciliation queue rather than retries.
- Private app contents are never opened merely to classify an icon. Unsupported
  or security-sensitive steps produce an exact manual handoff on the iPhone.
- Re-running an unchanged inventory preserves accepted group decisions and
  proposes no duplicate moves; verified restore can reconstruct the prior Home
  Screen organization within the limits of Apple's visible interface.

## 1.0.0 — native macOS product

Status: **committed**

Release one native macOS GUI application, preferably Swift/SwiftUI, that
integrates the proven 0.x workflows into a coherent product:

- dashboard for actual local storage, cloud placeholders, protected data, and
  reclaimable space;
- explainable recommendations backed by short-term observations and long-term
  user decisions;
- review queues for storage, browser knowledge, notes, SSH metadata,
  application adapters, WeChat groups, photos, and iPhone operational/layout
  management;
- preview, confirmation, progress, rollback, and measured-result views;
- local-first operation with no credential collection and no destructive
  default;
- accessible, localized, signed, notarized release with a documented privacy
  model.

Mac App Store submission is a release option, not an assumed compatibility
fact. Before 1.0, choose and validate one distribution architecture:

- **Mac App Store sandbox** — safer distribution, but broad disk scans,
  Homebrew control, LaunchDaemon management, and arbitrary filesystem cleanup
  require user-selected security-scoped access or may be unavailable.
- **Developer ID outside the Store** — supports deeper system management but
  requires notarization, stronger trust communication, update infrastructure,
  and careful privilege separation.
- **Hybrid** — App Store-safe viewer/policy app plus a separately installed,
  explicitly authorized local helper; validate this against App Store policy
  before committing to it.
