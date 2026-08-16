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
- Safari source validation accepts only a user-mediated Bookmarks-and-Reading-List-only export
  for item enumeration. Capability inspection may read Safari app metadata and
  internal-file presence/readability, but never opens bookmark content; iCloud,
  Apple Events, WebDriver, extensions, `SSReadingList`, and the internal plist
  cannot silently become item sources.
- Browser-item validation requires explicit browser/profile/account and
  collection boundaries, opaque non-URL-derived identity, lifecycle and
  conflict evidence, and `execution_authorized: false`. Only fictional
  synthetic fixtures may set `git_allowed: true`; private exports and machine
  observations must fail closed if marked Git-authorized.
- Safari export parsing accepts only an explicitly supplied ZIP containing one
  combined Netscape HTML member or one bookmarks plus one Reading List member;
  directory entries and AppleDouble metadata are ignored. It rejects extra
  CSV/JSON or other semantic files,
  encryption, symbolic links, path traversal, unsafe compression ratios,
  oversized inputs, malformed signatures, and schema-invalid items. The CLI
  emits counts and booleans only—never the input path, artifact hash, URL,
  title, or folder—and performs no write.
- Browser URL normalization removes only query keys in the tracked,
  authority-backed allowlist. It preserves raw path bytes, fragments, retained
  query order, repeated and unknown parameters, and non-default ports. A
  protected key/prefix, userinfo, backslash authority, semicolon query,
  unsupported scheme, or malformed authority blocks the whole proposal.
  Duplicate review never crosses browser/profile/account identity boundaries,
  explains exact/canonical/title/collection evidence, emits only counts from
  its CLI, and never authorizes merge, move, or deletion.
- Private duplicate review export is preview-only by default. Applied export
  requires `EXPORT PRIVATE BROWSER REVIEW`, accepts only a JSON destination
  below `Private/browser/`, creates it atomically with mode `0600`, validates
  read-back against the registered Schema, refuses a different existing file,
  keeps stdout free of paths/hashes/URLs/titles/item IDs, and never writes
  Safari or grants execution authority.
- Browser organization compilation requires complete and unique coverage of
  the source export, disjoint path rules and item overrides, exact duplicate
  membership, asserted summary counts, valid two-level targets, and
  `execution_authorized: false`. Preview is aggregate-only. Applied sync
  requires `SYNC PRIVATE BROWSER ORGANIZATION`, writes one mode-0600
  Git-ignored JSON atomically, refuses a different target, and never writes
  Safari. Organization-derived plans include bookmark move/archive/delete
  operations only; Reading List decisions and title suggestions never enter
  the transaction plan.
- Browser evidence import accepts only one validated regular-file Safari ZIP,
  derives a date-and-hash destination below `Private/browser/evidence/`, and
  previews without writing. Applied import requires `IMPORT PRIVATE BROWSER
  EVIDENCE`, preserves exact bytes, writes atomically with mode `0600`, verifies
  source stability, destination hash and parser binding, confirms Git ignore,
  and refuses links, malformed exports, changed sources, or different existing
  bytes. Output never contains a path or hash and the action never writes
  Safari.
- Browser reconciliation validates the old organization and new export,
  inherits only equal-multiplicity semantic fingerprints, exact path rules,
  unchanged item overrides, and duplicate groups with identical fingerprint
  multisets. Added/changed unresolved items, removed items, ambiguity, and
  duplicate membership drift block candidate generation. Applied persistence
  requires `WRITE PRIVATE BROWSER RECONCILIATION CANDIDATE`, writes one
  mode-0600 Git-ignored versioned organization atomically, refuses conflicts,
  and never switches the canonical organization or writes Safari.
- Browser lifecycle policy keeps the five built-in classification IDs stable,
  bounds public and custom review periods, and never authorizes browser writes.
  Private decision-ledger validation rejects Git-authorized personal content,
  duplicate IDs/labels, unknown classifications, multiple active decisions for
  one item/identity, and non-forward review dates. Suppression requires an
  unchanged semantic fingerprint, the same browser/profile/account boundary,
  a unique active match, and a future review date; changed, expired, ambiguous,
  or cross-identity items re-enter the queue. CLI output contains counts and
  reason names only, never labels, notes, item IDs, fingerprints, or paths.
- Browser transaction planning accepts only an explicit verified Bookmarks-and-Reading-List-only
  Safari export and item-scoped move/merge/archive/delete intent. Plans bind the
  export hash, item fingerprints, identity boundaries, operation counts, and a
  self-hash. Freeze preview writes nothing; apply requires `FREEZE BROWSER
  PLAN`, writes one mode-0600 machine-local plan atomically, refuses conflicts,
  and never writes Safari. Export/item drift, cross-identity merge, self-merge,
  malformed targets, plan tampering, and ambiguous post-state counts fail
  closed. Post-export verification emits counts only. Live Safari apply remains
  blocked while no supported enumerate-and-mutate interface exists.
- Browser macomrade routes preserve exact argument order and never add apply or
  confirmation authority. The browser apply route remains read-only and
  blocked. Browser reports accept only named redacted summary kinds and
  allowlisted aggregate fields; raw parses, frozen plans, unknown browser
  documents, private-content claims, paths, URLs, titles, item IDs, and
  fingerprints never enter localized terminal or semantic static HTML output.
- Safari-only live acceptance parses the same explicit export twice, preserves
  the shared-profile boundary, compares deterministic review/decision/plan
  evidence in memory, and performs no write. Invalid exports, unstable runs,
  invalid ledgers/plans, or post-export mismatches fail closed. Missing
  optional inputs remain deferred, Safari apply remains interface-limited,
  Chrome remains `deferred_by_user`, and no partial result can become complete
  0.3.0 acceptance.

GitHub Actions is not part of this contract unless the user explicitly changes
the local-validation policy.
