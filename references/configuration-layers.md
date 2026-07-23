# Configuration layers

## Contract

Keep reproducible configuration in four distinct layers:

1. **Public base** — reusable engine, catalog, scripts, and non-personal policy
   in the existing tracked paths.
2. **Tracked Private overlay** — user-approved identifiers, account/profile
   mappings, names, and preferences under `Private/`. These files are committed
   and synchronized through Git; they are private configuration, not secrets.
3. **Machine-local state** — detected versions, paths, permissions, timestamps,
   measurements, and logs under the directory returned by
   `scripts/state_paths.py path`.
4. **Secrets** — passwords, access/refresh tokens, private keys, recovery codes,
   cookies, and session material in Keychain or another user-controlled secret
   store, never Git.

The deterministic merge order is public base followed by the tracked Private
overlay. Objects merge recursively, scalar values replace their base value,
and arrays replace rather than concatenate. Preserve unknown object fields so
a newer producer does not lose data when an older loader performs a merge.

`Private/manifest.json` is the tracked registry for overlays. An empty manifest
is valid while existing personal configuration remains in its historical
tracked path.

The application catalog uses `Private/app-catalog-overlay.json`, merged by
stable app name. Public follow-up text may contain `{preferred_account}`;
`scripts/config_layers.py` requires the corresponding Private value and renders
the prompt only after merging.

Dock membership/order and confirmed allowlisted macOS preference values live in
`Private/dock-order.json` and `Private/system-preferences-values.json`.
Historical paths under `settings/` remain tracked locators so older commands
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

Existing tracked configuration remains tracked throughout this process. Never
turn the tracked Private layer into `.gitignore` content.

## Validation

Run:

```sh
python3 scripts/config_layers.py audit
python3 -m unittest tests/test_config_layers.py
```

The audit rejects paths outside the repository and common secret-bearing key
names. This is a guardrail, not a secret scanner; review every Private change
before committing.
