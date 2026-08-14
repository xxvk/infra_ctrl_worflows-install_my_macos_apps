---
component_id: "uv"
name: "uv"
category: "Developer CLI"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-formula"
brew_cask: null
brew_formula: "uv"
official_url: "https://docs.astral.sh/uv/"
check_command: "uv"
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 20000000
download_estimate_method: "catalog_size_gb_planning_estimate"
cli_path: "/opt/homebrew/opt/uv"
---
# uv

`uv` owns a regenerable download/build cache separately from project virtual
environments. Inspect with `uv cache dir` and `uv cache size`; use
`uv cache clean` for a user-approved full cache reset. The next sync or run may
redownload wheels and rebuild packages.

macomrade may classify only the resolved uv cache root as `safe_cache` through
the public storage policy. Never generalize that permission to `.venv`,
`~/.local/share/python`, project source, lockfiles, or Hugging Face model
caches. Record current size and measured reclaim only in machine-local state.

## Orphaned uv tool environments

A failed or partial tool removal can leave both an environment under the
directory reported by `uv tool dir` and a launcher under `~/.local/bin`. For
example, Aider may use an `aider-chat` environment and an `aider` launcher.
Inspect all three views before proposing cleanup:

```sh
uv tool list
uv tool dir
readlink ~/.local/bin/<launcher>
```

If the tool is still registered, prefer `uv tool uninstall <package>`. If it
is no longer registered, its interpreter target is missing, and the launcher
points only into that exact orphan environment, preview the environment and
launcher as two explicit targets. After user approval, remove only those
targets; do not delete the whole uv tool directory or run `uv cache clean` as
a substitute. First verify that no process is executing from the environment.

After cleanup, require the environment and launcher to be absent and rerun
`uv tool list`; it must no longer emit an orphan-environment warning. Record
the exact paths and measured reclaimed bytes only in machine-local state.
