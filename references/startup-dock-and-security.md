# Startup items, Dock, and macOS security

Load this reference only when the current task uses this domain. Its rules were moved verbatim from the original skill entry point during RC-05.

## Contents

- Startup item and login component audit
- Dock configuration and order audit
- Developer-machine Gatekeeper policy

## Startup item and login component audit

Use `scripts/macos_startup_items.py` when the user asks what launches at login
or wants to remove selected startup applications/components:

```sh
python3 scripts/macos_startup_items.py scan
python3 scripts/macos_startup_items.py review
```

The scan reports three sources: macOS Login Items, the current user's
`~/Library/LaunchAgents`, and Background Task Management entries from
`sfltool dumpbtm`. The numbered `review` flow requires an explicit `DISABLE`
confirmation for each selected batch. It can remove a Login Item or disable a
user LaunchAgent; it does not automatically modify system LaunchDaemons,
delete applications, delete caches, or remove Background Task Management
records directly. Background-task entries are report-only and must be handled
through their corresponding Login Item or vendor setting.

Disabling a user LaunchAgent unloads it and renames its plist from `.plist` to
`.plist.disabled`, preserving a reversible copy. Never infer that an installed
app should launch merely because its bundle appears in the scan. After a
change, run `scan` again and record the result in machine-local state when a
machine-specific audit is needed.

## Dock configuration and order audit

The desired persistent Dock applications and their left-to-right order are
reusable skill configuration. The current machine's existence checks and scan
metadata are machine-local state. Scan and save both with:

```sh
python3 scripts/macos_dock.py
python3 scripts/macos_dock.py --save-config
```

The scan JSON in machine-local state preserves the ordered application list, bundle
identifier, path, existence check, and a `kind` classification. The reusable
configuration is stored in `Private/dock-order.json` without machine scan
timestamps or `exists` values. `kind` distinguishes
`system`, native third-party `native`, PlayCover `playcover`, and WebCatalog
wrappers `webcatalog`. A Dock entry is not evidence that an application is in
the reusable catalog or that it is installed from the same source.

In particular, the current Dock entries for **Notion** and **X** are
WebCatalog applications under `~/Applications/WebCatalog Apps/`, not native
Notion or X macOS applications. Preserve that distinction in audits and do not
replace their paths with `/Applications/Notion.app` or `/Applications/X.app`.

`Private/dock-order.json` is the desired baseline and is persisted with the
skill. It does not automatically reorder the Dock; any future apply workflow
must compare it with a fresh scan and explicitly request the user's approval.
Keep only current machine observations in machine-local state.

Dock appearance and behavior are tracked separately in
`Private/system-preferences-values.json`. The baseline currently requires:

- Dock on the left, 128 px tile size, and no Recent Applications section;
- launch animation enabled and running-app indicators enabled;
- minimize windows into their owning App icon (`minimize-to-application=true`),
  so minimized-window thumbnails are not shown as separate Dock items;
- no persistent directory stacks, including the “最近下载”/Downloads stack;
- unspecified Dock keys remain macOS defaults unless explicitly added to the
  baseline after review (for example, auto-hide, magnification, and minimize
  effect are not silently inferred).

Run `scripts/macos_preferences.py --check` to compare these values. Apply them
only through the normal explicit-confirmation preference workflow, then restart
the Dock if macOS does not reload the values immediately.

## Developer-machine Gatekeeper policy

This skill is primarily used for development Macs. The default developer
profile therefore records the following optional system policy in the plan:

```sh
sudo spctl --global-disable
```

This changes Gatekeeper from its normal assessment policy to the broader
“Anywhere” mode, making it easier to install trusted developer tools that are
not from the App Store or an identified/notarized developer. It is a deliberate
security trade-off: never run it silently. Before the first execution on a Mac,
show the user the exact command and obtain explicit confirmation. On recent
macOS releases, keep **System Settings → Privacy & Security** open, run the
command from a visible Terminal, then close and reopen that settings pane; the
“Anywhere” choice is hidden until this confirmation flow has been triggered.
If an automated administrator prompt is used, it may return “needs to be
confirmed in System Settings” rather than changing the policy. Verify the
result with `spctl --status` (expected output: `assessments disabled`) and
record only the policy state and timestamp in the machine-local state record; do
not put machine state in a component guide.

The matching rollback command is:

```sh
sudo spctl --global-enable
```

If the user declines the global policy, continue with the safer per-application
workflow: use macOS Privacy & Security → **Open Anyway** for a trusted app, or
use a narrowly scoped Homebrew cask install option when appropriate. Never
disable Gatekeeper merely to bypass an unverified or suspicious download.



