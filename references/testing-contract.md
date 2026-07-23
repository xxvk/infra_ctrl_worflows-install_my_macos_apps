# Local testing contract

## Hermetic release check

Run:

```sh
python3 scripts/release_check.py
```

This is the default automated quality gate. It validates the catalog,
component documentation state boundary, configuration layers, release and
mutation contracts, installation-source policy, Skill structure, bootstrap definition, all fixture/unit
tests, the macomrade route/identity contract, and Python compilation. It must not inspect the user's live Applications
folders, invoke Homebrew, read the real TCC database, call `defaults`, or
change external state.

Fixtures under `tests/fixtures/` provide deterministic Homebrew, App Store,
TCC, defaults, and filesystem evidence. Tests must patch process execution and
paths so a developer account, installed app, permission, or device is never a
test prerequisite.

## Live macOS supplement

Run:

```sh
python3 scripts/release_check.py --include-live-smoke
```

The additional smoke phase reads the current Mac and writes only temporary or
machine-local scan/plan/install-dry-run records. It never passes `--apply`.
Live smoke can reveal integration drift but cannot replace a genuine clean-Mac
acceptance run.

## Required negative contracts

- Dry-run executes no mutating external command.
- Missing or unavailable TCC/defaults interfaces remain unavailable, never
  empty or successful.
- Unknown plan targets and oversized install batches stop before execution.
- Interrupted apply writes no success record.
- Repeated apply renders the same idempotent package-manager command sequence.
- State migration refuses unavailable sources and conflicting destinations,
  and cleanup requires its exact confirmation phrase.
- Component guides reject runtime fields, completed checkboxes, local evidence
  blocks, state-record links, and current-status tables.
- Component-state migration preserves exact lines and source hashes locally
  before tracked documentation is normalized.
- Supply-chain policy rejects mutable network-to-shell execution, unpinned npm
  globals, unreviewed third-party taps, and public decrypted-IPA source details.
- Clean-Mac acceptance rejects ineligible attestation, dirty or changed source,
  secret-bearing evidence, incomplete gates, and under-evidenced finalization.
  Harness tests never claim the external hardware run occurred.
- macomrade rejects unknown or reserved routes before starting a subprocess, preserves
  legacy argument order and exit codes, and never adds `--apply` or another
  mutation authorization implicitly.

GitHub Actions is not part of this contract unless the user explicitly changes
the local-validation policy.
