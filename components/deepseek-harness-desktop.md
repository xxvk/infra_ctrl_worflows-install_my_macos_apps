---
component_id: "deepseek-harness-desktop"
name: "DeepSeek Harness Desktop"
category: "AI Agent"
tier: "core"
lifecycle_status: "active"
source: "official_web"
delivery_method: "vendor-download"
brew_cask: null
brew_formula: null
official_url: "https://github.com/hairyf/deepseek-harness-desktop"
check_command: "test -d '/Applications/Deepseek Harness Desktop.app'"
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store model-provider API keys, passwords, tokens, recovery codes, or license secrets here."
download_estimate_bytes: 6854317
download_estimate_method: "github_release_asset_metadata"
---

# DeepSeek Harness Desktop

> [!summary] Purpose
> A lightweight community Tauri shell for the DeepSeek Harness web runtime. The
> desktop shell, downloaded Harness package, Node runtime, user data, and global
> `dsh` command are separate deliverables and must be verified separately.

This is not an official DeepSeek product. The catalog currently selects
[`hairyf/deepseek-harness-desktop`](https://github.com/hairyf/deepseek-harness-desktop)
instead of the heavier `anywhere-labs` Electron edition. Do not infer that data,
plugins, providers, or sessions migrate between the two implementations.

## Architecture and state boundary

The installed app is only the Tauri supervisor. On first launch it obtains the
compatible Harness package and starts the web profile on loopback. Its own
state root is:

```text
~/Library/Application Support/io.github.hairyf.deepseek-harness-desktop/
```

The downloaded CLI currently lives below `dependencies/dsh/`; desktop runtime
data lives below `data/dsh/`; diagnostics live below `logs/`. The app may reuse
a compatible Homebrew Node instead of embedding another runtime.

> [!warning] The state root is not a self-contained profile
> Do not treat the bundle-identifier directory as an isolated `DSH_HOME`. From
> `v0.7.1` the shell writes profile configuration into the shared, pre-existing
> `~/.dsh/` tree during first-launch provisioning:
>
> ```text
> ~/.dsh/profiles/web/pnpm-workspace.yaml   rewritten to extend pnpm allowBuilds
> ~/.dsh/profiles/web/.npmrc                created or ensured
> ```
>
> This is the application's own provisioning behavior, not a migration
> performed by this skill, and it happens with no separate prompt. Plan for it:
> installing or upgrading this shell **mutates shared CLI state that other DSH
> consumers also read**. Capture `~/.dsh/profiles/web/` before install when its
> current contents matter, and never describe the desktop profile and the
> global CLI state as independent.

The shell also writes command shims to `~/.local/bin/dsh` and
`~/.local/bin/pnpm`. It preserves an existing user file at either path and logs
the skip rather than overwriting, so a hand-managed wrapper survives install.
Verify the shim target after install regardless; a preserved wrapper may still
point at a retired runtime layout.

Legacy state such as `~/.dsh/`, `~/Library/Application Support/DSH Desktop`,
and `~/Library/Application Support/@deepseek-ai/dsh-desktop` must be preserved
during replacement. Never copy credentials, sessions, provider configuration,
or plugins into the desktop profile automatically. Migration requires a
separate inventory, compatibility review, dry-run, confirmation, and read-back.
The same-version, history-only procedure is defined in
[`references/deepseek-harness-operations.md`](../references/deepseek-harness-operations.md#history-migration-into-an-isolated-desktop-profile).
Provider, VL-router, and credential migration uses the separate field-level
procedure in
[`references/deepseek-harness-operations.md`](../references/deepseek-harness-operations.md#provider-and-vl-migration-into-an-isolated-desktop-profile).
Never replace the destination credential or settings file wholesale.

## Reviewed source

The current reviewed Apple Silicon release is `v0.7.1`:

```text
asset:  Deepseek.Harness.Desktop_0.7.1_aarch64.dmg
bytes:  6854317
sha256: e6f608d7fb66cdf27d7f7d361996c98134473944ffdf536a98e47bbad2fb4a01
bundle: io.github.hairyf.deepseek-harness-desktop
app:    Deepseek Harness Desktop.app
engine: dsh-web-app@0.1.0-rc.6.patch
```

The previously reviewed release was `v0.1.10`:

```text
asset:  Deepseek.Harness.Desktop_0.1.10_aarch64.dmg
bytes:  5671019
sha256: 645deba675e888b52601b023b244e1622c23deafc2ede16894ba301fe43097ac
```

This project releases very rapidly — 28 tags shipped between `v0.1.10` and
`v0.7.1` inside one week. Re-freeze the asset name, byte size, and SHA-256 from
release metadata every time; do not assume the pinned record here is still the
latest, and do not install an unreviewed newer tag without repeating the
signature and Gatekeeper review below.

No reviewed Homebrew Cask exists for this selected implementation. Do not
silently substitute a similarly named Cask or the separate `anywhere-labs`
application.

## Version-level blocklist

[`anywhere-labs/deepseek-harness-desktop` v2.0.0](https://github.com/anywhere-labs/deepseek-harness-desktop/releases/tag/v2.0.0)
is **blocked and must not be installed, upgraded to, or used as an automatic
fallback** by this skill. Live acceptance with the preserved profile exposed
incompatible plugin composition and unacceptable interactive performance.
Observed failures included duplicate Cordis loader entry IDs after migrated
Computer Use configuration and duplicate `deepseek-official` provider
registration from Polyglot.

This is a project-local compatibility and quality decision, not a claim that
the release or publisher is malicious. The block applies specifically to
`v2.0.0`; do not infer trust for another version. Reconsider only after a newer
release or plugin fix passes isolated-profile migration, plugin-by-plugin
activation, cold-start readiness, performance, explicit Quit/relaunch, and
rollback acceptance.

## First-launch plugin provisioning

First launch installs a fixed preinstall plugin set from third-party git URLs
without presenting a separate authorization step:

```text
git+https://github.com/hairyf/dsh-tauri.git
dshmarket
git+https://github.com/omdsh-dev/DSH-better-sidebar.git
git+https://github.com/omdsh-dev/dsh-notification.git
git+https://github.com/baihejiangnan/dsh-session-context-menu.git
```

Provisioning escalates on its own when a package requires a build. Observed on
`v0.7.1`, the shell rewrites `~/.dsh/profiles/web/pnpm-workspace.yaml` to add
`allowBuilds` entries and retries until the install succeeds — first for
`dsh-better-sidebar`, then for `node-pty`. **Approved package build scripts
therefore execute as a side effect of launching the app**, and the allowlist
persists in shared CLI state after the app quits.

Treat this as an authorization boundary, not a detail:

- Launching this shell is not equivalent to installing only the reviewed DMG.
  The plugin set, its transitive dependencies, and its build scripts are
  additional supply-chain surface that the frozen release hash does not cover.
- Review the current preinstall list against the release before first launch;
  it is defined by the shell version, not by user configuration.
- Record the resulting `allowBuilds` entries in machine-local state, and
  reconcile them whenever the shell version changes.
- Never present a clean first-launch log as evidence that no third-party code
  was fetched or built.

## Signature and Gatekeeper boundary

Every reviewed release so far is ad-hoc signed, has no Developer ID Team or
stapled notarization ticket, and fails strict code-signature validation because
its resource envelope is malformed:

```text
codesign --verify --deep --strict  ->  "code has no resources but signature
                                        indicates they must be present"
Signature=adhoc, linker-signed      TeamIdentifier=not set
stapler validate                    ->  no ticket stapled
```

This is a supply-chain defect even if the DMG hash matches GitHub metadata. It
is **unfixed across the whole reviewed range** — identical findings on `v0.1.10`
and on `v0.7.1` seven minor versions later — so treat it as the project's
standing posture rather than a one-release regression, and re-check it on every
upgrade instead of assuming it was eventually corrected.

Downloading the DMG with a non-quarantining client (`curl`, `wget`, an API
fetch) leaves no `com.apple.quarantine` attribute, so the app launches with no
Gatekeeper confirmation at all. That is a weaker posture than a browser
download, not a fix. Verify the attribute explicitly rather than inferring the
gate from whether a prompt appeared, and say plainly when the confirmation step
was absent.

Never automate `xattr -dr com.apple.quarantine`, disable Gatekeeper, or describe
either action as a normal fix. Prefer a corrected signed/notarized release or a
locally reviewed source build. If the user explicitly accepts the current
artifact, keep the decision separate from installation and leave any macOS
security confirmation to the user.

## Installation

1. Freeze the exact repository, release, asset name, size, and SHA-256.
2. Download to a temporary private path and verify the local SHA-256.
3. Mount the DMG read-only. Require exactly one expected app bundle and verify
   version, bundle identifier, executable architecture, signature, Gatekeeper,
   and notarization status. Stop on any unexplained mismatch.
4. Preserve all previous app bundles and support data. Copy the new app to
   `/Applications/Deepseek Harness Desktop.app` only after the security review.
5. Launch normally. Do not pass quarantine-changing flags. Wait for the first
   runtime download to finish.
6. Verify the visible window, the supervised Harness process, loopback HTTP,
   logs, explicit Quit, and relaunch.
7. Measure warm-idle CPU and RSS at least three times. Retire the prior bundle
   only after the new implementation is materially better and functionally
   complete. Move it to Trash first; permanent purge is a separate action.

The release shell can update or replace its downloaded Harness package. Record
both shell and engine versions in machine-local evidence and recheck plugin
compatibility whenever either changes.

## Verification

```sh
test -d "/Applications/Deepseek Harness Desktop.app"
defaults read "/Applications/Deepseek Harness Desktop.app/Contents/Info" CFBundleShortVersionString
defaults read "/Applications/Deepseek Harness Desktop.app/Contents/Info" CFBundleIdentifier
file "/Applications/Deepseek Harness Desktop.app/Contents/MacOS/deepseek-harness-desktop"
codesign --verify --deep --strict --verbose=2 "/Applications/Deepseek Harness Desktop.app"
spctl --assess --type execute --verbose=4 "/Applications/Deepseek Harness Desktop.app"
```

Runtime acceptance additionally requires:

- one expected Tauri process and one supervised Harness/Node process;
- HTTP 200 from the configured loopback endpoint;
- no fatal error in the runtime log;
- explicit Quit stops the supervised process;
- relaunch restores a usable first window;
- no unapproved import from legacy state;
- `dsh --version` succeeds independently if the global CLI is required;
- `~/.dsh/profiles/web/pnpm-workspace.yaml` reviewed for `allowBuilds` entries
  the shell added during provisioning;
- `~/.local/bin/dsh` and `~/.local/bin/pnpm` still resolve to the intended
  targets after the shell's shim pass.

Do not treat a successful window launch as proof of code-signing integrity,
provider login, plugin compatibility, or global CLI availability.

## Global CLI

Homebrew's `dsh` is the unrelated Dancer's shell. The global Harness command is
a separately managed wrapper at `~/.local/bin/dsh`. After the desktop runtime
layout changes, back up the wrapper, repoint only its package entry, verify
`dsh --version`, and keep the default CLI state at `~/.dsh/` unless the user
explicitly requests another `DSH_HOME`.

## Rollback

Before permanent cleanup, rollback is bundle-level and reversible:

1. quit the new shell and supervised Host;
2. restore the previous app bundle from Trash;
3. restore the timestamped global CLI wrapper if needed;
4. retain both old and new support directories for diagnosis.

Never delete Keychain items, `~/.dsh`, isolated desktop data, provider secrets,
plugins, or sessions as part of rollback. Runtime operations knowledge lives in
[`references/deepseek-harness-operations.md`](../references/deepseek-harness-operations.md).
Current versions, paths, measurements, and install evidence belong only in
machine-local state.
