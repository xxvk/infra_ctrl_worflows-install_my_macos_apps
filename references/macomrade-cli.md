# macomrade CLI

## Contents

- [Identity](#identity)
- [Repository-local entry point](#repository-local-entry-point)
- [Command map](#command-map)
- [Authorization boundary](#authorization-boundary)
- [Compatibility contract](#compatibility-contract)
- [Reserved future commands](#reserved-future-commands)
- [Validation](#validation)

## Identity

`macomrade` is the distinct repository-local CLI name. It compresses Mac +
comrade into one memorable word and presents the
command as an operator's companion for preparing, inspecting, correcting, and
maintaining a Mac. This selection does not assign a product name; the product
name remains undecided.

The point-in-time collision audit is machine-readable in
[`cli-identity.json`](cli-identity.json). The 2026-07-23 check found no exact
local PATH, Homebrew formula/cask, npm, PyPI, crates.io, GitHub
repository/account, Mac App Store, or `.com`/`.net` software/domain collision.
Public search did find a same-name music artist and usernames. This is not
trademark clearance and does not reserve or register the name. `Mac` and
`macOS` remain Apple trademarks; do not imply Apple affiliation or endorsement.
The future App Store product name remains a separate, undecided decision.

## Repository-local entry point

Run the checked-in launcher from the repository root:

```sh
./bin/macomrade --help
./bin/macomrade routes
./bin/macomrade --version
```

The launcher deliberately remains repository-local in 0.2.0. Installing a
global symlink, Homebrew formula, npm package, or application bundle is a
separate packaging and publication decision.

## Command map

The stable command families are:

```text
scan → review → plan → apply → verify → history
drift → diagnostics → migration
```

Examples:

```sh
./bin/macomrade scan apps
./bin/macomrade scan adapters --adapter wechat
./bin/macomrade scan monitor
./bin/macomrade scan storage --mode quick
./bin/macomrade review storage --candidate ID --decision keep_local --apply
./bin/macomrade plan apps --profile auto
./bin/macomrade plan storage --target auto
./bin/macomrade plan apps --profile auto --roles auto,developer,robotics
./bin/macomrade plan adapters --adapter claude-vm
./bin/macomrade apply apps "$PLAN" --only "App Name"
./bin/macomrade apply apps "$PLAN" --only "App Name" --apply
./bin/macomrade apply storage "$STORAGE_PLAN" --action-class safe_cache --apply --confirm 'PURGE APPROVED REGENERABLE CACHES'
./bin/macomrade verify baseline
./bin/macomrade verify release
./bin/macomrade verify schemas
./bin/macomrade verify storage "$APPLY_RECORD"
./bin/macomrade history storage --import-mole
./bin/macomrade drift baseline
./bin/macomrade diagnostics permissions
./bin/macomrade diagnostics schemas
./bin/macomrade diagnostics roles --roles auto,developer --storage-gb 256
./bin/macomrade diagnostics adapters
./bin/macomrade diagnostics benchmark --operation inventory --operation plan
./bin/macomrade diagnostics report /path/to/bootstrap-verify.json --format html --output /path/to/report.html
./bin/macomrade diagnostics publication
./bin/macomrade diagnostics release-manifest
./bin/macomrade diagnostics public-clone
./bin/macomrade diagnostics bundle --output /path/to/diagnostics.zip
./bin/macomrade migration state inspect
./bin/macomrade migration schema app-plan /path/to/legacy-plan.json --to 1
```

Use `./bin/macomrade routes --json` for the complete machine-readable route
table. Use `./bin/macomrade --explain ...` to print the exact compatibility
command without executing it.

## Authorization boundary

The dispatcher adds no mutation flag, confirmation phrase, credential, or
privilege. In particular, `macomrade apply` names the workflow family but does
not silently append the underlying `--apply`. The called script remains the
authority for dry-run, exact target, confirmation, verification, rollback, and
record behavior.

Before an external change, follow the same reviewed mutation contract as the
legacy script. A route name is never authorization.

## Compatibility contract

Existing `python3 scripts/*.py` entry points remain supported compatibility
shims in 0.2.0. `macomrade` delegates to those scripts with the same Python
interpreter, repository root, argument order, standard input/output, and exit
code. It does not duplicate their implementation.

Unknown command families or targets fail before a subprocess starts. Arguments
after the family and target pass through unchanged, so existing automation can
migrate incrementally and compare `--explain` output before switching.

Schema migration is also only a route. It remains preview-only unless the
underlying command receives its explicit apply flag, separate output path, and
exact confirmation. See
[`schema-and-migration.md`](schema-and-migration.md).

Diagnostic preview and export are deliberately separate routes. Preview with
`diagnostics bundle`; export with `apply diagnostic-bundle` only after
reviewing the manifest and redaction report. The dispatcher never adds the
required `--apply` or exact confirmation. See
[`redacted-diagnostic-bundle.md`](redacted-diagnostic-bundle.md).

Release-manifest generation is also preview-only. It binds source, schemas,
public policy, validation, benchmark, limitations, and source-only provenance,
but writes no artifact and keeps commit, tag, push, release, and visibility
authority false. See [`release-manifest.md`](release-manifest.md).

The public-clone diagnostic requires a clean source commit, creates a
non-local temporary clone with a new HOME, disables credential prompts and
global Git configuration, forces public-only configuration, runs the complete
hermetic release gate and documented read-only quick start, and records only a
machine-local summary. While the GitHub repository remains Private, this is a
credential-free local-transport rehearsal—not proof of anonymous network
access. The final GitHub read-back remains a separate authorized transaction.

Role selection only changes the contents of the current application plan. App
adapter routes inspect metadata and prepare a handoff; there is intentionally
no `apply adapters` route. WeChat remains manual-only, and Claude VM cleanup
continues to use its existing exact-confirmation transactions. See
[`machine-role-profiles.md`](machine-role-profiles.md) and
[`app-adapter-sdk.md`](app-adapter-sdk.md).

Benchmark and report routes are read-only except that a benchmark writes a
machine-local measurement record and an explicitly requested report output
writes the named local static file. The drift-monitor route makes no repair and
its opt-in weekly LaunchAgent still requires the existing separate `--apply`
transaction. See [`performance-benchmarks.md`](performance-benchmarks.md),
[`audit-reports.md`](audit-reports.md), and
[`drift-monitor.md`](drift-monitor.md).

Storage adds the `review` and `history` families without weakening this
boundary. Review records a machine-local non-authorizing decision; history may
import content-addressed Mole evidence. Storage apply still requires the
underlying script's explicit `--apply`, one exact action-class confirmation,
fresh path/cloud checks, measurement, and replanning. See
[`storage-lifecycle.md`](storage-lifecycle.md).

## Reserved future commands

`mac-buro` and `5y-plan` are reserved as possible future Easter-egg commands.
They have no executable, alias, route, or behavior in 0.2.0. Calling either
through `macomrade` fails before a subprocess starts. Define the exact
purpose, safety boundary, help text, tests, and mutation contract before
activating either name.

## Validation

Run:

```sh
./bin/macomrade validate --json
python3 -m unittest tests.test_macomrade_cli
python3 scripts/release_check.py
```

Validation checks the identity contract, required command families, unique
routes, repository-bounded targets, executable launcher, target scripts, and
version source. Tests prove route parity, return-code propagation, unknown-route
rejection, and the absence of an implicitly added `--apply`.
