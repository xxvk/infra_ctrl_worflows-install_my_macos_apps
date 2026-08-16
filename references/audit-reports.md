# Accessible audit reports

## Contents

- [Purpose](#purpose)
- [Inputs and outputs](#inputs-and-outputs)
- [Accessibility and localization](#accessibility-and-localization)
- [Commands](#commands)
- [Boundary](#boundary)

## Purpose

Audit reports render existing read-only JSON evidence into a concise terminal
summary or a standalone HTML document. JSON remains authoritative; the report
is a human view, not a repair engine.

## Inputs and outputs

The renderer accepts a `bootstrap-verify-*.json` record or one supported
redacted browser workflow summary. Baseline reports carry forward only
aggregate findings: missing Core app names, source mismatch names, permission
counts, preference status, and check outcome. Browser reports carry forward
only allowlisted counts, booleans, fixed interface status, stage, and outcome.
They omit filesystem paths, account/profile references, raw permissions,
command output, URLs, titles, folders, item IDs, fingerprints, notes, and
private content.

Raw Safari parser output, frozen browser plans, unknown browser kinds, and
inputs that do not explicitly declare private content absent and execution
unauthorized are rejected rather than rendered as empty successful reports.
The allowlisted browser kinds include the redacted
`browser_live_acceptance_summary`; only its aggregate count object and stable
overall status are rendered, never its gate evidence or runtime-private input.

## Accessibility and localization

Reports support `en`, `ja`, and `zh-Hans` through the common locale catalog.
The terminal report contains no ANSI-color dependence. HTML uses a semantic
main region, headings, table headers, textual status with an accessible label,
and contrast that meets the tracked WCAG AA policy. No client-side script,
remote asset, or telemetry is included.

## Commands

    python3 scripts/audit_report.py /path/to/bootstrap-verify.json --format tui --lang ja
    python3 scripts/audit_report.py /path/to/bootstrap-verify.json --format html --lang zh-Hans --output /path/to/report.html
    ./bin/macomrade diagnostics report /tmp/browser-review.json --format tui --lang zh-Hans
    ./bin/macomrade diagnostics report /tmp/browser-verify.json --format html --lang ja --output /tmp/browser-verify.html

The default prints to the terminal. An explicitly named unused output path
writes a local, static report only; it does not open, share, or upload it.

## Boundary

The renderer never changes an application, permission, preference, account,
or network setting. Review the source JSON and use the corresponding separate
workflow for any repair.

See [`browser-workflow-cli.md`](browser-workflow-cli.md) for the accepted
browser summary kinds and six-stage route contract.
