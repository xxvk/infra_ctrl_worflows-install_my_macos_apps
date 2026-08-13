# Application installation workflow

Load this reference only when the current task uses this domain. Its rules were moved verbatim from the original skill entry point during RC-05.

## Contents

- Workflow
- App Store workflow
- Documentation churn policy
- Component frontmatter integrity

## Workflow

1. Inspect the current Mac and write a dated scan:

   ```sh
   python3 scripts/macos_apps.py scan
   ```

   The scan records source evidence for catalog apps. An App Store receipt is
   checked at `Contents/_MASReceipt/receipt`; Homebrew casks are checked against
   `brew list --cask`; other bundles are reported as `manual_or_unknown`. A
   source mismatch is a review item, not proof of malicious software. A cask
   receipt alone is not proof that a usable `.app` bundle exists: some casks
   install a privileged vendor installer and place the real app under a system
   support directory until reboot. The final check must find the expected app
   bundle (or the component's documented post-reboot service) and launch/verify
   it; do not close a missing-app item merely because `brew list --cask` lists it.

2. Create a plan. Use `auto` unless the user explicitly selects a capacity tier:

   ```sh
   python3 scripts/macos_apps.py plan --profile auto
   ```

   Omitting `--roles` defaults to `auto`: active Core applications plus the
   capacity role (`compact` below 512 GB, `expanded` at 512 GB or above).
   Optional applications enter a plan only through an explicit role or
   `--include-app`; the planner does not default to all active Optional items.

   `portable` applies below 512 GB; `expanded` applies at 512 GB or above. The planner includes `core` apps in both tiers, while apps marked `heavy` are excluded from `portable` by default. Large games and other entertainment packages should remain outside the compact-memory Mac profile; install them only on a separately designated expanded-memory gaming machine.

3. Review the plan with the user. Select one or two apps only. Identify required free space, account/permission tasks, and any source that is not Homebrew. Do not run installations before confirmation.

   Homebrew CLI-only entries marked as approved recommendations may be
   installed in batches of up to five after one confirmation. GUI applications,
   App Store applications, official website downloads, and any item requiring
   account or permission decisions remain strictly one at a time.

   Review `source_mismatches` before installing. For example, Slack and Telegram
   are cataloged as `app_store`; if their bundles have no App Store receipt, tell
   the user they appear to come from a website or another installer and offer a
   reinstall from the App Store. Never delete or replace the existing bundle
   automatically. The user must explicitly approve any reinstall and decide
   whether to remove the old copy first.

   **Perplexity source rule:** Perplexity is website-only. If a detected bundle
   contains `Contents/_MASReceipt/receipt`, it is a legacy Mac App Store build
   and must be removed **before** downloading or installing the website build.
   This is an explicit source-replacement exception to the general
   “never-delete-during-scan” rule. After removal, install and verify the
   website bundle (version, Bundle ID, launch, and permissions). Delete only
   the old App bundle; never delete Perplexity support data or login state.

   **X source rule:** X is WebCatalog-only. Native and Mac App Store X bundles
   are rejected even when they launch. Create and verify the `https://x.com/`
   WebCatalog wrapper under `~/Applications/WebCatalog Apps/`; only after that
   verification may the user approve removal of `/Applications/X.app`. Never
   remove browser or account data during this source replacement.

   **Notion source rule:** Notion is WebCatalog-only. Reject native, Homebrew,
   and Mac App Store Notion bundles even when they launch. Create and verify
   the `https://www.notion.so/` WebCatalog wrapper under `~/Applications/WebCatalog Apps/`,
   then move the old `/Applications/Notion.app` to Trash. The old native
   Notion app's support data, caches, containers, and offline data are
   disposable under this user's baseline and should be removed after the
   WebCatalog replacement is verified. Do not delete browser profiles or
   unrelated WebCatalog data.

   **X/Notion cleanup rule:** For either WebCatalog source replacement, app
   bundles, app-specific support data, caches, containers, and offline data for
   the retired copy are disposable and must be removed after the replacement
   is verified. Measure and record them in machine-local state; never remove browser
   profiles or unrelated application data.

   **Privileged Homebrew cask rule (Logi Options+ and similar installers):**
   Some Homebrew casks are installer wrappers rather than drag-and-drop `.app`
   bundles. Run them from a visible Terminal when the installer requests
   administrator authorization; Codex must not collect or persist the password.
   If an old bundle is owned by `root:admin`, stop and hand off to the user for
   the visible `sudo` password prompt before removing it. After installation,
   inspect the expected app path and vendor support/service path, then reboot
   when the cask caveat requires it. Only after reboot run `scan` and `plan`
   again. A completed Homebrew transaction with no app bundle is an incomplete
   installation, not a successful source repair. Record the cask version,
   reboot requirement, and post-reboot scan in machine-local state; never store
   the password or raw privileged logs.

   **Logi Options+ residue rule:** After Logi Options+ has installed and passed
   its post-reboot check, `/Applications/logioptionsplus_installer.app` is
   removable installer residue. Keep `logioptionsplus.app`,
   `Utilities/LogiPluginService.app`, the Driver Installer bundle, and Logi
   support directories; they are runtime components. Record the removed path
   and measured size in machine-local state.

4. Execute only after explicit approval. Start with a dry run, then apply the recorded plan:

   ```sh
   STATE_DIR="$(python3 scripts/state_paths.py path)"
   python3 scripts/macos_apps.py install "$STATE_DIR/PLAN.json" --only "App Name"
   python3 scripts/macos_apps.py install "$STATE_DIR/PLAN.json" --only "App Name" --apply

   Components marked `retired_pending_cleanup` remain installed while the
   user completes data export or migration. Do not delete their app, support
   data, or caches during a generic scan; require a separate explicit cleanup
   request after the data handoff is verified.
   ```

   The script accepts at most two `--only` values per run. It bootstraps Homebrew only with `--apply` and asks interactively first. It installs only catalog entries with a verified Homebrew cask or formula identifier. It never supplies credentials, modifies privacy settings, or silently installs an unverified DMG/PKG.

   **Homebrew dependency-upgrade guard:** Homebrew may otherwise upgrade an
   existing formula while installing a new one. This skill's installer invokes
   `brew install` with `HOMEBREW_NO_AUTO_UPDATE=1` and
   `HOMEBREW_NO_INSTALL_UPGRADE=1`, so an install does not silently upgrade
   unrelated packages such as an existing FFmpeg. Before an apply, record
   relevant installed versions; if the transaction still needs a dependency
   upgrade, stop and present the old/new versions, reason, download size, and
   disk impact for confirmation. Run that upgrade separately only after
   approval. Do not use a global same-major-version assumption. Read
   [homebrew-install-policy.md](homebrew-install-policy.md)
   for the detailed policy and temporary pin guidance.

   **IPATool authentication and IPA workflow:** IPATool is a Core Homebrew
   formula, but it is not a prerequisite for PlayCover. M4a and M4b verified
   that its Apple account/authentication workflow is not usable for the
   required IPA packages. Install it only as a general developer utility with
   `brew install ipatool` and verify with
   `ipatool --version`. Before downloading an App Store package, identify the
   intended App Store purchase account; the current iCloud account is only a
   candidate because iCloud and App Store purchase accounts may differ. Start
   `ipatool auth login --email "<APPLE_ID>"` from a visible Terminal so the
   user can enter the password and six-digit two-factor code. Never collect,
   display, log, or persist these secrets in Markdown, machine-local state, Obsidian, or
   Git. Verify with `ipatool auth info`; the CLI does not provide a native
   macOS Passkey/Touch ID login prompt. For YouTube, search/download using
   bundle ID `com.google.ios.youtube`. IPATool downloads an App Store package
   that may be encrypted; it is not automatically a PlayCover-compatible IPA
   and must not gate the YouTube workflow.
   PlayCover requires a decrypted IPA, so do not claim success until import
   and launch are tested. Keep the downloaded IPA and authentication result in
   ignored machine-local state only, and use `ipatool auth revoke` when the
   account should no longer remain authenticated. See
   [../components/ipatool.md](../components/ipatool.md).

   **YouTube through PlayCover:** treat YouTube as a separate Core capability
   installed after PlayCover. Use only the approved decrypted-IPA source label
   from `Private/app-catalog-overlay.json`; do not persist a version-specific
   direct IPA URL in the catalog. For the validated YouTube 21.28.3 profile,
   after importing, open the app's Settings → Misc and explicitly click
   **Remove PlayTools**; PlayCover may install PlayTools automatically during
   import, but it must be removed before the first launch.
   PlayTools must remain removed. Keep PlayChain off, Jailbreak Bypass on,
   Introspection libraries off, and Force Insert iOS Frameworks on. Use the
   iPad Pro 13-inch (7th generation) M4 8 GB device profile, 1080p, 4:3, and
   Resolution Scaler 2.0. If YouTube crashes with `PlayKeychain.copyMatching`,
   `igdrms`, or a PlayTools frame in the crash report, do not change DNS,
   Full Disk Access, or SIP; first verify that PlayTools was not reinjected.
   See [../components/youtube-playcover.md](../components/youtube-playcover.md).
   **Login persistence limitation:** PlayChain was tested for this validated
   YouTube installation but did not reliably preserve the login session, while
   PlayTools cannot be reintroduced because it causes the tested build to crash
   during PlayKeychain/DRM initialization. The supported workflow is to expect
   a fresh YouTube login after the app is fully quit and reopened. Do not keep
   changing PlayTools/PlayChain or delete Keychain entries and PlayCover data
   automatically; persistent login is a future compatibility investigation.

   **Claude pre-install storage gate:** before installing or replacing Claude,
   run `python3 scripts/claude_vm_cleanup.py inspect`. The VM review and any
   cleanup are separate actions from the Claude installation. **Analyze Disk is
   mandatory completion work for every Claude install or replacement:** if
   `claudevm.bundle` exists, report its total size and obtain explicit approval
   to remove the complete bundle with `remove-bundle --confirm "REMOVE CLAUDE VM BUNDLE"`.
   Only after the user explicitly confirms, and only after Claude is fully quit, may the skill
   run `remove --confirm "REMOVE CLAUDE VM IMAGES"` or the complete-bundle removal.
   Optional directory locking
   is a second confirmation using `lock --confirm "LOCK CLAUDE VM DIRECTORY"`;
   it disables Cowork/local-agent VM recreation and is never implicit. See
   [../components/claude.md](../components/claude.md).

   **Claude Desktop Developer settings:** after Claude Desktop opens and the
   intended account is verified, automatically inspect the Help menu. If it
   shows `Help → Troubleshooting → Enable Developer Mode`, the skill must click
   that menu item, accept the app's non-binding warning, and wait for Claude to
   restart. This is a local application preference and does not enter
   credentials or change macOS privacy permissions. Verify that the top-level
   `Developer` menu appears; if it already shows `Disable Developer Mode`, the
   check passes. Then inspect `Developer → Configure Third-party Inference…`.
   Verify required Local MCP servers separately. Never
   enter, display, log, or sync API keys through the skill, and never store them
   in the catalog, machine-local state, Obsidian, or Git. If the build exposes the
   third-party inference page, the user may manually configure the Gateway base
   URL, credential kind, custom headers, model discovery, and model list. Test
   each provider with a non-sensitive prompt and record only provider name,
   endpoint type, model name, and pass/fail. If the menu is absent, mark the
   feature blocked and report the build version. Use the GUI for this workflow;
   do not edit Claude's local configuration files directly.

   **Claude Desktop model compatibility guard:** a Gateway endpoint being
   Anthropic-protocol-compatible does not mean the Desktop model list accepts
   the provider's native model IDs. Current builds validate model entries as
   Anthropic-family routes. In particular, adding an OpenRouter ID such as
   `deepseek/deepseek-v4-pro` can produce the warning `Doesn't look like an
   Anthropic model` and can leave Claude Desktop in a `provider setup needs a
   fix` state after relaunch. Before applying a non-Anthropic model, run the
   real GUI validation; if that warning appears, remove the entry, save and
   apply the restored list, relaunch, and verify the setup warning is gone.
   Do not treat community alias/proxy workarounds as native support. Use
   Claude Code CLI, OpenCode, or a separately tested Anthropic-compatible
   proxy/router for DeepSeek instead.

   Claude Desktop's model-list editor is not a general OpenRouter model
   switcher. It validates entries as Anthropic-family gateway routes. A
   non-Anthropic OpenRouter ID such as `deepseek/deepseek-v4-pro` can be
   accepted by the form but leave the provider setup malformed after relaunch.
   Before applying any manual entry, check the validation message; if it says
   the route is not an Anthropic model, discard/remove the entry, save and
   apply the restored list, relaunch Claude, and verify that the setup warning
   is gone. Use a separate tested Anthropic-compatible router/client when a
   non-Anthropic model is required.

   **Restore the original Claude subscription:** Developer Mode may remain
   enabled; it is independent of the inference mode. When Claude Desktop is
   in `Gateway` / 3P mode and the user wants the original Claude subscription,
   use the current Gateway account menu's `Sign out`/`Logout` action. After
   Claude relaunches, sign in again at `claude.ai` with the original Claude
   account. Verify the URL is `claude.ai/new`, the Gateway indicator is gone,
   and the model picker shows the subscription model. Do not remove Developer
   Mode as part of this switch. If sign-out does not restore the login flow,
   stop before deleting local state and report that 3P recovery requires a
   backed-up state reset.

   **LM Studio and multi-provider Gateway settings:** LM Studio is a local
   model server, not a general-purpose cloud API key proxy. Its current
   official server supports OpenAI-compatible endpoints and
   Anthropic-compatible `/v1/messages`; use it as a local backend for models
   loaded into LM Studio. Do not assume that a DeepSeek official API key can
   be stored in LM Studio and transparently forwarded to
   `api.deepseek.com`. For OpenRouter, DeepSeek, Google, and LM Studio behind
   one Claude Desktop Gateway, use a separate routing layer such as a tested
   Anthropic-compatible router, and keep provider keys in that router's secret
   store rather than in the catalog or component guides. Test model discovery,
   tool calls, streaming, and the exact model ID separately; compatibility at
   the HTTP endpoint does not guarantee agent compatibility.

   **LM Studio Bionic:** Bionic is the active `core` application for this Mac
   for code, documents, voice, and open-model agent workflows. Verify the
   official Bionic download page and macOS build before installing; do not
   substitute an unofficial similarly named download. Classic LM Studio is
   retired in this catalog. Bionic and classic LM Studio use the same `llmster`
   daemon, so do not run both local backends concurrently. Preserve shared
   model data unless the user explicitly requests cleanup.

   After installing Bionic, rename the application bundle in `/Applications`
   to `LM Bionic.app` for local organization. Do not change the bundle
   identifier or internal metadata. Open the renamed app once and verify launch
   success before marking installation complete.

   If classic LM Studio is installed, treat it as `retirement_pending`: quit
   both applications, verify Bionic's local/cloud workflows, then remove only
   the classic app bundle if requested. Do not delete `~/.lmstudio` as part of
   routine retirement.

   **Bionic capability verification:** treat the current Bionic build as an
   initial preview and verify these surfaces after installation:

   - Work Projects: research, writing, analysis, document editing, and
     generation of documents, presentations, spreadsheets, and other files in
     a managed workspace.
   - Code Projects: a selected local working directory with file search,
     code explanation, edits, Git visibility, shell tools, test execution, and
     documentation updates.
   - Sessions and tabs: separate task conversations, background sessions,
     side-by-side sessions, project files, and response forking.
   - Model routing: local models, remote models through LM Link, and hosted
     open models through LM Studio Secure Cloud.
   - Local model management: discover/download models and use models that fit
     the Mac's available memory and runtime support.
   - Web Search: optional fresh web context for Work Projects; verify that
     billing is enabled before treating it as available.
   - Account and billing: local and LM Link models do not require an account;
     Secure Cloud models require sign-in, credits, and network access.

   Record whether each test used local, remote, or cloud inference. Never
   assume that a feature works with every model: check tool support, image
   input, reasoning controls, streaming, and filesystem/shell permissions.

## App Store workflow

Use this workflow for every catalog entry with `app_store_url`. It is the
default deployment method for a personal user with several Macs; Apple
Configurator is not a Mac application deployment tool in this workflow.

1. Confirm that the target Mac is signed in to the same Apple Account used for
   the user's App Store purchases. Never enter the account password, approve
   two-factor authentication, or accept a purchase on the user's behalf.
2. Open the catalog's App Store URL, verify that the page offers a Mac build,
   and check the user's Purchased list if the direct page is unavailable. A
   page that lists only iPhone/iPad/Apple TV is not a valid Mac installation
   source, even if the app has the same name.
3. The skill must actively open the catalog's App Store URL for the user,
   one application at a time, inside the native App Store whenever possible.
   Do not send a normal `https://apps.apple.com/...` link to the default
   browser as the first attempt: that commonly opens a web page without
   handing off to App Store. Use this escalation order:

   ```sh
   open -a "App Store" "<app_store_url>"
   open "macappstore://itunes.apple.com/app/id< numeric_app_id >"
   ```

   The second form is a deep-link fallback constructed only from the numeric
   App Store ID already present in the catalog URL. Confirm that the foreground
   window is App Store and that the product title matches before proceeding.
   Only if both native routes fail may the skill open the HTTPS page in a
   browser, and it must record that fallback in `completion_notes`. The user
   must not be asked to search for or open the page manually. Search for the
   exact app if needed, select `Mac Apps`, and report whether the button says
   `Get`, `Download`, `Redownload`, `Update`, or `Open`. Stop immediately
   before any `Get`/`Download`/`Redownload` action and ask for confirmation.
   After the user confirms, the skill may click that button, but the user must
   complete any Apple Account password, Touch ID, purchase, or two-factor
   prompt. App Store installation must not be automated with Apple
   Configurator, undocumented store APIs, or credential entry.
4. After installation, open the app and confirm its first window. Re-run
   `scan` and verify the App Store evidence: the traditional
   `Contents/_MASReceipt/receipt`, or for some Mac Catalyst/wrapper packages
   `Wrapper/iTunesMetadata.plist`. Record version and any sign-in, license,
   notification, microphone, camera, VPN, or accessibility follow-up tasks.
   If replacing a direct-download copy with an App Store copy, do not assume
   that its login session will migrate: signing, sandbox containers, and
   Keychain access groups can differ even when the Bundle ID is identical.
   Have the user sign in to the new copy and verify the required workspace
   before retiring the old bundle.
5. If the App Store page is unavailable, not Mac-compatible, region-restricted,
   or the app is absent from Purchased, mark the item as `store_unavailable`
   in the plan and offer the catalog's official website or Web App only when
   that alternative is explicitly recorded. Do not silently substitute a
   website download for an App Store-required entry.

Apple Configurator may remain in the catalog for iPhone, iPad, and Apple TV
backup, restore, supervision, and preparation. It must not be used as the
normal way to install Mac apps or to bypass Apple Account authorization.

5. Open each just-installed GUI app and confirm that it reaches its first window without a crash or macOS security warning. Then complete the plan's `follow_up` tasks and re-run `scan`. Add completed account, license, permission, or configuration notes to the plan's `completion_notes`; never store passwords, API keys, recovery codes, or license secrets.

   When the merged catalog entry has `preferred_account`, prompt the user to
   verify that account in the app before proceeding. Resolve the account from
   `Private/app-catalog-overlay.json`; do not duplicate personal identifiers in
   this public procedure. Never automate account selection or login. Open the
   app's account/avatar menu and read the displayed email, then record only
   `account_verified: true/false` and the verification date. If the displayed
   account differs, stop and ask the user whether to switch accounts; never
   click Log out, change accounts, or enter credentials automatically.

   When an entry has `minimum_version`, treat it as a lower bound for every
   future install. The planner reports an installed app below that bound in
   `version_issues`; do not downgrade an app or silently replace it.

   Installation logs record download bytes and installed bytes separately for each Homebrew item. A cached or resumed download may report the final artifact size rather than bytes transferred during the current attempt.

   For Ghostty, after the app is installed, create or update `~/.config/ghostty/config` with the skill defaults below, preserving unrelated user settings:

   ```ini
   theme = Cyberpunk Scarlet Protocol
   font-family = JetBrains Mono
   font-size = 20
   ```

   Treat this as a post-install configuration step, not part of the Homebrew installation. Verify the theme name with `ghostty +list-themes --plain` and open Ghostty once after writing the config.

6. For a first install or a material deployment change, create or update the
   matching `components/<component_id>.md`, add or update its row in
   `components/README.md`, and ensure the catalog entry has the relative
   `guide` path. Material changes include a changed delivery source, changed
   installation or verification procedure, new permission/configuration
   requirement, changed account/license workflow, or changed lifecycle status.
   Routine reinstalls, upgrades, and repeated scans should write evidence to
   machine-local state records without rewriting the guide merely to refresh a version,
   timestamp, formatting, or unchanged measurement. For every uninstall or
   removal, update that guide's reusable `lifecycle_status: retired`, document
   what was removed and what data was preserved, and keep machine-specific
   evidence in the machine-local state record.
   A component operation is complete when catalog, guide, and state evidence
   are synchronized at the appropriate level of change.

   **Effective SmartDNS requirement:** SmartDNS is opt-in, not the default DNS
   path. Keep the Homebrew service stopped after installation and configure the
   active macOS network service with resilient public DNS (`1.1.1.1` and
   `8.8.8.8`) by default. Only after explicit user approval for China-network
   access may the skill start SmartDNS and switch DNS to its local listeners
   (`127.0.0.1` and `::1` when both are bound). Flush the macOS resolver cache,
   verify `scutil --dns`, and run a real `dig` query after either switch. Record
   the previous DNS servers, changed service, listener addresses, service
   status, and rollback command in the machine-local state record. If SmartDNS or
   its local listener is unavailable, automatically restore the public DNS
   pair and stop the service; never leave macOS pointed at an unavailable
   `127.0.0.1` resolver across reboot.

   **Shell environment requirement:** When a component needs `PATH`,
   `JAVA_HOME`, `ANDROID_HOME`, `ANDROID_SDK_ROOT`, or a manager initializer,
   installation is incomplete until the environment is configured in the
   user's active shell startup file. Detect the active shell and prefer
   `~/.zshrc` for zsh or `~/.bashrc`/`~/.bash_profile` for bash. Preserve
   unrelated content, create a timestamped backup before editing an existing
   file, and add an idempotent clearly labelled block only when the lines are
   absent. Start a fresh login shell, verify `command -v` plus version output,
   and write the exact file, variables, and verification results to machine-local state.
   Never overwrite shell files, duplicate initialization blocks, or place
   credentials in them. PATH changes that point into a vendor app bundle or
   `/usr/local/bin` still require separate explicit confirmation.

   Every Core installation must record delivery and storage measurements in the
   machine-local install record: `download_bytes` (actual bytes transferred),
   `installed_bytes` (measured footprint), `installed_version`, and
   `installed_at`. The catalog's `size_gb` remains an estimate used for
   planning and must never be presented as the measured footprint. Component
   Markdown contains no current-machine installation measurements. Audit the
   complete Core set with:

   ```sh
   python3 scripts/audit_core_catalog.py
   ```

   Estimate download size in this order: (a) a cached Homebrew artifact or
   vendor-provided installer size, (b) the Mac App Store listing size for a
   verified Mac build, (c) a vendor download page/API, and only then (d) the
   catalog `size_gb` planning estimate. Label the method and timestamp; never
   present an estimate as transferred bytes. After first installation or a
   material packaging change, measure the actual bundle or Homebrew prefix with
   `du` and record it in the dated state installation log. Do not rewrite an
   unchanged guide on every routine upgrade; preserve detailed version and byte
   evidence only in the state installation log.

## Documentation churn policy

The skill is deployment-oriented, not a live changelog generator. Before
editing a component Markdown file, confirm that the source, procedure,
verification, permissions, configuration, lifecycle status, or operating
knowledge changed. If not, leave the Markdown file untouched and record only
the operation in machine-local state. Do not run enrichment or normalization scripts as a
routine post-install step when they would rewrite unchanged guides.

## Component frontmatter integrity

Every generated or catalog-linked `components/*.md` file must contain the
complete frontmatter contract from `templates/app-component.md`, including
`component_id`, `name`, `category`, `tier`, `lifecycle_status`, `source`,
`delivery_method`, source identifiers, account/permission fields, and
`secrets_policy`. Missing values must be explicit `null`, `[]`, or `false`; never
omit a template field and never use a placeholder such as `X`.

Machine-specific observations do not belong in component Markdown: do not
persist `status: installed`, installed version/size/timestamps, or verification
results there. Write those observations to machine-local scan, plan, and
install records. `lifecycle_status` describes the reusable catalog lifecycle,
not whether this Mac currently has the component installed.

After creating or materially rewriting guides, run:

```sh
python3 scripts/audit_component_frontmatter.py
```

The audit must pass for every catalog-linked guide and every other Markdown
file under `components/` except `README.md`. A failed audit blocks the
workflow until the frontmatter is repaired. Routine scans and upgrades must
not rewrite frontmatter or body text.
