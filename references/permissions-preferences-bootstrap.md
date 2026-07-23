# Permissions, preferences, and bootstrap

Load this reference only when the current task uses this domain. Its rules were moved verbatim from the original skill entry point during RC-05.

## Contents

- Required macOS permission preflight
- Permission inventory and bootstrap rule
- User-preference extraction rule
- Application workstyle baseline
- Bootstrap entry point
- Required iCloud/Git integrity preflight
- Stale TCC authorization cleanup

## Required macOS permission preflight

Before running any workflow that checks Chrome profiles, verify that the
Codex/ChatGPT process can read:

```text
~/Library/Application Support/Google/Chrome/Local State
```

This requires macOS permission at **System Settings → Privacy & Security →
Full Disk Access** for the app hosting Codex/ChatGPT (or the terminal process
running the skill). If the read is denied, stop the Chrome-profile check and
ask the user to grant that permission, then retry. Never report all expected
profiles as missing when the underlying error is `Operation not permitted`.
The preflight reads only profile directories and account identifiers exposed in
Local State; it must never read cookies, passwords, tokens, or Keychain data.

### Permission inventory and bootstrap rule

Before extracting protected system configuration, inventory the permissions
needed by the current workflow. At minimum distinguish Full Disk Access,
Accessibility, Input Monitoring, Screen Recording, Automation, Files and
Folders, microphone, and camera. A requirement must state its target, purpose,
required/optional status, System Settings path, and verification method.
Reusable requirements belong in [`../settings/privacy.yaml`](../settings/privacy.yaml);
current results belong only in machine-local state.

The complete permission category registry is the
`permission_category_matrix` in `settings/privacy.yaml`. It includes both
TCC categories and capability-only observations such as network access. A
matrix row is not an instruction to grant permission: authorize only the
target and workflow named in that row, then verify the workflow visibly.

Run the read-only inventory with:

```sh
python3 scripts/macos_permissions.py
```

The script verifies the Chrome `Local State` read directly and labels other
TCC categories for manual verification. It never changes permissions.

For the full machine inventory, run:

```sh
python3 scripts/macos_permissions.py
```

The resulting ignored state record contains four separate evidence layers:

1. Every detected app bundle from `/Applications`, `~/Applications`, system
   applications, WebCatalog, and PlayCover, including Bundle ID, version,
   path, source, code-signing identity, and entitlement **keys**.
2. Read-only TCC rows matched to Bundle IDs, with
   `verified_granted`, `verified_denied`, `tcc_records_present`, and
   `no_record` kept distinct. A missing row is not a denial.
3. An App × observed-service matrix and entitlement/TCC reconciliation. An
   entitlement indicates declared capability, never user authorization.
4. Non-App components: Homebrew formulae/casks, LaunchAgents, LaunchDaemons,
   privileged helper tools, network services, VPN connections, System
   Extensions, and Background Task Management output.

The scanner may report `unavailable` for `systemextensionsctl` or
`sfltool dumpbtm`. Preserve the exact interface error; do not interpret it as
an empty inventory. It must not use `sudo` or silently elevate.

Entitlement values, notification contents, Focus rules, cookies, passwords,
tokens, TCC database bytes, and private document contents are never persisted.

macOS privacy grants are device-local TCC state. The skill may check them and
open System Settings, but must not pretend that a raw TCC database copy,
`tccutil` reset, or stored authorization token is a portable grant. On a new
Mac, repeat visible authorization and then record the verification result
locally.

### User-preference extraction rule

Extract preferences by an allowlist, one domain at a time. Start with the
tracked Dock order and keyboard policy, then add input sources, Finder,
appearance, default applications, login items, and other explicitly selected
domains only when their values are understood and reproducible. Desired values
belong in tracked `settings/`; raw current readings and comparisons belong in
machine-local state. Never persist recent-document lists, private paths, serial numbers,
or secrets unless the user explicitly declares them portable.

Capture the first allowlisted baseline with:

```sh
python3 scripts/macos_preferences.py
```

This is an export/check operation only. Applying a preference requires a
separate reviewed policy entry and an explicit verification step.
After the desired values have been reviewed, compare them with the current
Mac using `python3 scripts/macos_preferences.py --check`.
Applying the reviewed values requires an explicit confirmation:

```sh
python3 scripts/macos_preferences.py --apply
python3 scripts/macos_preferences.py --check
```

The apply path is limited to the tracked allowlist and restarts Finder and
Dock so their settings reload; it does not apply permissions, login items,
default applications, or input-source changes.

The preference scanner currently captures an allowlisted baseline for machine
profile, locale/input sources, keyboard/HID mappings, text-input settings,
Dock/Finder, desktop/window management, screenshots, displays, sound/power
interfaces, notifications, Control Center, Focus database presence, and
screensaver fields. It also records a redacted LaunchServices association
slice and the developer environment shape: Shell, startup-file hashes, PATH
shape, Git key names, SSH config metadata, and CLI versions. Redact private
paths and text-substitution contents; never persist Git identity values, SSH
contents, or credentials. `--check` compares only tracked desired values;
unavailable interfaces remain unavailable rather than being converted to
defaults.

For hardware/network interfaces that return `AuthorizationCreate() failed:
-60008` or incomplete data in a non-admin shell, an explicitly requested
read-only baseline may use the macOS administrator authorization dialog for
`system_profiler`, `networksetup`, `scutil`, and `fdesetup`. Store only the
redacted result under machine-local state; omit display serial numbers, Wi-Fi
passwords, VPN credentials, certificates, and private keys. Do not use this
path to change DNS, proxy, firewall, FileVault, or VPN settings.

### Application workstyle baseline

Portable application behavior is defined in
[`../settings/app-workstyle.yaml`](../settings/app-workstyle.yaml). It separates
desired policy from current machine observations and manual authorization.
Use read-only checks first, then apply one app policy at a time. Account
identifiers, session databases, Keychain entries, app containers, IPA files,
private paths, and device telemetry are never portable configuration. The
current verification set covers K240, Solaar, Claude Developer Mode,
PlayCover YouTube, SmartDNS, Dock order, and startup listeners. GUI Login Items
remain incomplete until Automation permission is available.

### Bootstrap entry point

Use the ordered, read-only assessment before any new-Mac changes:

```sh
python3 scripts/bootstrap_macos.py --profile auto
```

It runs app scan, capacity-aware app plan, permission inventory, and
preference baseline/check in order. It never installs apps, grants TCC
permissions, enters accounts, or applies preferences. Resolve the output with
`python3 scripts/state_paths.py path` and review the generated
`bootstrap-*.json` record before separately authorizing any change.

Manual account, license, privacy, browser-profile, VPN, and app-configuration
checkpoints live in [`../settings/manual-actions.yaml`](../settings/manual-actions.yaml).
They are instructions and verification contracts only; never turn them into
credential storage or automatic login.

### Required iCloud/Git integrity preflight

This repository remains in iCloud Drive by design. Before any Git-dependent
operation—including status/diff used as release evidence, commit preparation,
submodule work, fsck, pull, push, or recovery—run:

```sh
python3 scripts/icloud_git_guard.py inspect --repo .
```

If the result is not `ready`, do not run Git. Treat `dataless`, `offline`, and
`archived` as File Provider availability states, not deletion or corruption.
Follow the plan-first grouped materialization, exact fallback, Finder **Keep
Downloaded** verification, read-only Git verification, and copy-first
fresh-clone recovery contract in
[`icloud-git-integrity.md`](icloud-git-integrity.md).
Never relocate this repository as remediation, never use `sudo` for
materialization, and never reset/repack/delete Git data to bypass the guard.

For Capacities, the app and its app-specific data are retired and may be
removed after the user explicitly requests cleanup:

```sh
python3 scripts/capacities_migration_inventory.py
```

It records only candidate locations, sizes, counts, and extensions. It does
not read document contents. After the user's cleanup confirmation, remove only
the app bundle with the auditable cleanup script:

```sh
python3 scripts/capacities_cleanup.py \
  --apply \
  --confirm "REMOVE CAPACITIES APP"
```

The cleanup preserves Capacities Application Support, preferences, HTTP
storage, and logs so data migration can be verified independently. It records
the app-bundle result in machine-local state. Do not remove unrelated browser
profiles or other application data.

Chrome profile identity is matched by account email. Profile directory names
such as `Profile 5`, `Profile 7`, or `Profile 9` are machine-local allocation
details and are informational only; they must not cause a missing-account
result or be used as the cross-machine identity key. Display names are checked
separately against the tracked registry.

Run the final read-only drift/recovery report with:

```sh
python3 scripts/bootstrap_verify.py
```

It records missing Core apps, source mismatches, permission drift,
preference-check results, and safe rerun commands. It never applies the
recovery commands automatically.

Login Items have two separate sources. User `LaunchAgents` can be inventoried
read-only from `~/Library/LaunchAgents`. The GUI Login Items list is queried
through Apple Events and may require an explicit Automation permission. If
that query fails, record the error and the LaunchAgents subset; never call a
partial result a complete Login Items baseline.

### Stale TCC authorization cleanup

Use [`../scripts/macos_permissions_cleanup.py`](../scripts/macos_permissions_cleanup.py)
for permissions belonging to apps that were deliberately removed. Its default
mode is dry-run:

```sh
python3 scripts/macos_permissions_cleanup.py
```

The script includes only classified legacy/removed clients by default. Add
`--include-manual-review` only after confirming an unlisted client is no longer
needed. Applying a reset requires `--apply` and typing `CLEAN TCC`; it calls
`tccutil reset` for exact service/client pairs and never removes application
data. Re-run the permission inventory afterward. Never reset current ChatGPT,
CUA, Perplexity, Logi Options+, or other active helper identities as part of a
generic cleanup.

The cleanup script uses the latest permission state and includes only clients
classified as legacy/removed by default. Manual-review clients require
`--include-manual-review`. It never deletes app data or repairs an incomplete
uninstall; Homebrew cask cleanup and data migration are separate tasks.

System Extension and Background Task discovery may be restricted by macOS:
`systemextensionsctl list` can return an OSSystemExtensionError, while
`sfltool dumpbtm` may require an administrator authorization context. Record
those exact interface states as unavailable or authorization_required; do not
interpret them as evidence that no extension or background task exists.

When a complete inventory is explicitly requested, the read-only commands may
be retried through the macOS administrator authorization dialog:

```sh
osascript -e 'do shell script "/usr/bin/systemextensionsctl list" with administrator privileges'
osascript -e 'do shell script "/usr/bin/sfltool dumpbtm" with administrator privileges'
```

Store the resulting raw observation only under machine-local state and record the
exact authorization context. In the current M4B result, System Extensions
reported `0 extension(s)` and Background Task Management returned real records;
these are observations, not portable grants or enable/disable instructions.

