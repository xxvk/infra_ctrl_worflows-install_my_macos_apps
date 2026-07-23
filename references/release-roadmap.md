# Release roadmap

## Contents

- [Product direction](#product-direction)
- [Version policy](#version-policy)
- [0.1.0 — reproducible Mac baseline](#010--reproducible-mac-baseline)
- [0.2.0 — memory-backed storage management](#020--memory-backed-storage-management)
- [0.3.0 — browser bookmarks and reading lists](#030--browser-bookmarks-and-reading-lists)
- [0.4.0 — notes lifecycle](#040--notes-lifecycle)
- [0.5.0 — SSH key lifecycle](#050--ssh-key-lifecycle)
- [0.6.0 — application-specific storage adapters](#060--application-specific-storage-adapters)
- [0.7.0 — photo review and cleanup](#070--photo-review-and-cleanup)
- [0.8.0 — undecided](#080--undecided)
- [0.9.0 — undecided](#090--undecided)
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
2. **Git-tracked private configuration** — user-approved personal identifiers,
   account mappings, names, and preferences that must follow the user across
   Macs. Private means access-controlled/personal, not ignored by Git.
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

The release-candidate artifact map is:

| Capability | Primary artifacts |
| --- | --- |
| App inventory, plan, install | `references/app-catalog.json`, `components/`, `scripts/macos_apps.py` |
| Unified CLI | `bin/macomrade`, `scripts/macomrade.py`, `references/macomrade-cli.md`, `references/cli-identity.json` |
| Bootstrap and drift | `scripts/bootstrap_macos.py`, `scripts/bootstrap_validate.py`, `scripts/bootstrap_verify.py` |
| iCloud-backed Git integrity | `scripts/icloud_git_guard.py`, `references/icloud-git-integrity.md`, `tests/test_icloud_git_guard.py` |
| Machine-local runtime state | `scripts/state_paths.py`, `scripts/migrate_state.py`, `state/locator.json`, `references/machine-local-state.md` |
| Permissions | `settings/privacy.yaml`, `scripts/macos_permissions.py`, `scripts/macos_permissions_cleanup.py` |
| Preferences and workstyle | `settings/`, `scripts/macos_preferences.py` |
| Dock, startup, Chrome, keyboard | `scripts/macos_dock.py`, `scripts/macos_startup_items.py`, `scripts/chrome_profiles.py`, `scripts/keyboard-config-logi-k240.swift` |
| Cleanup workflows | `scripts/capacities_cleanup.py`, `scripts/claude_vm_cleanup.py`, `scripts/docker_desktop_cleanup.py`, `scripts/openclaw_cleanup.py`, `scripts/scan_group_containers.py` |
| Portability and recovery guidance | `references/disaster-recovery-runbook.md`, `references/multi-mac-continuous-sync.md`, `references/browser-bookmark-migration.md`, `references/ssh-gpg-provisioning.md` |
| Integrity audits | `scripts/audit_component_frontmatter.py`, `scripts/audit_core_catalog.py`, `scripts/validate_app_catalog.py` |
| Clean-Mac release acceptance | `references/clean-mac-acceptance.json`, `references/clean-mac-acceptance-status.json`, `scripts/clean_mac_acceptance.py` |

The canonical behavior classification is the machine-validated
[`release-acceptance-matrix.json`](release-acceptance-matrix.json). It is the
only 0.1.0 acceptance matrix: `supported` rows require existing evidence;
`interface_limited`, `deferred`, and `excluded` rows define boundaries that
must not be represented as supported. Run
`python3 scripts/validate_release_contract.py` to verify the matrix, `VERSION`,
and this section's `release_candidate` status together.

The accepted release backlog is tracked under
[`TODO.md`](../TODO.md#010-release-candidate-work). P0 tasks block a validated
release candidate, P1 tasks block changing this status to `shipped`, and P2
tasks are accepted 0.1.x enhancements that do not block 0.1.0. The repository
will remain in iCloud Drive; iCloud-aware integrity protection is therefore a
release requirement rather than repository relocation. A genuine Clean-Mac
acceptance run remains a P1 gate and is externally deferred until suitable
unused hardware is available.

## 0.2.0 — memory-backed storage management

Status: **committed**

Extend Mole CLI with a stateful, policy-driven storage layer. Mole remains the
fast interactive explorer and cleanup executor where appropriate; this skill
adds memory, classification, measurement, safety, and verification.
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

- Store reusable, user-approved rules in a tracked
  `settings/storage-policy.yaml`.
- Store scans, temporary decisions, observed paths, actual sizes, access times,
  and cleanup outcomes in machine-local `storage-*.json` records.
- Remember a decision with an expiry/review date so the same unchanged item is
  not repeatedly presented.
- Promote a local decision into synced policy only after explicit review.
- Never sync private filenames, document contents, cloud tokens, or credentials
  merely to provide memory.

### Planned workflow

Provide one deterministic entry point with subcommands equivalent to:

```text
scan → review → plan → apply → verify → history
```

The first implementation must:

1. ingest or invoke Mole without trusting its size value as physical usage;
2. calculate logical and allocated bytes independently;
3. classify iCloud placeholders and protected model/project paths;
4. suppress unchanged, previously decided candidates until their review date;
5. preview exact actions and expected reclaimable bytes;
6. require item-level confirmation for deletion or cloud offload;
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

## 0.3.0 — browser bookmarks and reading lists

Status: **committed; rules to be designed**

Create a privacy-preserving information architecture for bookmarks and
read-later items across browser profiles. Define identity, duplicate URL
normalization, canonical title, folder/tag taxonomy, stale-link review,
archive/delete boundaries, profile/account ownership, exports, and conflict
handling before implementing writes.

Do not ingest cookies, history, tokens, or private URLs by default. Prefer
browser-native sync and export APIs; require a redacted preview before any
merge, move, archive, or deletion.

This is distinct from the 0.1.0 documentation-only migration reference:
0.3.0 introduces reviewed classification and lifecycle behavior.

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

This is distinct from the individual 0.1.0 cleanup scripts: 0.6.0 defines a
common adapter contract and adds productized, application-aware storage
management.

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

## 0.8.0 — undecided

Status: **undecided**

No product capability is assigned to this version. Candidate directions are
kept in [`product-ideas.md`](product-ideas.md). Assign one only after explicit
user selection and then define its scope, non-goals, safety model, and
acceptance gates here.

## 0.9.0 — undecided

Status: **undecided**

No product capability is assigned to this version. Candidate directions are
kept in [`product-ideas.md`](product-ideas.md). Assign one only after explicit
user selection and then define its scope, non-goals, safety model, and
acceptance gates here.

## 1.0.0 — native macOS product

Status: **committed**

Release one native macOS GUI application, preferably Swift/SwiftUI, that
integrates the proven 0.x workflows into a coherent product:

- dashboard for actual local storage, cloud placeholders, protected data, and
  reclaimable space;
- explainable recommendations backed by short-term observations and long-term
  user decisions;
- review queues for storage, browser knowledge, notes, SSH metadata,
  application adapters, and photos;
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
