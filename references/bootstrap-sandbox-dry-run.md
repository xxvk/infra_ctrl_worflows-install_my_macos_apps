# Sandboxed dry-run of the full bootstrap

Documentation only — no script here creates a sandbox account or VM. This
records how to exercise the full [disaster-recovery
runbook](disaster-recovery-runbook.md) without touching the production
account, at two levels of isolation, plus how the skill's own scripts
already support a dry-run mode independent of which environment you use.

## Level 1: every script's own dry-run mode (no sandbox needed)

Before reaching for an account or VM, note that almost every mutating
script in this skill already defaults to a dry-run and requires an explicit
flag to actually change anything:

| Script | Dry-run (default) | Applies |
|---|---|---|
| `macos_apps.py install` | prints the plan | `--apply` |
| `macos_preferences.py` | `--check` only compares | `--apply` |
| `docker_desktop_cleanup.py` | `inspect` | `remove --confirm '...'` |
| `capacities_cleanup.py` | no flags | `--apply --confirm "REMOVE CAPACITIES APP"` |
| `macos_permissions_cleanup.py` | no flags | `--apply` + typed `CLEAN TCC` |
| `dotfiles_sync.py link` | no flags | `--apply` |
| `drift_check_schedule.py install`/`uninstall` | no flags | `--apply` |

Running through the full runbook once with every mutating step in its
dry-run form (never passing `--apply`/`--confirm`) is itself a form of
end-to-end dry-run: it exercises every script's argument parsing, its read
paths, and its reporting shape against this Mac's real state, without
changing anything. This is the cheapest sandbox and requires no separate
environment — it is what `tests/smoke.sh` already does for a subset of
scripts.

Its limit: it never proves that the `--apply` code paths themselves work
(the actual file writes, `shutil.rmtree` calls, `launchctl bootstrap`
calls, App Store install flow) — only that they parse and stop at the
right gate.

## Level 2: a throwaway local admin account (lightweight, partial isolation)

For a closer approximation without a VM:

1. Create a new local administrator account (`System Settings > Users &
   Groups > Add Account`) — not on the production account.
2. `git clone` (or point at the same iCloud-synced) copy of this repository
   inside that account's home directory.
3. Run the full runbook (see [disaster-recovery-runbook.md](disaster-recovery-runbook.md))
   under that account, this time allowing real `--apply`/`--confirm` steps
   for anything that only touches that account's own state (app
   installs into `/Applications` are still machine-wide, not
   account-scoped — be aware installs and Homebrew changes affect every
   account on the Mac).
4. Delete the throwaway account when done (`sysadminctl -deleteUser`, see
   [account-removal.md](account-removal.md)) — this also removes its
   home directory and any account-scoped state.

What is isolated: that account's own Dock, Finder preferences, login
items, and per-user LaunchAgents/TCC grants.
What is **not** isolated: `/Applications`, Homebrew (`/opt/homebrew`),
system-level LaunchDaemons, and anything under `/Library` — a throwaway
account dry-run of `macos_apps.py install --apply` still really installs
software machine-wide. Treat this level as good for validating
preference/permission/dotfiles logic, not for validating app installation
or Homebrew bootstrap.

## Level 3: a full macOS VM (true isolation, higher cost)

For validating the entire runbook including real app installs and Homebrew
bootstrap without any risk to the host Mac, use a macOS virtualization tool
such as [UTM](https://mac.getutm.app/) or
[Tart](https://github.com/cirruslabs/tart) to run a genuinely separate
macOS instance:

1. Provision a fresh macOS VM (matching the host's major macOS version
   where possible, since some checks in this skill are version-sensitive,
   e.g. System Settings navigation paths).
2. Inside the VM, clone this repository and run the full runbook with real
   `--apply`/`--confirm` steps, including Homebrew bootstrap and Mac App
   Store sign-in (using a non-production Apple Account if App Store steps
   need to be exercised, to avoid mixing purchase history).
3. Record which steps failed and why in the VM (this is disposable state —
   never let VM-only observations leak into this repo's tracked `settings/`
   or `references/`).
4. Discard the VM afterward, or keep one "known-good VM snapshot" as a
   reusable dry-run baseline you revert to before each future test.

This is the only level that actually proves `--apply` code paths work end
to end, at the cost of installing and maintaining a virtualization tool and
a multi-GB VM image.

## What "the dry run passed" means

Regardless of level, a dry run is complete when:

- [ ] Every script in the runbook ran without a Python traceback.
- [ ] Every mutating script's dry-run/preview output matched what the
      operator expected before any `--apply`/`--confirm` was considered.
- [ ] `tests/smoke.sh` passes inside the sandbox environment too, not just
      on the host.
- [ ] Any interface documented as `unavailable` or
      `authorization_required` (System Extensions, Background Task
      Management, TCC database) is reported as such — not silently
      swallowed — since sandbox environments (especially fresh VMs) are
      exactly where these interfaces are most likely to differ from the
      host.
