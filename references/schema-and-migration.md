# JSON Schema and migration contract

## Contents

- [Scope](#scope)
- [Registry and dialect](#registry-and-dialect)
- [Validation before use](#validation-before-use)
- [Migration contract](#migration-contract)
- [Compatibility and unknown fields](#compatibility-and-unknown-fields)
- [Commands](#commands)

## Scope

The 0.1.0 contract publishes versioned JSON Schemas for seven portable or
machine-readable boundaries:

| Kind | Current schema | Primary use |
| --- | --- | --- |
| `catalog` | `schemas/catalog-v1.schema.json` | Public application catalog |
| `settings` | `schemas/settings-v1.schema.json` | JSON settings locators and confirmed Dock/preference values |
| `private-overlay` | `schemas/private-overlay-v1.schema.json` | Private application-catalog overlay |
| `app-plan` | `schemas/app-plan-v1.schema.json` | Generated application installation plan |
| `state-record` | `schemas/state-record-v1.schema.json` | Generic machine-local state envelope |
| `diagnostic-result` | `schemas/diagnostic-result-v1.schema.json` | Local release-check result |
| `diagnostic-bundle` | `schemas/diagnostic-bundle-v1.schema.json` | Redacted support-bundle payload |

This work does not claim that every YAML settings file is JSON. The existing
keyboard and policy YAML files retain their conservative, workflow-specific
parsers. A future YAML schema system requires its own reviewed parser and
migration contract.

## Registry and dialect

[`schema-registry.json`](schema-registry.json) is the machine-readable source
of truth for kind names, current versions, schema paths, and tracked examples.
Every published schema declares JSON Schema Draft 2020-12.

The runtime validator in `scripts/schema_contract.py` uses only the Python
standard library. It implements the exact schema keywords used by these
contracts and fails closed if a schema introduces an unsupported keyword.
This avoids silently accepting a constraint that the local runtime did not
enforce. The schemas remain standards documents and may also be validated by a
full Draft 2020-12 implementation.

Schema validation establishes structure and version. Existing semantic
validators remain authoritative for cross-field policy such as source
consistency, guide existence, secret-key boundaries, and release
classification.

## Validation before use

The shared catalog loader validates the public catalog and Private overlay
before merging. The app installer validates an `app-plan` before selecting a
target or starting any subprocess. The final baseline verifier validates the
new plan before reading it. The release checker validates its own
`diagnostic-result` before returning it.

A legacy plan without `schema_version` is version 0. It is rejected at the
consumer boundary with a migration-oriented error; it is never guessed to be a
valid current plan.

## Migration contract

Version 0 means a pre-versioned JSON object. The 0.1.0 migrator supports only:

- upgrade `0 → 1`: add `"schema_version": 1`;
- downgrade `1 → 0`: remove only `schema_version`, and only with
  `--allow-downgrade`.

Migration is preview-only by default. An applied migration:

1. requires `--apply`;
2. requires exact confirmation `WRITE SCHEMA MIGRATION`;
3. requires a separate `--output` path;
4. never edits the source;
5. refuses a different existing output;
6. writes through a temporary sibling and atomically renames it;
7. re-reads the output and verifies its SHA-256.

Adopting the output as a canonical tracked file is a separate reviewed change.
The migration command does not commit, stage, replace, or delete anything.

## Compatibility and unknown fields

The catalog, settings, Private overlay, plan, generic state, and release-result
schemas allow unknown object fields at their intended extensibility
boundaries. Upgrade and downgrade copy the complete JSON structure and change
only `schema_version`; fixtures prove that unknown top-level and nested fields
survive a `0 → 1 → 0` round trip. The diagnostic-bundle schema is intentionally
strict with `additionalProperties: false`: a support artifact must add a new
reviewed schema field before collecting a new data class.

This preservation rule does not make unknown fields authoritative. Consumers
may ignore a field they do not understand, but must not erase it while merging
or migrating. A future schema version must add a named migration and fixtures;
never reinterpret version 1 in place.

## Commands

Inspect and validate:

```sh
./bin/macomrade diagnostics schemas
./bin/macomrade verify schemas
python3 scripts/schema_contract.py validate app-plan /path/to/plan.json
```

Preview an upgrade:

```sh
./bin/macomrade migration schema app-plan /path/to/legacy-plan.json --to 1
```

Write a separate verified migration artifact:

```sh
./bin/macomrade migration schema app-plan /path/to/legacy-plan.json \
  --to 1 \
  --output /path/to/plan-v1.json \
  --apply \
  --confirm "WRITE SCHEMA MIGRATION"
```

Downgrade preview additionally requires `--allow-downgrade`. Run
`python3 -m unittest tests.test_schema_contract` for deterministic positive,
negative, conflict, confirmation, and round-trip coverage.
