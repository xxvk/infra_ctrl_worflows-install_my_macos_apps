# Safari bookmark and Reading List sources

## Scope and decision

This is the Safari-only completion slice of BR-01. Chrome remains deferred.
The preferred live item-reading source is the public `macos-data` Safari CLI
contract introduced in 0.8.0. It provides bounded bookmark and Reading List
list/query/get commands, opaque IDs, pagination, and stale-cursor rejection.
The skill consumes that adapter rather than opening Safari's private plist.

A Safari export that the user deliberately creates through **File → Export
Browsing Data to File…** with only **Bookmarks** and **Reading List** selected
remains the immutable evidence and recovery source. Use it for hash-bound
planning, preservation, reconciliation, package generation, and post-change
acceptance—not as the default way to answer every live read question.

The export is an unencrypted private artifact. It must never enter Git, a
diagnostic bundle, a public fixture, or a general log. The BR-03 Safari adapter
reads only an explicitly supplied export from a private or machine-local path,
produces a redacted count-only preview, and retains no item content by default.

The machine-readable source classification is
[`browser-data-sources.json`](browser-data-sources.json). Validate it with:

```sh
python3 scripts/browser_sources.py validate
python3 scripts/browser_sources.py inspect-safari
MACOS_DATA_CLI=/path/to/macos-data python3 scripts/browser_sources.py inspect-safari
python3 scripts/safari_export.py inspect /private/path/to/Safari\ Export.zip
python3 scripts/browser_review.py inspect-safari-export /private/path/to/Safari\ Export.zip
python3 scripts/browser_lifecycle.py review-safari-export /private/path/to/Safari\ Export.zip \
  --ledger Private/browser/decision-ledger.json --as-of 2026-08-14
```

The live inspection reads Safari's version and scripting dictionary plus file
presence/readability metadata, then probes only `macos-data --version` and
`macos-data --help`. It never opens the bookmark plist or emits a URL,
title, folder name, profile name, or Apple Account identifier.

## Execution priority

Use these routes in order according to intent:

1. **Live read/query:** `macos-data >= 0.8.0` via PATH or
   `MACOS_DATA_CLI`; fall back to an explicit export only when the adapter is
   unavailable or an immutable snapshot is required.
2. **Immutable evidence and exact verification:** explicit Safari export ZIP.
3. **Cross-device desired-state write:** deterministic HTML package imported
   by Safari so Safari owns the resulting sync transaction.
4. **Local-only write:** public `macos-data >= 0.8.1` is preferred over GUI row
   operations when capability probing confirms bookmark/folder CRUD and the
   user explicitly selects local-only scope.
5. **GUI/Computer Use:** last-mile Safari-owned import/export or a bounded
   fallback, never the default per-item execution engine.

The 0.8.1 public CLI implements atomic local plist mutation with Safari exited,
handle checks, private recovery, rollback, and local UI/CLI read-back. It has
not demonstrated iCloud propagation to a second device. Therefore local write
and synchronized write remain separate capabilities.

## Supported export contract

Apple documents the current Safari browsing-data export as a ZIP archive. Its
bookmark member uses the Netscape Bookmarks HTML format. Reading List entries
are represented inside that bookmark file as the subfolder whose identifier is
`com.apple.ReadingList`.

Bookmarks and Reading List are shared rather than separately exported per
Safari profile. History and extension files may be profile-specific, but they
are outside this workflow. Safari 27 presents **Bookmarks** and **Reading List**
as separate switches. The operator must select both and deselect history,
passwords, payment cards, and extensions. Apple documents Reading List through
the `com.apple.ReadingList` folder identifier. A live Safari 27 beta export may
place that folder in a separate `ReadingList.html` member rather than the same
member as bookmarks, so the adapter accepts both documented/legacy and observed
Safari 27 layouts.

The supported flow is therefore:

```text
user opens Safari export sheet
→ user selects Bookmarks and Reading List only
→ user chooses a private destination
→ parser validates ZIP/member/format without importing it
→ parser separates normal bookmarks from com.apple.ReadingList
→ raw URLs and titles stay private or machine-local
```

## BR-03 read-only parser contract

[`safari_export.py`](../scripts/safari_export.py) accepts one explicit ZIP
path. It never discovers or opens `~/Library/Safari/Bookmarks.plist`, never
starts Safari, never follows links, never fetches a bookmark URL, and never
writes parsed content. Its CLI emits only bookmark and Reading List counts plus
privacy/authority booleans.

After ignoring directory entries and AppleDouble metadata under `__MACOSX` or
`._*`, the ZIP must contain either one Netscape HTML member carrying both
collections, or two Netscape HTML members with exactly one bookmarks document
and one `com.apple.ReadingList` document. No other semantic file is allowed.
This deliberately enforces the **Bookmarks and Reading List only** selection:
password CSV, history/extension/payment-card JSON, or any unrelated member
causes a fail-closed result. The reader also rejects encrypted members,
symbolic links, absolute/traversal paths, excessive member counts or sizes,
unsafe compression ratios, non-UTF-8 HTML, and missing Netscape signature. It
reads the HTML member in memory and never extracts the archive.

Apple documents that Reading List is a subfolder identified by
`com.apple.ReadingList`, not a localized display name or one specific HTML
attribute. The parser therefore recognizes the exact identifier in any folder
attribute value (including `ID` or `IDENTIFIER`) or as the folder text. It does
not classify a translated folder name such as “Reading List” by name alone.

### Safari 27 beta archive verification

A user-mediated Safari 27 export on build `22625.1.29.11.2` contained a wrapper
directory, `Bookmarks.html`, `ReadingList.html`, and Finder-created AppleDouble
metadata under `__MACOSX`. Both semantic members used the Netscape format; the
Reading List member retained `com.apple.ReadingList`. The raw private artifact
and item content were not persisted or copied into Git. This live shape is now
covered by fictional fixtures and remains fail-closed for any unrelated member.

Until a supported Safari-native item identifier exists, parsed IDs are derived
from the private export fingerprint and source ordinal—not from a URL—and are
marked `source_position_fallback` / `unstable`. Re-parsing the unchanged ZIP is
repeatable; a changed export may produce new IDs and must be reconciled later
by the reviewed BR-04 duplicate workflow. Canonical URL remains unevaluated in
the parser. The separate BR-04 review can produce private, non-authorizing
canonical and duplicate proposals under the
[tracked normalization policy](browser-url-normalization.md); its CLI still
emits counts only.

Apple's current beta documentation describes
`SFSafariSettings.openExportBrowsingDataSettings`, but documentation, selected
SDK, and runtime can temporarily disagree during a beta cycle. The enclosing
`SFSafariSettings` type existing is not proof that this method exists. A future
native adapter must pass all three gates before adopting it:

1. the exact method declaration exists in the selected SDK headers;
2. a minimal fixture referencing the exact method compiles with that SDK;
3. the foreground application opens the sheet successfully on the target
   runtime and handles the completion error.

Inspect the selected SDK rather than a hard-coded Xcode path:

```sh
SDK_PATH="$(xcrun --sdk macosx --show-sdk-path)"
rg -n "SFSafariSettings|openExportBrowsingDataSettings" \
  "$SDK_PATH/System/Library/Frameworks/SafariServices.framework/Headers"
```

When the method is present, the native adapter must availability-gate it and
compile the exact call, for example:

```swift
import SafariServices

@available(macOS 27.0, *)
func openSafariExportSheet() {
    SFSafariSettings.openExportBrowsingDataSettings { error in
        // Report only pass/fail; never log exported browsing data.
    }
}
```

Sandboxed checks should use a writable module cache, such as
`xcrun swift -module-cache-path /tmp/macomrade-swift-module-cache ...`. If the
method is absent or fails to compile, the supported fallback remains **Safari
→ File → Export Browsing Data to File…**. The user still selects **Bookmarks
and Reading List only** and chooses the private destination; opening the sheet never authorizes
selection or export on the user's behalf.

### Xcode 27 Beta 5 verification

The selected Xcode 27 Beta 5 / macOS 27 SDK contains
`SFSafariSettings.h`, but it declares only
`checkAutoFillUserNamesAndPasswordsEnabledWithCompletionHandler:`. That method
reports the Safari AutoFill toggle to an eligible process; it neither opens an
export nor reads bookmarks or Reading List items. A direct command-line probe
returned `SFSafariSettingsErrorNotAllowed`, so its presence is not treated as a
general-purpose entitlement or a usable browser-data source.

The exact documented export-sheet symbol is absent from the header, and a
minimal Swift reference fails with `type 'SFSafariSettings' has no member
'openExportBrowsingDataSettings'`. This is a beta documentation/SDK mismatch,
not permission failure. Keep the three adoption gates above and retain the
manual export fallback until a later selected SDK and runtime pass them.

On macOS 27 build `26A5406e`, a runtime probe also finds the
`SFSafariSettings` class but reports that it does not respond to
`openExportBrowsingDataSettingsWithCompletionHandler:`. A dynamic invocation
must therefore fail closed too; class presence alone is insufficient.

Safari 27 also adds `/usr/bin/safaridriver --mcp`. Its tool surface covers open
tabs and page debugging—DOM/page content, interactions, console, network, and
screenshots. Apple explicitly states that it has no access to personal Safari
information. It can help test a future browser-facing UI, but it cannot
enumerate bookmarks or Reading List items.

## Interface classification

| Interface | Read items? | BR-01 disposition |
| --- | ---: | --- |
| Safari browsing-data ZIP | Yes, after explicit user export | Supported source; Bookmarks and Reading List only |
| iCloud Safari sync | No public enumeration API | Authoritative sync and bookmark recovery, not an input API |
| Safari AppleScript dictionary | No | Can show Bookmarks UI and add a Reading List item only |
| `SSReadingList` | No | Add/check support only; not enumeration |
| `safaridriver` / Safari MCP | No | Tab/page development automation; Apple says no personal-information access |
| `SFSafariSettings` in Xcode 27 Beta 5 | No | AutoFill toggle check only; documented export-sheet method is absent from selected SDK |
| Safari Web Extension Bookmarks API | Not yet accepted | WebKit work exists, but current shipped/API/permission behavior is not verified; do not select |
| `~/Library/Safari/Bookmarks.plist` | Technically may be readable | Undocumented internal implementation; forbidden as product input |

Full Disk Access can change whether the internal plist is readable. It does not
turn that implementation detail into a supported API. The workflow must never
fall back to the plist when export is unavailable.

## Native sync and recovery

iCloud Safari synchronizes bookmarks, Reading List, tabs, history, profiles,
and selected settings across devices signed into the same Apple Account with
Safari enabled. Bookmark archives can be restored through iCloud.com recovery.
This is the default cross-device continuity mechanism, but it is not evidence
that every expected item is present on a particular Mac; verification remains
visible in Safari or uses an explicit export.

Removing a Reading List item propagates through iCloud, so future write support
must treat deletion as a cross-device mutation. BR-01 introduces no write path.

## Official evidence

- [Importing data exported from Safari](https://developer.apple.com/documentation/safariservices/importing-data-exported-from-safari)
- [Export Safari data to another browser on Mac](https://support.apple.com/guide/safari/export-safari-data-to-another-browser-ibrwebf10132/mac)
- [Keep Safari in sync across devices with iCloud](https://support.apple.com/guide/icloud/what-you-can-do-with-icloud-and-safari-mm9b8da4f328/icloud)
- [Set up iCloud for Safari](https://support.apple.com/guide/icloud/set-up-safari-mm5400ef10c4/icloud)
- [`SSReadingList`](https://developer.apple.com/documentation/safariservices/ssreadinglist)
- [Safari web extensions](https://developer.apple.com/documentation/safariservices/safari-web-extensions)
- [`SFSafariSettings`](https://developer.apple.com/documentation/safariservices/sfsafarisettings)
- [Safari 27 beta release notes](https://developer.apple.com/documentation/safari-release-notes/safari-27-release-notes)
- [Safari MCP server](https://webkit.org/blog/18136/introducing-the-safari-mcp-server-for-web-developers/)

## Deferred work

- BR-01 Chrome source verification remains open by user choice.
- BR-02 defines the private browser-item schema and identity boundary in
  [`browser-item-schema.md`](browser-item-schema.md).
- The Safari-only BR-03 fixture and export parser are complete. Chrome remains
  deferred, so BR-03 as a whole remains open.
- BR-04 URL/duplicate review and BR-05 taxonomy/decision memory are complete as
  read-only engines; neither authorizes browser writes.
- BR-06 can freeze and verify an export-bound private plan, but live Safari
  apply remains blocked. See
  [`browser-transaction-safety.md`](browser-transaction-safety.md) for the
  transaction, recovery, and interface-adoption gates.
- A Safari Web Extension Bookmarks API experiment requires a separately
  reviewed extension, permissions, and current SDK/runtime acceptance. It is
  not a fallback for BR-03.
