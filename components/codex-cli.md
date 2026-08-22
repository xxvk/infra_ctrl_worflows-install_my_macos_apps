---
component_id: "codex-cli"
name: "Codex CLI"
category: "Developer CLI"
tier: "core"
lifecycle_status: "planned"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "codex"
brew_formula: null
official_url: "https://github.com/openai/codex"
check_command: "codex"
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 100000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---

# Codex CLI

Codex CLI is a separate terminal capability from the ChatGPT desktop app.
Prefer the declared Homebrew/standalone delivery when ChatGPT is not already
installed. When ChatGPT is installed and its bundle contains the executable
below, the app-bundled path is a reviewed fallback for users who want the same
Codex build and shared configuration as the desktop app:

```text
/Applications/ChatGPT.app/Contents/Resources/codex
```

This is a Codex-specific exception to the general rule against arbitrary
links into application bundles. Do not generalize it to other apps.

## Installation

1. Check whether `codex` already resolves to a working command. Do not change
   an existing command without a source/version comparison.
2. If ChatGPT is the intended source, inspect the exact bundle path and verify
   that the containing app passes strict code-signature verification. Read the
   nested CLI's signing metadata and version separately; a working version
   command alone is not a trust check:

   ```sh
   APP_CLI="/Applications/ChatGPT.app/Contents/Resources/codex"
   test -x "$APP_CLI"
   codesign --verify --strict --verbose=2 /Applications/ChatGPT.app
   codesign -dv --verbose=2 "$APP_CLI" 2>&1
   "$APP_CLI" --version
   ```

   Confirm that the outer metadata identifies `com.openai.codex`, the nested
   metadata identifies `codex`, and both report the same `TeamIdentifier`. If
   strict verification fails but those identities still match, report the
   exact failure and obtain separate explicit confirmation to reuse that
   already-installed App binary; record it as an accepted verification
   exception, never as a valid signature. If the identities differ or signing
   metadata is absent, stop and use the standalone/Homebrew delivery.

3. Use only the user-local destination `"$HOME/.local/bin/codex"`. Confirm
   that `"$HOME/.local/bin"` is already on `PATH`; adding it to a shell startup
   file is a separate explicitly authorized change.
4. Inspect the destination before any write. If it is a regular file, or a
   symlink to any other target, stop and ask the user; never overwrite it.
5. After explicit confirmation, create the link without forcing replacement:

   ```sh
   mkdir -p "$HOME/.local/bin"
   ln -s "$APP_CLI" "$HOME/.local/bin/codex"
   ```

6. Refresh the current shell (`rehash` in zsh) or start a new shell.

Homebrew/standalone remains the fallback when the ChatGPT bundle is absent,
the executable is not signed/usable, or the user wants an independently
updated CLI. Do not install a second CLI merely because the app-bundled CLI is
not currently on `PATH`.

## Configuration

The CLI and desktop/IDE clients read the shared user configuration from
`~/.codex/config.toml`, including the default model, provider, MCP, sandbox,
and approval settings. Do not copy the app's configuration into another file.

Keep authentication in Codex's existing credential store. Never place API
keys, tokens, or endpoint credentials in this guide, the catalog, Git, or
machine-local records. If a custom provider is already configured, do not run
`codex logout`/`codex login` or replace its `base_url` as part of linking.

## Verification

```sh
command -v codex
readlink "$HOME/.local/bin/codex"
codex --version
```

- [ ] `command -v codex` resolves the user-local link.
- [ ] `readlink` returns the exact ChatGPT App resource path when that fallback
      is selected.
- [ ] The CLI version command succeeds.
- [ ] Run `codex doctor` when a configuration/authentication health check is
      needed; record only redacted pass/fail evidence in machine-local state.

Do not treat a link, a version result, or a package-manager receipt as proof
that authentication or the configured provider can reach its endpoint. Test
the intended workflow separately without exposing credentials.

## Updates and rollback

Do not run `codex update` when the link targets the ChatGPT App bundle. Update
ChatGPT through its normal app updater, then rerun the verification commands;
the stable bundle path should point to the new embedded CLI. If the app is
moved or removed, stop and choose the standalone/Homebrew delivery instead of
repairing the link to an unverified binary.

To roll back only this fallback, remove the link only when it still targets
the exact app resource path:

```sh
DEST="$HOME/.local/bin/codex"
APP_CLI="/Applications/ChatGPT.app/Contents/Resources/codex"
[ -L "$DEST" ] && [ "$(readlink "$DEST")" = "$APP_CLI" ] && unlink "$DEST"
```

This leaves the ChatGPT app, `~/.codex`, and all credentials untouched.

## Evidence and notes

- Official CLI documentation: https://learn.chatgpt.com/docs/codex/cli
- Shared configuration documentation: https://learn.chatgpt.com/docs/config-file/config-basic
- Current command paths, versions, timestamps, and verification outcomes
  belong only in machine-local state.
