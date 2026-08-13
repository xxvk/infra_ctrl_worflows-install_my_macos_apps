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

The renderer accepts a `bootstrap-verify-*.json` record and carries forward
only aggregate findings: missing Core app names, source mismatch names,
permission counts, preference status, and check outcome. It omits filesystem
paths, account data, raw permissions, command output, and private content.

## Accessibility and localization

Reports support `en`, `ja`, and `zh-Hans` through the common locale catalog.
The terminal report contains no ANSI-color dependence. HTML uses a semantic
main region, headings, table headers, textual status with an accessible label,
and contrast that meets the tracked WCAG AA policy. No client-side script,
remote asset, or telemetry is included.

## Commands

    python3 scripts/audit_report.py /path/to/bootstrap-verify.json --format tui --lang ja
    python3 scripts/audit_report.py /path/to/bootstrap-verify.json --format html --lang zh-Hans --output /path/to/report.html

The default prints to the terminal. An explicitly named unused output path
writes a local, static report only; it does not open, share, or upload it.

## Boundary

The renderer never changes an application, permission, preference, account,
or network setting. Review the source JSON and use the corresponding separate
workflow for any repair.
