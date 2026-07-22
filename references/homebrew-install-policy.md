# Homebrew installation policy

Homebrew can upgrade an already-installed, outdated formula while processing a
new `brew install`. Installing a tool such as `scrcpy` may therefore upgrade an
existing dependency such as `ffmpeg`. This is different from `brew update`
(refresh formula metadata) and `brew upgrade` (explicitly upgrade packages).

## Default for this skill

The installation workflow uses:

```sh
HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_UPGRADE=1 brew install <formula-or-cask>
```

Before applying, record the installed versions of the target and known critical
dependencies. Afterward, compare versions and the transaction output. If an
existing package must still be upgraded to satisfy a dependency, stop and show
the old/new versions, reason, download size, and storage impact. Continue only
after explicit approval. Never silently run `brew upgrade` as an install
side-effect.

These flags are conservative, not a compatibility guarantee: a package may
fail when its dependency is too old. Offer the dependency upgrade as a separate
confirmed action when that happens.

## Version locking

Use `brew pin <formula>` only for a temporary, explicitly documented production
constraint. Verify with `brew list --pinned`; remove it with `brew unpin` after
the constraint ends. Do not make pinning the default because it blocks security
updates and can create dependency conflicts.

For reproducible environments, persist a reviewed `Brewfile`/catalog and
observed versions in ignored machine state. Do not promise a global “same major
version only” policy: Homebrew formulae do not guarantee strict SemVer behavior.
