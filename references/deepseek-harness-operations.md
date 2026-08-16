# DeepSeek Harness operations

Operational knowledge for DeepSeek Harness (`dsh web`) across the lightweight
Hairyf Tauri shell, the independently managed CLI, and preserved legacy
profiles: plugin composition, VL wiring, local OCR, MCP servers, CLI entry, and
agent presets. This is the knowledge companion to
[`components/deepseek-harness-desktop.md`](../components/deepseek-harness-desktop.md)
(which covers installation) and
[`browser-workflow-cli.md`](browser-workflow-cli.md) (Safari bookmark CRUD).

> Scope rule: this file is portable knowledge. Current machine state — exact
> plugin versions, paths, installed models, permissions, credentials — belongs
> in `~/.dsh/` machine-local state, never here. Secrets never enter this
> repository.

## CLI global entry

`dsh` is the stable global entry (`~/.local/bin/dsh` wrapper, uses fnm-managed
Node to run the CLI downloaded by the Hairyf desktop shell below
`~/Library/Application Support/io.github.hairyf.deepseek-harness-desktop/dependencies/dsh/`).
Homebrew's `dsh` is the unrelated **Dancer's shell** — never confuse the two.
`DSH_BIN` overrides the CLI path. Verify with `dsh --version`.

The Hairyf shell downloads `@deepseek-ai/dsh` separately instead of embedding
it in the app bundle. Because that runtime can change independently, record
both versions and update the wrapper only after its entry path is verified.
Brace `${DSH_BIN}` when adjacent to non-ASCII punctuation in shell messages;
an unbraced `$DSH_BIN（...` may be parsed as a different variable under a
Unicode locale and fail with `unbound variable`.

Wrapper rationale: `~/.local/bin` is first on `PATH` via `.zshenv`, so both
interactive and non-interactive zsh (Codex/script) see `dsh`; Node resolves
from fnm v24 (the developer baseline), not the TRAE-bundled Node. The wrapper
intentionally does not set `DSH_HOME`, so the CLI keeps using `~/.dsh` instead
of the desktop shell's isolated state. Restore on a new machine: launch the
desktop shell once to provision its runtime, recreate the short wrapper, ensure
fnm+Node 24, and verify with `dsh --version`. Use
`dsh --profile web --dump-config` only after reviewing the preserved plugins.

## Desktop runtime separation

The Hairyf app starts the web profile with a private `DSH_HOME` below
`~/Library/Application Support/io.github.hairyf.deepseek-harness-desktop/data/dsh`.
Its dependencies and logs are siblings under the same app-support root. This
separation is deliberate: the desktop shell must not inherit `~/.dsh` plugins,
provider keys, sessions, or Cordis patches implicitly.

Treat desktop-shell version, downloaded Harness version, global CLI version,
and Profile state as four separate checks. Any migration from `~/.dsh` into the
isolated desktop profile requires an inventory, compatibility review, backup,
dry-run, explicit confirmation, and read-back. Never bulk-copy the directory.

## Blocked release and duplicate-loader recovery

The project blocklist rejects
[`anywhere-labs/deepseek-harness-desktop` v2.0.0](https://github.com/anywhere-labs/deepseek-harness-desktop/releases/tag/v2.0.0).
Do not install it, upgrade to it, or silently select it as a fallback. This is
a version-specific compatibility and performance decision, not a malware
finding. Keep any older or alternate bundle and its state available for
rollback until a replacement passes sustained acceptance.

When a Host reports `duplicate loader entry id`, identify the profile from the
actual Host process arguments before editing anything; the desktop shell may
boot the `web` profile even though the product is a desktop app. Then:

1. back up the complete active `DSH_HOME` and the exact active patch;
2. inspect the profile package's bundle list and the plugin-owned
   `cordis.patch.yml` before treating a user patch as authoritative;
3. remove only the redundant user insert when the package bundle already
   registers the same IDs; keep the plugin package and bundle dependency;
4. run `dsh --profile <actual-profile> --dump-config` and require each intended
   loader ID to appear exactly once;
5. cold-restart the shell, discover its dynamic loopback port, require HTTP
   200 and a normal main window, then Quit and relaunch once more.

For the reviewed Computer Use failure, `computer-use-host` and
`computer-use-tool` are package-owned IDs and must each compose exactly once.
For the separate v2.0.0 Polyglot failure, keep the package installed but
inactive when it attempts to register the already built-in
`deepseek-official` provider. Do not send a paid inference request merely to
validate loader recovery.

## History migration into an isolated desktop profile

The old Electron bundle is not migration data and must never be merged into a
Tauri app bundle. Electron `Cache`, `Cookies`, `Local Storage`, GPU caches, and
window state are implementation-specific and remain excluded. Durable Harness
history normally lives below `~/.dsh/`.

Use this bounded sequence when moving history into the Hairyf desktop profile:

1. Require the source and destination Harness engine versions to match exactly.
2. Quit the desktop shell and verify that both its supervisor and Host process
   have stopped.
3. Create an owner-only staging directory as a sibling of `data/`, not inside
   the active `DSH_HOME`. Copy `sessions`, `attachments`, `storages`, `profiles`,
   `settings.yaml`, and user scripts there with metadata and symlinks preserved.
4. Exclude `.credentials.yaml`, anonymous IDs, caches, and models. Models are
   large and independently reproducible; credentials require a separate
   user-controlled secret migration.
5. Verify staging with a checksum-based dry-run. Do not activate any directory
   whose destination already contains data.
6. When `sessions` and `attachments` are both absent at the destination, they
   may be copied together as one additive history unit. Keep `profiles`,
   `settings.yaml`, and `storages` staged: they can conflict with generated
   defaults or reintroduce an incompatible plugin such as an outdated router.
7. Relaunch and require loopback HTTP success, no fatal log entry, and a
   read-only UI session-tree enumeration. Do not open private session content
   merely to prove migration.

Session files alone appear under `未分组`. Preserve their project association by
restoring both `storages/workspace.json` and
`storages/session_projcache.json`. Before replacement, require every cache ID to
match exactly one migrated session ID, back up the destination's generated
workspace file, and keep `checkpoints.json` separate. Verification must show
the expected workspace count and grouped session tree, not merely the same
number of session files.

The staging copy is a rollback source, not an active profile. Preserve the
original `~/.dsh` until the user separately confirms profile/plugin migration
and sustained session read-back. Any later cleanup is an independent exact-path
transaction.

## Provider and VL migration into an isolated Desktop profile

Provider configuration is not inherited across `DSH_HOME` boundaries. A
working global CLI profile under `~/.dsh` therefore does not prove that the
Hairyf Desktop profile can see the same router, model, or credential. Treat the
plugin package, Cordis patch, settings namespaces, credential fields, and
default model selection as separate migration units.

Use this sequence for a provider or VL migration:

1. Inventory the source and destination without printing secret values. Record
   plugin IDs, provider/model IDs, settings namespace names, and credential key
   names only. For value comparison, use an in-process equality check or digest
   and emit only pass/fail; never place a key in command arguments, stdout,
   diagnostics, shell history, Git, or `Private/`.
2. Confirm that the destination engine can load the approved plugin version.
   For VL, require the `dsh-vision-router` package and its `vision-router`
   Cordis insert before migrating any provider selection. Package presence is
   not activation evidence; inspect the active patch and the runtime boot list.
3. Quit the Desktop shell and verify that both the Tauri supervisor and its
   supervised Node/Harness process have stopped. Back up the destination
   `settings.yaml` and `.credentials.yaml` with one timestamp and preserve
   owner-only mode `0600` on originals and backups.
4. Merge settings by namespace and credentials by exact field. Preserve every
   destination field not named in the approved migration. For the reviewed
   DashScope route, copy only `DASHSCOPE_API_KEY` from the source active
   `DSH_HOME/.credentials.yaml` into the destination
   `DSH_HOME/.credentials.yaml`; preserve `DEEPSEEK_API_KEY` and any unrelated
   destination keys. Never bulk-copy or replace `.credentials.yaml`.
5. Merge only required plugin-owned settings such as the `vision-router`
   namespace. Do not replace the complete `settings.yaml`, because locale,
   permissions, presets, theme, and model choices may have diverged in the new
   profile.
6. Launch the Desktop shell and wait for loopback HTTP readiness and complete
   plugin loading. Apply the desired default model through the running Harness
   model selector or its supported settings API. A pre-launch file edit alone
   is not acceptance evidence: the web client can write a newer in-memory
   selection back to `settings.yaml` during startup.
7. Verify the runtime model picker, not merely the patch text. The reviewed VL
   route should expose `Vision HTTP` with `aliyun/qwen3-vl-flash`; the router
   may additionally expose DeepSeek `Auto Vision` choices. Confirm that the UI
   selection and `agent-default-model` settings agree.
8. Quit and relaunch once more. Acceptance requires the selected model to
   survive restart, both expected credential key names to remain present, the
   migrated secret to compare equal without disclosure, credential/settings
   files to remain `0600`, loopback HTTP to return successfully, and no fatal
   provider/plugin error in the Host log.

Do not send a paid model request merely to prove that migration copied a key.
An external inference smoke test is a separate, explicitly approved action
because it transmits prompt data and may incur provider charges. Static and
restart acceptance prove configuration persistence, not account balance,
quota, or successful inference.

Rollback is file-scoped: quit the shell, restore the timestamp-matched
destination settings and credentials backups, preserve `0600`, restore the
previous patch if it changed, and relaunch. Never remove or rewrite the source
`~/.dsh` during this rollback.

## Staged plugin activation

Never activate the complete legacy patch at once. Copy packages without
overwriting packages supplied by the current runtime, then enable only the
user-approved IDs. Each batch requires `dump-config`, Host HTTP success, a
fully loaded main UI, preserved workspace grouping, no browser-console error,
and no fatal Host log. A package may be present but inactive; only the patch is
execution authority.

The lower-risk local batch may combine attachment limits, notifier with empty
channels, checkpoint-rewind, native-memory plus session-query SQLite, and a
locally reviewed backup plugin. Chrome/Drive MCP and vision-router may join
that batch only after explicit user approval because they expose logged-in or
external services. Their child process existing proves startup, not account or
tool-level authorization.

`ds-balance` can load successfully while its card remains `空闲` with pending
balance data until a new token-consuming request occurs. Judge it by whether
the main plugin loader and conversation UI complete; do not require its balance
route to return data before usage exists. Roll it back if it blocks the main UI.

Keep `dsh-computer-use` and model routers such as polyglot in a separate risky
batch. Computer Use requires the companion app and macOS privacy grants;
polyglot changes provider selection and must pass a current-runtime export and
fallback compatibility review before activation.

## Plugin composition (Cordis)

- `~/.dsh/profiles/web/cordis.patch.yml` is the web-profile plugin
  composition; `~/.dsh/settings.yaml` holds globals (locale, permission
  preset, default agent preset, model routing, theme).
- Installed plugins live in `~/.dsh/profiles/node_modules/`; enablement is the
  patch insert list.
- Cost plugins: `ds-balance` (generated from `tools/dsh/cost-crystal`),
  `ds-session-cost` (hand-written; backup retained as a component artifact).
- Known-good set (2026-08): balance card, Chrome/GDrive MCP, vision-router,
  attachment limits, native-memory, checkpoint-rewind, backup, notifier,
  polyglot model routing, computer-use (host + tool). Enablement changes over
  time — read the live patch.
- `dsh-computer-use` (companion app `DSH Computer Use`, optional catalog
  entry) drives a text-first browser and background control; the plugin rows
  `computer-use-host`/`computer-use-tool` must be present in the patch for it
  to work.
- `dsh-native-memory` needs the `session-query-sqlite` full-text search
  section (`openAt: first-search`, persistent path) to recall across sessions;
  both must be restored together on a new machine.
- `@dsh-polyglot/bundle` routes models with automatic fallback
  (`/model <chain>`); `deepseek-official` reuses `DEEPSEEK_API_KEY`, other
  presets are skipped unless their key is configured.
- `dsh-notifier` with `channels: []` subscribes without pushing (safe
  default); channel configuration is personal, not repository policy.
- Backup/checkpoint schedules and snapshot directories are machine-local
  behavior, initialized per machine from the plugin's own docs.

## VL capability (vision-router)

`dsh-vision-router` gives text models eyes: semantic understanding via Alibaba
DashScope `qwen3-vl-flash` (key env `DASHSCOPE_API_KEY`), plus pixel-level
`vision_*` tools (describe/ground/crop/pixel_diff/OCR/trace/cutout/screenshot).
Model selector shows a "+ Auto Vision" group. The key lives only in the active
`DSH_HOME/.credentials.yaml`: normally `~/.dsh/.credentials.yaml` for the
global CLI, but
`~/Library/Application Support/io.github.hairyf.deepseek-harness-desktop/data/dsh/.credentials.yaml`
for the Hairyf Desktop profile. These files do not inherit from each other;
use the field-level migration contract above when the user explicitly approves
copying the provider key.

## Local free LLM / OCR

`~/.dsh/scripts/xvk_ocr2.py` runs local OCR via LM Studio
(`http://127.0.0.1:1234/v1`) with DeepSeek-OCR-2 GGUF weights
(`~/.dsh/models/ocr2/`), free for text/table pages. Paid VL is used only for
image *semantics* after budget approval. Model assets are machine-local;
automatic cleanup must never delete them.

## MCP wiring

- chrome: `chrome-devtools-mcp` with `--autoConnect` reuses the daily Chrome
  profile login state; requires Full Disk Access and
  `chrome://inspect/#remote-debugging`.
- gdrive: Google Drive upload/metadata via the mcp-gdrive package.
- Both launch through `@deepseek-ai/dsh-mcp-client` (stdio) with a Node from
  the TRAE SOLO toolchain (machine-specific absolute path).

## Agent presets

Shipped presets (`code`/`minimal`/`standard`/`cordis`) live in the app bundle;
user presets go under `~/.dsh/.agent-presets/<id>/`. Never edit the shipped
install; copy a preset out and edit the copy. Default preset comes from
`settings.yaml` (`agent-presets.default`).

## Machine-local state (never in this repo)

Hairyf desktop state lives under
`~/Library/Application Support/io.github.hairyf.deepseek-harness-desktop` and
is isolated from the global CLI state under `~/.dsh/`. Preserve legacy Electron
data under `~/Library/Application Support/DSH Desktop` and
`~/Library/Application Support/@deepseek-ai/dsh-desktop` until any desired
Profile/session/provider migration passes read-back.

`~/.dsh/.credentials.yaml` (secrets, Keychain-class), `~/.dsh/models/`
(binary GGUF), `~/.dsh/storages/`, `~/.dsh/sessions/`, `~/.dsh/cache/` —
backup via the installed `dsh-backup` plugin, never via Git. Cross-device
sync of *knowledge* is this repo; cross-device sync of *configuration* is
the user's own machine/backup concern.
