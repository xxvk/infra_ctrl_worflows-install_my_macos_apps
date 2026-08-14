# Local testing contract

## Hermetic release check

Run:

```sh
python3 scripts/release_check.py
```

This is the default automated quality gate. It validates the catalog,
component documentation state boundary, configuration layers, release and
mutation contracts, installation-source policy, Skill structure, bootstrap definition, all fixture/unit
tests, the formal JSON Schema registry and migrations, the macomrade route/identity contract, and Python compilation. It must not inspect the user's live Applications
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
- Registered JSON examples validate before use; unsupported schema keywords
  fail closed; migrations preserve unknown fields, preview without writing,
  require exact confirmation for a separate output, and refuse conflicts.
- Machine roles reject unknown apps and inheritance cycles; their parent-first
  selection and explicit include/exclude precedence remain deterministic.
- Every declared locale has the same message and placeholder IDs; stable CLI
  identifiers never depend on translated output.
- Application adapters inspect metadata only and expose no generic apply path;
  a destructive handoff must name a pre-existing exact-confirmation action.
- Benchmarks use bounded, repeatable command sets with a cold/warm pair and
  compare only local baselines against declared absolute/regression budgets.
- Audit reports omit paths and private content, retain textual status without
  ANSI/color dependence, and render semantic static HTML without scripts.
- The drift monitor is read-only, defers on low battery, deduplicates unchanged
  findings with severity cooldowns, and never invokes a repair workflow.
- Publication inventory records paths, categories, and counts only; matched
  sensitive text is never copied, and no finding authorizes visibility or
  history changes.
- Public-clone rehearsal requires a clean exact commit, strips inherited
  credential channels, forces public-only configuration, writes runtime state
  outside the clone, and fails if `Private/`, personal output markers, or a
  dirty clone appears. Local transport is not anonymous GitHub proof.
- Diagnostic collection is allowlisted and bounded; redaction removes
  credential/account/host fields and sensitive text; preview writes nothing;
  export requires exact confirmation, refuses overwrite, and verifies ZIP
  members and manifest hashes on read-back.
- Storage scans keep logical and allocated bytes separate, deduplicate hard
  links, never follow symlinks or materialize dataless files, and treat
  third-party File Providers as read-only handoffs. Sanitized live-sample
  fixtures prove multi-GiB iCloud logical content with sub-MiB allocation is
  not a high-value reclaim recommendation.
- Storage apply rejects wrong confirmation, stale plan hash, changed path,
  inode/size/cloud drift, unsupported provider, unproven cache, offline or
  undersized archive target, and conflicting restore destination. Reaching the
  actual free-space target stops the remaining action list.
- Trash staging records zero measured reclaim; only a separate exact-confirmed
  manifest purge may measure reclaimed bytes. Reimporting identical Mole
  history is idempotent and never creates a decision.

GitHub Actions is not part of this contract unless the user explicitly changes
the local-validation policy.
