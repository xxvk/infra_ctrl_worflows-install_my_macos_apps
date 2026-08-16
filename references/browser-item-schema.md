# Browser item schema and privacy boundary

## BR-02 decision

[`browser-item-v1.schema.json`](../schemas/browser-item-v1.schema.json) is the
versioned contract for one bookmark or Reading List item. It defines data
shape only. It does not read Safari, create an inventory, normalize a URL,
authorize a browser change, or make browser data safe to commit.

The only tracked instance is a fictional `.invalid` fixture. A real item is
private browser content even when its URL is publicly reachable.

## Identity and browser boundaries

`item_id` is an opaque persisted identifier beginning with `bri_`. It must not
be a plain SHA-256 or another unkeyed digest of the URL: such values are
guessable and can disclose visited destinations. A future parser may use, in
priority order:

1. a supported browser-native identifier;
2. an opaque identifier persisted with the private collection;
3. a source-position fallback explicitly marked unstable. The Safari BR-03
   parser currently uses this method, based on private export fingerprint plus
   source ordinal rather than URL content.

Canonical URL comparison is duplicate evidence, not primary identity. Items
from different browser profiles or accounts are never silently merged;
`cross_profile_merge_allowed` is fixed to `false`. Safari's exported bookmarks
and Reading List are shared across Safari profiles, so their `profile_scope`
is `shared_across_profiles` and profile/account references remain `null` unless
a future supported source proves a narrower boundary.

## Required item model

Every item carries:

- source browser, source interface, profile scope, optional private profile and
  account references, and an opaque export reference;
- collection kind and folder path;
- original URL plus an optional proposed/confirmed canonical URL;
- title, tags, Reading List read state, intended lifecycle, confidence, and
  decision expiry;
- explicit conflict evidence rather than an unexplained duplicate verdict;
- provenance, storage layer, Git policy, redaction requirement, and
  `execution_authorized: false`.

The item's `intended_lifecycle` is an inventory snapshot and remains compatible
with BR-02. BR-05 stores authoritative reviewed classifications separately in
the Private decision ledger, allowing custom categories without changing the
browser-item v1 enum or rewriting a parsed export.

The BR-03 parser leaves `canonicalization_status` as `not_evaluated`. BR-04 may
privately change it to `proposed` using the named and tested
[`browser-url-normalization-v1`](browser-url-normalization.md) policy. It never
sets `confirmed`: a canonical match is duplicate evidence, not merge authority.

## Storage layers

| Content | Layer | Git |
| --- | --- | --- |
| Schema, enums, privacy rules, fictional fixtures | Public tracked source | Allowed |
| User-approved raw export, URLs, titles, folders, tags, profile/account mapping, reviewed intent | `Private/browser/` in iCloud | Never |
| Exact export path, import time, file fingerprint, counts, parse errors, temporary inventory, apply/verify evidence | machine-local `browser/` state | Never |
| Cookies, passwords, payment cards, tokens, sessions, private keys | Not an input; secrets remain in their owner/Keychain | Never |

Private is a synchronization boundary, not a secret store. The Safari export
is unencrypted. Keep it machine-local when cross-Mac access is unnecessary;
placing it under `Private/browser/` is an explicit user choice, not a parser
default. Raw exports and item records are excluded from diagnostics and public
reports. A public report may contain only redacted counts, opaque IDs generated
for that report, and policy-level status.

## Provenance combinations

The schema fails closed on the three permitted combinations:

- `synthetic_fixture` + `public_fixture` + no private content + Git allowed;
- `private_export` + `private_icloud` + private content + Git forbidden;
- `machine_observation` + `machine_local` + private content + Git forbidden.

No item record grants execution. Scan and review commands may classify
or propose; future move, merge, archive, or delete operations require a frozen
plan, restorable export, exact confirmation, and browser-visible read-back.

## Safari 27 capability boundary

Xcode 27 Beta 5 exposes `SFSafariSettings`, but the selected macOS 27 SDK only
declares the AutoFill user-name/password toggle check. Apple online
documentation also lists
`openExportBrowsingDataSettingsWithCompletionHandler:`, while that exact
symbol is absent from the selected SDK and a minimal Swift reference does not
compile. The manual Safari export remains the supported source.

Safari 27 also adds `/usr/bin/safaridriver --mcp` for web-development and
debugging access to tabs, DOM, network, screenshots, console, and page
interactions. Apple states that it cannot access Safari personal information.
It therefore remains a web-content automation interface, not a bookmark or
Reading List source.

See [Safari source verification](safari-bookmark-reading-list-sources.md) for
the complete interface matrix and official evidence.
