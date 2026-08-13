# Low-noise Drift Monitor

## Contents

- [Purpose](#purpose)
- [Finding and notification policy](#finding-and-notification-policy)
- [Power and privacy](#power-and-privacy)
- [Scheduling](#scheduling)
- [Commands](#commands)

## Purpose

The monitor is a read-only wrapper around the existing final drift check. It
turns its bounded findings into stable IDs, deduplicates unchanged findings,
and emits only new or cooldown-due summaries. It never repairs drift.

## Finding and notification policy

[drift-monitor.json](../settings/drift-monitor.json) defines the minimum
battery threshold, confidence filter, severity cooldowns, maximum summary
length, and intended weekly schedule. Missing Core apps are high severity,
source mismatches and tracked-preference mismatches are medium, and unavailable
read-only checks are low. Findings without enough confidence are not surfaced.

The local ledger retains only finding ID, severity, confidence, generic message,
and timestamps. It intentionally excludes paths, usernames, app document names,
TCC rows, command output, and accounts.

## Power and privacy

On battery below the configured threshold, the monitor defers before running a
scan. It runs normally while charging. It makes no network request, launches
no GUI, reads no TCC database, and creates no tracked file.

## Scheduling

The existing weekly LaunchAgent remains opt-in. Its installation transaction is
unchanged, but its command now calls `drift_monitor.py run`. Preview it first;
only the user-approved existing `--apply` transaction writes or loads the
LaunchAgent.

## Commands

    python3 scripts/drift_monitor.py validate
    ./bin/macomrade scan monitor
    python3 scripts/drift_check_schedule.py install
    python3 scripts/drift_check_schedule.py install --apply

The first three are read-only or dry-run. Schedule installation does not grant
permission to install apps, alter preferences, delete data, or perform repairs.
