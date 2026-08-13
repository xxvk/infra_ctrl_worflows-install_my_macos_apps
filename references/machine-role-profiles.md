# Composable machine-role Profiles

## Contents

- [Purpose](#purpose)
- [Role model](#role-model)
- [Planning](#planning)
- [Overrides and boundaries](#overrides-and-boundaries)
- [Validation](#validation)

## Purpose

Machine roles describe reusable intended capability, not current-machine
observation or an authorization to install. The public catalog is
[machine-roles.json](../settings/machine-roles.json). Its base role always
selects active Core applications. Additional roles explicitly bring selected
Optional applications into a plan.

Roles are composable. A current compact robotics developer Mac is represented
by auto,developer,robotics; auto resolves to compact below 512 GB and expanded
at or above 512 GB. A high-memory content machine can use
auto,developer,content. The role string is operator input, rather than a
synced host identity, so one repository can safely prepare multiple Macs.

## Role model

The initial roles are:

| Role | Purpose |
| --- | --- |
| base | Active Core applications and portable baseline policy. |
| compact / expanded | Capacity classification selected by auto. |
| developer | Xcode and xurl beyond Core. Cursor remains manually selectable Optional software. |
| robotics | Inherits developer; adds Android Studio, Android File Transfer, and Foxglove; excludes Android Studio Preview. |
| content | Explicit creative audio, video, and design applications. |
| gaming | Optional PlayCover learning/gaming applications. |

Inheritance is resolved parent-first. A role can include or exclude catalog
apps. Explicit command-line inclusion wins over role exclusions; explicit
command-line exclusion is final. Every included or excluded app receives an
explanation in the generated plan.

## Planning

Plans without a roles argument default to `auto`: Core plus the detected
`compact` or `expanded` capacity role. Optional applications are never selected
merely because they are active. Use roles deliberately for a Core-plus-role
plan, or use `--include-app Cursor` when Cursor is wanted on one machine:

    ./bin/macomrade plan apps --profile auto
    ./bin/macomrade plan apps --profile auto --roles auto,developer,robotics
    ./bin/macomrade plan apps --profile auto --include-app Cursor
    ./bin/macomrade plan apps --profile auto --roles auto,content
    ./bin/macomrade diagnostics roles --roles auto,developer --storage-gb 256

The include-app and exclude-app flags change only the current plan. They do
not edit the catalog, grant a permission, or install anything. Installation
still requires the separately reviewed plan and explicit apply flag.

## Overrides and boundaries

Roles may select applications and portable policy only. They must not automate
account login, license activation, privacy grants, VPN connection, purchases,
or security-policy changes. Those remain manual checkpoints even when an app is
included by a role.

Do not put computer names, serial numbers, paths, installed state, or
measurements into the role catalog or Private. Those are machine-local
observations. Add a new role only after selecting concrete catalog components
and documenting its rationale.

## Validation

    python3 scripts/machine_roles.py validate
    ./bin/macomrade diagnostics roles --roles auto,developer,robotics --storage-gb 256

Validation rejects unknown catalog apps, missing parents, inheritance cycles,
and invalid schema. Hermetic tests prove parent-first composition and explicit
include/exclude precedence.
