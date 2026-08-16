# Configuration layers

## Contract

Keep reproducible configuration in four distinct layers:

1. **Public base** — reusable engine, catalog, scripts, and non-personal policy
   in the existing tracked paths.
2. **iCloud Private overlay** — user-approved identifiers, account/profile
   mappings, names, and preferences under `Private/`. The directory is ignored
   by Git and synchronized by the surrounding iCloud Drive folder; it is
   private configuration, not a secret store.
3. **Machine-local state** — detected versions, paths, permissions, timestamps,
   measurements, and logs under the directory returned by
   `scripts/state_paths.py path`.
4. **Secrets** — passwords, access/refresh tokens, private keys, recovery codes,
   cookies, and session material in Keychain or another user-controlled secret
   store, never Git.

The deterministic merge order is public base followed by the iCloud Private
overlay. Objects merge recursively, scalar values replace their base value,
and arrays replace rather than concatenate. Preserve unknown object fields so
a newer producer does not lose data when an older loader performs a merge.

`Private/manifest.json` is the local registry for overlays. It travels through
iCloud with the rest of `Private/`, never through Git. A public clone without
that directory is valid and uses public defaults; `examples/private/` contains
fictional copyable templates.

Set `MACOMRADE_PUBLIC_ONLY=1` for an explicit public-only app-catalog run even
when a local `Private/` directory exists. This is the public onboarding and
anonymous-clone rehearsal boundary: the base catalog is validated and loaded,
but the Private app-catalog overlay is ignored. It does not delete, rename, or
inspect the overlay.

The application catalog uses `Private/app-catalog-overlay.json`, merged by
stable app name. Public follow-up text may contain `{preferred_account}`;
`scripts/config_layers.py` requires the corresponding Private value and renders
the prompt only after merging.

Dock membership/order and confirmed allowlisted macOS preference values live in
`Private/dock-order.json` and `Private/system-preferences-values.json`.
Historical paths under `settings/` remain public locators so existing commands
continue to resolve the canonical Private files.

Personal keyboard selection, dictation preferences, and device-specific K240
mappings live in `Private/keyboard.yaml` and `Private/keyboards/`. Their
historical `settings/` paths are strict YAML locators. The shared resolver reads
only the three scalar locator fields; it does not claim to be a general YAML
parser. Manifest auditing supports JSON objects and a conservative
secret-bearing-key check for declared YAML files.

Storage uses `settings/storage-policy.json` plus the optional
`Private/storage-policy.json`. Its path rules are the deliberate array-merge
exception: Private rules are evaluated first and public rules remain available
after them, so a personal archive/protection pattern does not erase public
cache regeneration proof. Private target and archive arrays otherwise replace
their public defaults. Neither layer may set execution authorization; exact
paths, sizes, fingerprints, and transaction evidence remain machine-local.

Browser lifecycle work uses the tracked `browser-item` Schema plus the public
`settings/browser-url-normalization.json` policy. Public policy may identify
authority-backed tracking keys and produce review proposals, but it carries no
execution authority. User-approved bookmark/Reading List exports, item records,
and reviewed duplicate decisions may sync under `Private/browser/`. The
optional canonical decision ledger is `Private/browser/decision-ledger.json`;
custom labels, notes, identity references, fingerprints, and review dates are
Private and never tracked. URLs, titles, folder paths, tags, profile or
account mappings, and exports never enter Git. Exact source paths, fingerprints,
counts, parse errors, temporary inventories, frozen plans, and apply/verify
evidence remain under machine-local `browser/` state. A frozen plan may contain
private item IDs, fingerprints, folder paths, and the exact export path; it is
mode `0600`, redacted from CLI output, and never synchronized. No Private browser record carries
execution authorization; only fictional public fixtures may declare themselves
Git-allowed.
The optional duplicate-only human-review artifact also lives below
`Private/browser/`. It is created only by an exact-confirmed command, is bound
to one export hash, uses mode `0600`, and contains no execution authorization.
Its CLI summary remains aggregate-only; it is neither a ledger nor a frozen
Safari mutation plan.
The canonical reviewed two-level taxonomy and all source-item decisions may
live at `Private/browser/organization.json`. It is bound to one source-export
hash, created only after `SYNC PRIVATE BROWSER ORGANIZATION`, mode `0600`, and
never Git-authorized. It can classify and suppress repeated review, but cannot
grant plan-freeze or Safari execution authority.
Declare the canonical file as the optional `browser-organization` entry in
`Private/manifest.json`, so another Mac can discover and validate it after
iCloud synchronization. The source export is separate immutable evidence under
`Private/browser/evidence/`; the organization stores its hash, while the ZIP
stores the original bytes. Neither belongs in the tracked example manifest as
real content—the example carries path metadata only.

## Migration rule

Do not move or delete existing configuration merely because it contains
personal values. Migrate one consumer at a time:

1. Inventory the current source file and every loader.
2. Add an equivalent Private overlay without removing the existing value.
3. Compare the merged result with the current behavior using fixtures.
4. Update the consumer to use the shared loader.
5. Remove a duplicate historical value only after semantic equivalence and
   backward compatibility are verified and the user approves that migration.

Keep the existing `Private/` directory and values in place during migration.
The directory-level `Private/` ignore is mandatory; never add a negation that
causes a real personal file to become tracked. Git history is cleaned as a
separate reviewed transaction and does not delete the iCloud copies.

## Validation

Run:

```sh
python3 scripts/config_layers.py audit
python3 -m unittest tests/test_config_layers.py
```

The audit rejects paths outside the iCloud project directory and common
secret-bearing key names. This is a guardrail, not a secret scanner. Confirm
with `git check-ignore -v Private/<file>` that every personal file remains
outside Git.
