# Component documentation state boundary

Tracked component guides describe reusable intent:

- stable component identity, category, tier, and lifecycle;
- reproducible source and delivery method;
- desired non-secret configuration;
- installation, verification, rollback, and recovery know-how;
- expected paths and commands when they are part of the delivery contract.

They do not describe one Mac's result. Detected versions and paths,
installation status, timestamps, byte measurements, completed checkboxes,
permission grants, account state, scan results, and verification results belong
only in the directory returned by:

```sh
python3 scripts/state_paths.py path
```

`lifecycle_status` is reusable product intent, not installation state:

- `planned`: desired but not yet adopted by the reusable baseline;
- `active`: part of the desired baseline;
- `retired`: deliberately excluded or replaced;
- `blocked`: desired behavior cannot currently be delivered.

It must never be inferred from the current Mac's app inventory.

## Audit and migration

Audit all component guides:

```sh
python3 scripts/component_state.py audit
python3 scripts/audit_component_frontmatter.py
```

Before removing historical machine observations from tracked guides, preserve
the exact guide, source SHA-256, line, code, and text in machine-local state:

```sh
python3 scripts/component_state.py migrate
python3 scripts/component_state.py migrate \
  --apply \
  --confirm "MIGRATE COMPONENT STATE"
```

Migration is additive and does not edit the source guides. Normalize the guides
only after reading back the generated record. The component template and
frontmatter repair tools must never add runtime state fields.
