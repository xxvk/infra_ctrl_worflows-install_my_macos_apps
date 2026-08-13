# Application Adapter SDK

## Contents

- [Purpose](#purpose)
- [Adapter contract](#adapter-contract)
- [WeChat reference adapter](#wechat-reference-adapter)
- [Claude VM reference adapter](#claude-vm-reference-adapter)
- [Adding an adapter](#adding-an-adapter)
- [Validation](#validation)

## Purpose

An adapter models data lifecycle for an application whose storage cannot be
safely treated as a generic cache. The tracked adapter catalog declares known
root classes, data classifications, capabilities, risk, and allowed handoff
operations. It never stores current paths, file names, account identifiers,
document content, sessions, or measurements.

The SDK has no generic apply command. A destructive action stays with its
existing application-specific transaction owner and exact confirmation token.
This prevents a generic adapter abstraction from silently broadening deletion
authority.

## Adapter contract

Every adapter declares:

- stable adapter and component IDs;
- metadata-only known roots relative to the current home directory;
- data classes with protected, manual_review, official_cleanup_only,
  safe_cache, or unknown disposition;
- inspect, classify, and plan capabilities;
- operations, risk, and whether an operation can be automated;
- a pre-existing mutation action ID and exact confirmation mode when it
  delegates a destructive action.

Inspection reports only root existence and allocated-byte metadata. It never
reads file content, database records, messages, attachments, account state, or
session data. Records are written only to machine-local state.

## WeChat reference adapter

WeChat is the first product reference adapter because its data is valuable,
opaque, often large, and unsafe to delete generically. It inventories only
declared container roots and classifies possible message databases as
protected, attachments as manual_review, and cache-like content as
official_cleanup_only.

The adapter has no deletion path. Its only plan is a high-risk manual handoff:
open WeChat's supported storage-management UI, review the proposal visibly,
and then re-inspect metadata. Never delete message history, attachments,
unsynchronized media, or unknown container data from the filesystem.

## Claude VM reference adapter

The Claude VM adapter inventories the known VM bundle and image sizes through
the existing Claude VM inspector. Its plan delegates only to the existing
registered transactions for removing images or the complete bundle.

The SDK itself does not forward a confirmation or remove a file. The user must
run the existing Claude VM workflow after inspecting processes, plan, backup
implications, and exact target size.

## Adding an adapter

1. Add a schema-valid entry to app-adapters.json.
2. Add complete localized message IDs in all three catalogs.
3. Implement metadata-only inspection before planning any cleanup.
4. Register a separate transaction contract before adding every mutation.
5. Add fixtures for unavailable roots, protected data, manual-only operations,
   interruption, and idempotency where relevant.
6. Update the component guide only for reusable lifecycle knowledge, never for
   current-machine measurements.

## Validation

    python3 scripts/app_adapters.py validate
    ./bin/macomrade diagnostics adapters
    ./bin/macomrade scan adapters --adapter wechat
    ./bin/macomrade plan adapters --adapter claude-vm

All inspect and plan commands are read-only except for writing their bounded
machine-local record. There is intentionally no adapter apply route.
