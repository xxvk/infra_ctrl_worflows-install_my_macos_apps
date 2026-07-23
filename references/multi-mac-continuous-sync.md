# Keeping multiple Macs converged over time

Documentation only. The skill's existing design bootstraps *one* new Mac
against the tracked baseline; it has no notion of "Mac A changed, now
reconcile Mac B." This records the actual mechanism already available and
its real limits, rather than proposing new infrastructure that isn't
needed yet.

## What already propagates automatically across Macs

Because this repository lives under iCloud Drive
(`iCloud~md~obsidian/Documents/XVK_PM`), every tracked file — the app
catalog, `settings/*.yaml`, `templates/`, `dotfiles/home/*`, this skill's
scripts themselves — syncs to every Mac signed into the same Apple Account
with iCloud Drive enabled for this folder, independent of any Git push/pull.
Editing `Private/dock-order.json` on Mac A makes the new desired value
visible on Mac B as soon as iCloud finishes syncing.

**What does not propagate**: applying that change. iCloud sync moves the
*file*, not its effect. A new desired value in a tracked `settings/` file
has no effect on Mac B until something on Mac B actually runs the
corresponding `--apply`/`--check` command.

## The actual reconciliation loop

1. Change a tracked policy value on one Mac (e.g. edit
   `Private/dock-order.json`, `Private/keyboard.yaml`, or
   `Private/system-preferences-values.json`).
2. iCloud Drive syncs the file to every other Mac (no action needed).
3. On each other Mac, run the matching `--check`:
   - `python3 scripts/macos_preferences.py --check`
   - `python3 scripts/macos_dock.py` (compare against
     `Private/dock-order.json`)
   - `python3 scripts/bootstrap_verify.py` for the full picture
4. Review the reported drift and run the corresponding `--apply` on that
   Mac after confirming it's still wanted there — some tracked values are
   genuinely meant to differ per Mac (see "Not every value should
   converge" below).
5. The weekly drift-check LaunchAgent added in this backlog
   (`scripts/drift_check_schedule.py`) automates step 3 so a stale Mac
   surfaces its drift on its own schedule instead of only when someone
   remembers to check — but it still only *reports*; step 4 stays manual
   and explicit on every Mac, matching this skill's no-silent-apply rule.

## Not every value should converge

Some tracked settings are legitimately per-Mac, not a target to force
identical everywhere:

- `Private/keyboard.yaml`'s K240 profile only applies to a Mac with that
  physical receiver attached.
- Capacity-tier app selection (`portable` vs `expanded` in
  `macos_apps.py plan --profile`) depends on that Mac's actual disk size.
- Machine-local observations under Application Support are never meant to
  converge across Macs at all — by design, they never leave the Mac that
  produced them.

Before treating a `--check` mismatch as drift to fix, confirm the value is
actually meant to be identical across every Mac and not one of these
per-machine exceptions.

## Known conflict risk

See the cross-reference in
[`references/icloud-vs-skill-boundary.md`](icloud-vs-skill-boundary.md):
concurrent local `git commit`s on two Macs while iCloud is also syncing the
same working tree can conflict. If actively editing tracked policy on more
than one Mac in the same session, prefer finishing and letting iCloud sync
settle on one Mac before switching to edit the same files on another.
