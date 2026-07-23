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

The launcher deliberately remains repository-local in 0.1.0. Installing a
global symlink, Homebrew formula, npm package, or application bundle is a
separate packaging and publication decision.

## Command map

The stable command families are:

```text
scan → plan → apply → verify → drift → diagnostics → migration
```

Examples:

```sh
./bin/macomrade scan apps
./bin/macomrade plan apps --profile auto
./bin/macomrade apply apps "$PLAN" --only "App Name"
./bin/macomrade apply apps "$PLAN" --only "App Name" --apply
./bin/macomrade verify baseline
./bin/macomrade verify release
./bin/macomrade verify schemas
./bin/macomrade drift baseline
./bin/macomrade diagnostics permissions
./bin/macomrade diagnostics schemas
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
shims for 0.1.x. `macomrade` delegates to those scripts with the same Python
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

## Reserved future commands

`mac-buro` and `5y-plan` are reserved as possible future Easter-egg commands.
They have no executable, alias, route, or behavior in 0.1.0. Calling either
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
