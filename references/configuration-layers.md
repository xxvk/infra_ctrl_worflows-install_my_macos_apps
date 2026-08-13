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
