# Performance and resource benchmarks

## Contents

- [Purpose](#purpose)
- [Measured operations](#measured-operations)
- [Budgets and baselines](#budgets-and-baselines)
- [Commands](#commands)
- [Boundary](#boundary)

## Purpose

The benchmark runner measures seven representative read-only workflows: app
inventory/plan, storage scan/plan, validation, drift, and legacy-state
migration inspection. It records cold and warm elapsed time, per-sample peak
RSS through macOS `time(1)`, captured output bytes, and allocated state growth.

Measurements are machine-local evidence, not portable configuration. A result
is a review signal rather than an automatic failure or permission to weaken a
safety check.

## Measured operations

`inventory` runs app scan, `plan` runs the capacity-aware planner, `validate`
runs the hermetic release gate, `drift` runs final read-only verification, and
`migration` only inspects legacy state. `storage_scan` scans a bounded tracked
fixture through the Foundation helper, and `storage_plan` plans from a tracked
scan fixture. The runner requires at least two
iterations: the first is cold and later ones are warm.

The bounded `storage_scan` operation represents the repeatable quick contract;
it is intentionally not an all-Home benchmark. A live deep scan is a separate
acceptance check because its cost depends on current Home contents, filesystem
permissions, App inventory, and `/private/tmp`. Keep its exact elapsed time,
RSS, output, and state growth in machine-local evidence. A partial traversal is
a valid safe result only when it is explicitly reported as `partial`; it must
never be relabeled complete to satisfy a timing target.

Drift may return 1 to represent an observed mismatch; that is a valid measured
outcome, not a benchmark execution failure. Any other unexpected return code
is surfaced for review.

## Budgets and baselines

[performance-budgets.json](../settings/performance-budgets.json) sets generous
absolute limits for elapsed time, peak RSS, output, and state growth. It also
defines a percentage-and-minimum-delta regression threshold. The optional
baseline is local to one Mac; do not copy it into Git or compare unlike
hardware as a performance regression.

## Commands

    python3 scripts/performance_benchmark.py validate
    ./bin/macomrade diagnostics benchmark --operation inventory --operation plan
    ./bin/macomrade diagnostics benchmark --operation storage_scan --operation storage_plan
    python3 scripts/performance_benchmark.py run --set-baseline

The first two commands write only machine-local benchmark records. The final
command replaces only the local performance baseline after review. It does not
change Mac configuration, install software, or publish a release.

## Boundary

Do not run expensive all-operation sampling repeatedly on battery. Do not use
benchmark records as a reason to skip full validation. The RC-15 release
manifest consumes only the bounded latest summary and never includes the state
path or raw benchmark record. Generating either artifact never commits, tags,
pushes, or releases the repository.
