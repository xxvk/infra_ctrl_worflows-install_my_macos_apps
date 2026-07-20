# TODO

- [x] Capacities data migration: user confirmed the migration/retention
      decision is complete and Capacities has been deleted. Do not delete any
      remaining preserved support data during a generic app scan.
- [x] After user confirmation, remove only `/Applications/Capacities.app` and
      preserve Capacities support data for a separate cleanup decision.
- [x] Run the read-only Capacities migration preflight and record candidate data
      locations, sizes, file counts, and extensions without reading document
      contents.
- [x] Implement a read-only `scripts/macos_permissions.py` inventory that
      records direct capability checks and writes only a dated
      `state/permissions-*.json`; TCC categories still require visible review.
- [x] Implement the read-only allowlisted export half of
      `scripts/macos_preferences.py`; applying and verifying each desired
      policy remains a separate follow-up task.
- [x] Add reviewed apply/verify handlers for `settings/system-preferences.yaml`;
      begin with Dock/Finder/appearance; keyboard and input sources remain
      device-specific and require their existing listener workflow.
- [x] Review the generated permission and preference baselines on this Mac,
      then promote only confirmed reusable policy—not raw machine state—into
      tracked settings. Confirmed policy remains limited to the existing
      `settings/system-preferences-values.json` allowlist and Dock/keyboard
      policy; no TCC grant is portable, so `settings/privacy.yaml` remains a
      requirements-and-manual-authorization policy only.
- [x] Grant Apple Events access to the terminal/skill host if a complete GUI
      Login Items inventory is required; then rerun the preference baseline.
      Resolved: the current skill execution host successfully queried System
      Events and read `Google Drive` and `GeminiAppLauncher`; the refreshed
      baseline now distinguishes GUI Login Items from LaunchAgents.
- [x] Review malformed `~/Library/LaunchAgents/com.local.keyremap.plist`; it
      appears to be an older keyboard mapping and may overlap with the K240
      listener. Preserve a backup before any user-approved cleanup.
      Resolved: the malformed XML was a stray backslash before `>` in the
      DOCTYPE line. Content was an unrelated JIS-keyboard `hidutil`
      UserKeyMapping (not the K240 receiver), already `not running`. User
      confirmed it is no longer needed; backed up to
      `~/Library/LaunchAgents/backups/` and disabled via the existing
      `.plist.disabled` rename convention.

## Full application permission and authorization inventory

- [x] Expand `scripts/macos_permissions.py` to inventory every detected app
      bundle from `/Applications`, `~/Applications`, system applications,
      WebCatalog apps, and PlayCover apps. CLI/helper applications, login
      items, background tasks, system extensions, VPN/network extensions, and
      privileged helper tools remain follow-up sources.
- [x] Add read-only discovery for Homebrew formulae/casks, LaunchAgents,
      LaunchDaemons, privileged helper tools, system extensions, network
      services, VPN connections, and background-task output. CLI identity
      mapping and per-component ownership review remain follow-up work.
- [x] Re-run System Extension discovery in an approved administrator context
      if the complete extension inventory is required; preserve the current
      OSSystemExtensionError instead of treating it as an empty result.
      Resolved: macOS administrator authorization returned `0 extension(s)`;
      the raw observation is in ignored `state/`.
- [x] Re-run Background Task Management discovery with visible administrator
      authorization if those records are required; do not automate elevation.
      Resolved: macOS administrator authorization returned real records for
      ZeroTier, SmartDNS, AdGuard VPN, Docker, Logi Options+, OrbStack,
      Google, Claude, Slack, TRAE, Tailscale, and other current/system items;
      the raw observation is in ignored `state/`.
- [x] Classify the current unmatched TCC clients into current helpers, system
      components, current identity variants, and legacy/unlisted items; keep
      genuinely unknown clients in `manual_review`.
- [x] For each application, record reusable identification and current
      evidence: name, bundle identifier, version, path, code-signing
      identifier/team, source, detected entitlement keys, requested permission
      category hints, observed authorization status, evidence method, and
      checked timestamp. Entitlement values are not persisted.
- [x] Cover the complete permission category matrix: Full Disk Access;
      Accessibility; Input Monitoring; Screen Recording; Automation/Apple
      Events; Files and Folders; Removable Volumes; Desktop/Documents;
      Downloads; Network Volumes; Camera; Microphone; Speech Recognition;
      Contacts; Calendars; Reminders; Photos; Bluetooth; Location Services;
      Motion & Fitness; and any additional category exposed by the current
      macOS release. Resolved: added `permission_category_matrix` to
      `settings/privacy.yaml`, including TCC categories, protected-folder
      subcategories, Developer Tools, and capability-only network access;
      added Location and Reminders service-name mappings to the scanner.
- [x] Separate three states instead of guessing: `verified_granted`,
      `verified_denied`, and `manual_verification_required`. macOS may not
      expose a supported read API for every TCC category, so an inaccessible
      TCC database must never become a false denial or grant.
- [x] Read the current system TCC database in read-only mode when macOS allows
      it, attach real per-service records to matching application bundle IDs,
      and preserve `no_record` as distinct from `verified_denied`.
- [x] Generate an App × observed-TCC-service matrix. Missing rows remain
      `no_record`; they are not converted into a false denial.
- [x] Reconcile entitlement permission hints with actual TCC records, keeping
      “requested without record” separate from “requested and denied”.
- [x] Add a machine-initialization permission summary grouped by service,
      denied/granted application, unmatched client count, and cleanup candidate.
- [x] Use `not_scanned` while a permission service has not yet been checked;
      never use `manual_verification_required` as a placeholder for missing
      implementation.
- [x] Add entitlement/code-signature inspection as capability evidence, but
      never treat a declared entitlement as proof that the user authorized it.
- [x] Record protected application access requirements for known workflows:
      Chrome profile audit, ChatGPT/Computer Use, K240 listener, Solaar,
      PlayCover, VPN clients, browser extensions, and developer tools in
      `settings/privacy.yaml`.
- [x] Add a report that groups missing or manually unverified permissions by
      application and by bootstrap phase, with a System Settings path and a
      concrete verification action for each item.
- [x] Keep all current application permission observations in ignored
      `state/permissions-*.json`; keep only reusable requirements and policy
      in tracked `settings/privacy.yaml`. Never copy the TCC database,
      credentials, tokens, MDM secrets, or private document contents.
- [x] Test the inventory on this M4B, review false positives, and define the
      new-Mac authorization checklist before adding any apply automation. The
      current host cannot read TCC, so all five sensitive categories remain
      `manual_verification_required` until a visible authorization and workflow
      test is completed.

## Complete system-preference and user-workstyle baseline

- [x] Capture the first preference slice with explicit allowlists for
      language/region, calendar, measurement units, 24-hour setting, input
      sources, architecture, memory, and storage capacity/free space. These
      are observed baseline values; applying locale/input changes remains
      separate.
- [x] Extend the preference allowlist to modifier keys, function-key behavior,
      text-input automation, dictation, and keyboard shortcuts. Text
      substitution contents are redacted; only counts and safe metadata are
      captured.
- [x] Capture Dock, Finder, desktop/window management, Mission Control/Spaces,
      Stage Manager, and screenshot preferences. Private screenshot paths are
      redacted.
- [x] Capture notification authorization summaries and Control Center/menu
      bar visibility/position settings without notification contents or Focus
      rule details.
- [x] Capture Focus/DND database presence and screen-lock/screensaver policy
      fields while keeping Focus rules and private schedules redacted.
- [ ] Capture sound input/output, display scaling, refresh rate, Night Shift,
      True Tone, sleep, battery, and remaining power policies.
      Partial observation: sleep/power policy, battery power source, audio
      device metadata, and interface-limited Night Shift/display effects are
      captured; current macOS execution context still does not expose actual
      volume, physical display resolution, refresh rate, or True Tone state.
- [x] Record display controller identity and explicitly preserve unavailable
      Night Shift/windowserver interfaces as interface-limited observations.
- [x] Capture audio input/output device metadata without recording content or
      storing device serial numbers.
- [x] Parse battery/AC sleep, display-off, hibernate, wake, and power
      management parameters into structured machine-local profiles.
- [ ] Capture current display identity/resolution, sound volume/mute state,
      and power-management output as machine-local observations without
      storing serial numbers.
- [x] Capture default applications and file/URL associations for browser,
      mail, terminal, editor, images, video, PDF, archives, SSH, Git, and
      common development file types. Store bundle identifiers, not volatile
      application paths.
      Resolved: expanded `launchservices_profile()` in
      `scripts/macos_preferences.py` into named categories (browser, mail,
      images, video, pdf, archives, ssh, editor_text) with explicit
      `system_default_no_override` status when macOS has no LSHandler
      override, plus a separate `custom_url_scheme_handlers` list (60 on this
      Mac) capturing every vendor-registered URL scheme and its bundle
      identifier. `terminal` and `git` have no LaunchServices content-type or
      URL-scheme surface and are recorded as intentionally excluded rather
      than missing.
- [x] Add a read-only LaunchServices association slice for common file types
      and URL schemes; broader associations remain to be reviewed because
      this Mac currently exposes only a partial handler set.
- [x] Capture login items, user LaunchAgents, system/background tasks,
      shell startup files, PATH/toolchain initialization, Homebrew taps,
      formulae/casks, Git identity/config policy, SSH config shape, and
      developer runtimes. Exclude private keys, tokens, host secrets, and
      machine-specific paths.
      Resolved: `scripts/macos_startup_items.py scan` covers login items (2),
      user LaunchAgents (4), and background tasks (76) in one dated
      `state/startup-items-*.json` record; `developer_environment_profile` in
      `scripts/macos_preferences.py` already covers shell/PATH/SSH-config
      shape/Git config keys/CLI runtime versions. Added `taps` (via
      `brew tap`) alongside existing `formulae`/`casks` in
      `non_app_components.homebrew` (`scripts/macos_permissions.py`) to close
      the one remaining gap. No private keys, tokens, or secrets are read.
- [x] Capture Shell/startup-file shape, PATH size, Git config key names,
      SSH config metadata, and available CLI versions without collecting
      identities, file contents, private keys, or tokens.
- [x] Capture network behavior needed for bootstrap: active interfaces,
      preferred DNS split policy, proxies, VPN/Tailscale/ZeroTier intent,
      firewall/Gatekeeper/FileVault posture, and SmartDNS configuration. Keep
      Wi-Fi passwords, VPN credentials, certificates, and private keys out of
      the repository. Resolved: administrator-authorized read-only baseline
      captured Ethernet/Thunderbolt Bridge/Wi-Fi/Tailscale services, local
      SmartDNS `127.0.0.1`, no HTTP/HTTPS/SOCKS proxy, disconnected Tailscale,
      VPN-client presence, SmartDNS running, Gatekeeper enabled, Firewall
      disabled, SIP enabled, FileVault Off, and no MDM enrollment.
- [x] Capture network service names, per-service DNS observations, proxy/VPN
      summaries, and presence of the tracked SmartDNS policy without storing
      credentials, certificates, private keys, or live address data.
- [x] Capture read-only Gatekeeper, Firewall, FileVault, SIP, MDM enrollment,
      and VPN-client presence status without changing security posture or
      collecting keys/certificates.
- [x] Capture Chrome profile names and email matching for continuity. Email
      is the identity key; profile directory numbers are machine-local.
- [x] Capture Chrome extension IDs/names/versions, Safari Web Clipper presence,
      and WebCatalog/PlayCover directory presence. Never export cookies,
      passwords, tokens, or browsing history.
- [ ] Capture reliable Chrome extension enabled state; the current Secure
      Preferences source exposes `null` for this field.
- [x] Capture default-browser routing and safe app-specific WebCatalog/PlayCover
      settings through read-only checks. Current state includes WebCatalog
      wrappers Notion/X and PlayCover settings for YouTube; browser sessions,
      Keychain data, app containers, and account state remain excluded.
- [x] Capture selected app-specific workstyle policies already documented by
      this skill: K240 mappings, Solaar usage, Claude Developer Mode, PlayCover
      YouTube settings, SmartDNS routing, Dock order, and startup listeners.
      Resolved: added `settings/app-workstyle.yaml` with safe portable fields,
      read/apply/verify contracts, and explicit exclusions for accounts,
      sessions, Keychain, app containers, IPA files, and device telemetry.
- [x] Define a portable-vs-machine-local classification for every preference:
      tracked desired policy, ignored current observation, interactive manual
      step, or deliberately excluded secret/private data.
- [x] Add `--check` drift reporting before adding more apply handlers. Each
      preference must have read, apply, verify, and rollback behavior; do not
      implement a blanket `defaults import`.
- [x] Run the expanded baseline on this M4B, review it manually, and promote
      only confirmed user preferences into tracked `settings/`. Keep raw
      snapshots in ignored `state/preferences-*.json`. Remaining unchecked
      preference items are intentionally unresolved or machine-specific.

## System-app preference persistence audit

These are candidate settings for the built-in macOS apps. Each item must first
be read-only inventoried on this Mac, then classified as portable policy,
machine-local observation, manual setup, or deliberately excluded. Do not
export account credentials, message/note/event contents, cookies, private
paths, or library databases.

- [x] Contacts: persist global person-name presentation preferences
      (`NSPersonNameDefaultDisplayNameOrder` and
      `NSPersonNameDefaultShortNameFormat`) separately from Person's
      `givenName`/`familyName` fields. Added to the preference allowlist and
      tracked desired values; iPhone display-order settings remain separate.
- [x] Calendar: inventory safe default-calendar policy, time-zone/display
      preferences, calendar visibility, declined-event display, travel
      advisories, and view range. The current profile uses the last selected
      calendar as default and shows the Monthly view in Asia/Tokyo. Account or
      calendar identifiers, event data, and alert database contents remain
      excluded; week-start/work-week and alert defaults need a separate
      documented read method.
- [x] Reminders: inventory the available preference domains for default
      list/account policy, list sort/group, and completed-item display. The
      current domains expose no safe portable scalar policy beyond
      machine-local window state; do not copy Reminders databases or account
      data. Revisit only if Apple exposes a documented preference API.
- [x] Mail: inventory safe composer/viewer/thread/sort policy and favorite
      mailbox behavior without exporting accounts, mailbox identifiers,
      messages, search terms, signatures, tokens, or private paths. Current
      account selection and signature content remain manual setup; alert
      defaults need a separate documented read method.
- [x] Safari: inventory safe startup/search/reader/sidebar/developer and
      extension policy without reading history, cookies, passwords, bookmarks
      contents, tab groups, website permissions, extension storage, or private
      download paths. Current Safari uses Apple's start page and Google search;
      extension enabled-state and download policy remain separate follow-ups.
- [x] Finder: extend the baseline for sidebar visibility, desktop disk icons,
      iCloud Desktop/Documents visibility, extension visibility, spring-loaded
      folders, and Trash policy. Recent items, search scopes, mounted-volume
      positions, tag contents, private paths, and window coordinates remain
      excluded; default folder view details remain a separate follow-up.
- [x] Notes: inventory safe account/folder/sort/display candidates and locked
      note behavior without reading note content, titles, attachments,
      account identifiers, or sharing metadata. The only portable scalar found
      is checklist auto-sort (currently disabled); account/folder policy is
      manual and Notes database data remains excluded.
- [x] Messages: inventory safe junk/request filtering, retention, attachment
      retention, and conversation-list Focus policy without reading message
      content, participants, attachments, transcript databases, or account
      identifiers. Notification/read-preview defaults need a separate
      documented read method.
- [x] Photos: inventory safe library/display policy, grid columns, zoom,
      launch-library chooser, and shared-library presence without exporting
      library paths, iCloud accounts, photo content, thumbnails, albums, faces,
      locations, or shared-library content. Library selection and iCloud sync
      remain manual setup on a new Mac.
- [x] Music/TV/Podcasts: inventory safe playback/download policy. Current
      domains expose only limited playback/download fields; library paths,
      purchase/account state, and media metadata remain excluded.
- [x] Preview/Quick Look/TextEdit: inventory high-value document-view fields.
      Preview exposes safe sidebar/alignment fields; TextEdit and Quick Look
      expose no safe scalar policy in the current allowlist. Recent files,
      document contents, paths, and window geometry remain excluded.
- [x] Shortcuts and Automator: inventory layout/automation presence only.
      Shortcut actions, names, counts, and private automation data are not
      exported; no safe Automator scalar policy was found.
- [x] App Store and Software Update: inventory safe UI/update-policy fields.
      The current domains expose no portable automatic-update policy; Apple ID,
      purchases, receipts, update identifiers, and account state remain excluded.
- [x] Add a generic, reviewed system-app preference inventory report that
      compares the allowlisted domains against tracked policy and keeps raw
      observations in ignored `state/`.
      See `references/system-app-preferences-audit.md`.

## Cross-machine bootstrap readiness

- [x] Add one documented read-only bootstrap entry point that runs baseline scan,
      Homebrew/app installation, permission checklist, preference apply, and
      final verification in dependency order. The current first phase runs
      scan/plan/inventory/check only; mutating phases remain gated separately.
- [x] Add a tracked-definition validation that proves tracked `settings/`
      and `references/` are sufficient without depending on this Mac's
      ignored `state/`; full install simulation remains environment-dependent.
- [x] Add account/license/manual-action checkpoints for App Store, browser
      profiles, VPNs, developer tools, and protected permissions without
      storing credentials or tokens in `settings/manual-actions.yaml`.
- [x] Add final drift and recovery reporting so a second Mac can be compared
      with the baseline and failed steps can be rerun safely through
      `scripts/bootstrap_verify.py`.

## CTO gap-audit backlog (2026-07-19)

A read-only audit of `settings/`, `references/`, `scripts/`, and
`components/README.md` against the "one-sync, ready-to-use Mac" mission
found domains with no file or script touching them at all. Logged here for
review before promoting any item into an implementation task.

### Must-do (real gaps against the existing mission, low risk, high value)

- [x] Write one end-to-end disaster-recovery runbook that chains scan →
      install → TCC/preference restore → verify into a single "Mac lost or
      wiped" sequence. Today only separate script entry points exist; no
      single document walks the full recovery path.
      Resolved: added [`references/disaster-recovery-runbook.md`](references/disaster-recovery-runbook.md),
      an 8-step sequence (pre-loss snapshot → repo retrieval → network →
      read-only scan → account/secrets-manager setup → app install → TCC/
      preference restore → device-specific config → final verify) that
      references existing scripts/docs by path rather than duplicating
      their content, plus a short "recovery incomplete" troubleshooting note.
- [x] Add a read-only Time Machine / backup precondition check before any
      destructive-adjacent script (Docker Desktop retirement, Capacities
      cleanup, TCC reset) runs. Warn if no valid backup is detected instead
      of silently proceeding. No script or settings file currently touches
      backups at all.
      Resolved: added `scripts/backup_precondition_check.py` (read-only;
      checks `tmutil destinationinfo`/`latestbackup`, warns if no
      destination, no completed backup, or the latest backup is older than
      35 days — matched to the user's ~monthly cadence). It explicitly notes
      iCloud file sync is not a full-system backup substitute. Wired as an
      advisory-only warning (never a hard block) into `docker_desktop_cleanup.py
      remove`, `capacities_cleanup.py --apply`, and
      `macos_permissions_cleanup.py --apply`; each script's own existing
      confirmation token/prompt remains the sole gate.
- [x] Define a dotfiles reproduction mechanism. `developer_environment_profile`
      only records shell startup file shape (byte counts/hashes), not how to
      actually restore those configs on a new Mac. Needs a reusable dotfiles
      repo + symlink strategy as the closing step of dev-environment bootstrap.
      Resolved: added `dotfiles/` (tracked source of truth, mirroring `$HOME`
      under `dotfiles/home/<relative-path>`, see `dotfiles/README.md` for the
      manual-review-before-tracking convention) and
      `scripts/dotfiles_sync.py` (`status` read-only preview, `link --apply`
      symlinks tracked files into `$HOME`, backing up any pre-existing
      non-symlink destination first). No user dotfiles are seeded yet — the
      user confirmed no existing dotfiles repo and no current tracked
      content, by design, to avoid committing unreviewed secrets from the
      live `~/.zshrc`/`~/.ssh/config`; population is a separate, deliberate
      per-file step.
- [x] Define an SSH/GPG key provisioning strategy. SSH config shape is
      captured (never key contents); GPG is not mentioned anywhere. Needs a
      documented "generate new key vs. import from key manager" procedure and
      verification step, never storing key material in the repo.
      Resolved: added [`references/ssh-gpg-provisioning.md`](references/ssh-gpg-provisioning.md),
      documentation-only (no script, no key material). Records that this Mac
      uses per-project `.pem` files outside `~/.ssh/` rather than a default
      identity, and has no GPG installed/used. Defines: retrieval procedure
      for project `.pem` keys on a new Mac, a `ssh-keygen` + `ssh-add
      --apple-use-keychain` procedure if a default identity is ever needed
      (matched to the user's declared system/iCloud Keychain secrets
      manager), an opt-in-only GPG commit-signing procedure, and a
      verification checklist.
- [x] Declare the authoritative password/secrets manager. `manual-actions.yaml`
      already implies manual sign-in flows everywhere but never states which
      manager (1Password/Keychain/etc.) is the source of truth, nor how
      access is restored on a new Mac.
      Resolved: added a `secrets_manager` block to
      `settings/manual-actions.yaml` declaring the macOS system/iCloud
      Keychain as the authoritative source (user confirmed no third-party
      manager is in use), with a `new_mac_recovery_steps` list, plus a new
      `secrets-manager-availability` checkpoint (phase: bootstrap) that
      every other sign-in checkpoint in the file now implicitly depends on.
      `scripts/bootstrap_validate.py` still passes (128 catalog apps, no
      missing required files).
- [x] Schedule the existing `--check` drift detection. `macos_preferences.py
      --check` and `bootstrap_verify.py` are both manually triggered today.
      Add an optional user-level LaunchAgent that runs a read-only drift
      check periodically (e.g. weekly) and writes to `state/`.
      Resolved: added `templates/drift-check.launchagent.plist` (weekly,
      Monday 09:00, `RunAtLoad: false`) and `scripts/drift_check_schedule.py`
      (`status` read-only, `install --apply`/`uninstall --apply`, both
      dry-run by default) following the same never-implicit-install
      convention as the existing K240 LaunchAgent. The agent only re-runs
      the skill's own existing read-only `--check`/`bootstrap_verify.py`
      commands and logs output; it changes nothing itself. Rendered plist
      validated with `plutil -lint` (a `&&` in the shell command needed
      XML-escaping — caught before install, not after).
- [x] Add a sandboxed dry-run mechanism for the full bootstrap.
      `bootstrap_validate.py` only checks internal consistency of tracked
      definitions; there is no way to actually exercise the full bootstrap
      against a fresh local admin account or VM without touching the
      production account.
      Resolved: added
      [`references/bootstrap-sandbox-dry-run.md`](references/bootstrap-sandbox-dry-run.md),
      documentation-only (user has no existing sandbox environment; no
      script/VM was set up). Documents three levels: (1) every mutating
      script's own default dry-run mode, already usable with zero setup;
      (2) a throwaway local admin account, with an explicit note on what it
      does and doesn't isolate (per-account state yes, `/Applications` and
      Homebrew no); (3) a full macOS VM via UTM/Tart for genuinely testing
      `--apply` code paths end to end. Includes a "dry run passed" checklist.
- [x] Define an uninstall/rollback plan for the skill's own footprint.
      Docker, Capacities, and TCC entries each have retirement workflows, but
      nothing enumerates what this skill itself has installed (K240
      LaunchAgent, binaries, backup files) if the user wants to abandon the
      whole bootstrap approach.
      Resolved: added `scripts/skill_footprint_inventory.py` (read-only;
      lists both known LaunchAgents, the Application Support/bin directory,
      the Logs directory, and any deployed dotfiles symlinks, with
      existence/size/loaded checks) and `scripts/skill_uninstall.py`
      (dry-run by default; `--apply` unloads LaunchAgents and moves them
      plus the support directory to timestamped `.removed-*` backups rather
      than deleting outright; logs are kept unless `--remove-logs` is
      passed; the repository itself is explicitly never deleted). Verified
      read-only against this Mac's real state: found the K240 LaunchAgent
      genuinely `loaded`, confirmed dry-run left it untouched.
- [x] Record this session's FDA host-process finding in
      `settings/privacy.yaml` as a named requirement: when this skill runs
      inside a Claude desktop local-agent/Cowork session, the process tree's
      host app is `Claude.app`, not Terminal.app or iTerm — granting Full
      Disk Access to a terminal app has no effect for that execution context.
      Resolved: added an `execution_host_note` under `permissions.
      full_disk_access` and a new `claude-desktop-local-agent-execution-host`
      entry under `workflow_requirements`, both documenting the
      `ps -p $$ -o pid,ppid,comm` parent-chain-walking verification method
      used to actually diagnose this during this session.
- [x] Add a Wi-Fi/network-connectivity bootstrap checkpoint as the very first
      manual-action item. `network_profile` only records service names/DNS/
      proxy/VPN presence after the fact; joining Wi-Fi on a genuinely new Mac
      is never recorded as a checkpoint, even though nothing else in the
      bootstrap (App Store, Homebrew, account sign-in) works without it.
      Resolved: added `wifi-network-connectivity` as the first checkpoint in
      `settings/manual-actions.yaml` (phase: bootstrap, ahead of
      `secrets-manager-availability`), and cross-linked it from Step 2 of
      `references/disaster-recovery-runbook.md`. `bootstrap_validate.py`
      still passes.

### Optional (valuable, lower priority than the must-do list)

- [x] Font management: custom font inventory and installation is not covered
      anywhere.
      Resolved: added `settings/fonts.yaml` (tracked desired-font list) and
      `scripts/macos_fonts.py` (read-only scan across `~/Library/Fonts`,
      `/Library/Fonts`, and system font directories). Running it found a
      real gap: JetBrains Mono is referenced by `~/.config/ghostty/config`'s
      `font-family` but is not actually installed on this Mac -- Ghostty has
      been silently falling back to a substitute font. Installing it
      (`brew install --cask font-jetbrains-mono`) is left as a separate,
      explicit step, not automated by this script.
- [x] Printer/scanner setup: not covered.
      Resolved: added `scripts/macos_printers.py` (read-only; `lpstat -p`/
      `lpstat -d`/`system_profiler SPPrintersDataType` scan, writes only a
      dated `state/printers-*.json`). Deliberately no tracked `settings/`
      file: unlike fonts or Dock order, a printer list reflects
      network/USB devices identified by LAN IP, which is a machine-local
      observation, not portable cross-machine policy, per this skill's
      existing tracked-vs-observed classification.
- [x] Write an iCloud-vs-skill boundary document clarifying what's already
      handled by iCloud sync (Photos, Notes, Safari bookmarks, etc.) versus
      what this skill must handle explicitly, to avoid duplicated effort.
      Resolved: added [`references/icloud-vs-skill-boundary.md`](references/icloud-vs-skill-boundary.md),
      documentation-only. Also calls out one real overlap worth flagging:
      this repository's files sync via iCloud Drive while its Git history
      does not, so concurrent editing across two Macs on both channels at
      once can conflict -- something no script here detects or resolves.
- [x] Capture menu bar app inventory and Notification Center widget layout.
      `notification_profile` only records authorization status today, not
      menu bar icon order or Today View widgets.
      Resolved: found `control_center_profile()` in `scripts/macos_preferences.py`
      already captures Control-Center-routed menu bar item visibility/order
      (Wi-Fi, Bluetooth, Focus, Display, Clock, etc.). Extended it with a
      `today_view_widget_count` (count only, since widget instances are
      opaque NSKeyedArchiver blobs not safely decodable) and an explicit
      `scope_note` documenting that third-party apps drawing their own
      NSStatusItem outside Control Center are not enumerable read-only from
      any single `defaults` domain. `--check` still reports 0 mismatches.
- [x] Define a browser bookmark migration strategy. Chrome profile matching
      exists, but bookmarks themselves (excluding passwords/history) have no
      scripted migration path today; manual only.
      Resolved: added [`references/browser-bookmark-migration.md`](references/browser-bookmark-migration.md),
      documentation-only by deliberate choice (Chrome Sync is the default
      path; manual export/import via `chrome://bookmarks` is the fallback
      when Sync is off for a profile). No script reads bookmark
      titles/URLs -- confirmed the per-profile `Bookmarks` JSON file exists
      across all seven tracked profiles on this Mac, but content stays
      untouched, consistent with this skill's existing browser-data policy.
- [x] Define a multi-Mac continuous sync strategy. The current design is
      "bootstrap one new Mac against the baseline," with no handling for
      keeping several Macs converged over time after initial bootstrap.
      Resolved: added [`references/multi-mac-continuous-sync.md`](references/multi-mac-continuous-sync.md),
      documentation-only. Clarifies that iCloud Drive already propagates
      tracked *files* across Macs automatically, but never their *effect*
      -- each Mac must still run its own `--check`/`--apply` (now automatable
      weekly via the item-6 drift-check LaunchAgent). Also lists which
      tracked values are legitimately per-Mac and should not be forced to
      converge (K240 profile, capacity-tier app selection).
- [x] Add a license-key reminder checklist. `manual-actions.yaml` explicitly
      forbids storing license keys, but there is also no checklist of which
      apps require manual activation, making it easy to miss one.
      Resolved: added `settings/license-reminders.yaml`, manually curated
      (confirmed the app catalog's source fields do not reliably indicate
      paid-vs-free status -- e.g. Notion/Zoom are official_url-sourced but
      free, Affinity is brew_cask-sourced but requires a paid license -- so
      no auto-derivation was attempted). Seeded with Affinity. Cross-linked
      from the `developer-licenses` checkpoint in
      `settings/manual-actions.yaml`. `bootstrap_validate.py` still passes.
- [x] Document a FileVault enable + recovery-key escrow procedure. Disk
      encryption is currently only read-only observed, with no "how to
      enable and safely escrow the recovery key" workflow.
      Resolved: added [`references/filevault-enable-and-recovery-key.md`](references/filevault-enable-and-recovery-key.md),
      documentation-only, consistent with the existing Gatekeeper-policy
      pattern in SKILL.md (explicit user action, visible Terminal for sudo,
      never automated). Found FileVault is currently **Off** on this Mac
      (`fdesetup status`, 2026-07-19) -- a real finding, not changed by this
      task. Documents both the Apple-Account-escrow path (recommended) and
      the manual-recovery-key path, and is explicit that no script here
      ever generates, displays, or stores the recovery key.
- [x] Add CI/lint checks across the growing script and catalog set (128+
      catalog entries, a dozen-plus Python scripts) to catch malformed
      files before they land — similar in spirit to the stray-backslash
      corruption found and fixed in `com.local.keyremap.plist` this session.
      Resolved in two parts: (1) `tests/smoke.sh` already extended (backlog
      item 6 follow-up) to `py_compile` every `scripts/*.py` file and
      `plutil -lint` every LaunchAgent plist template, including rendered
      output; (2) added `.github/workflows/smoke.yml` running that same
      script on `macos-latest` for push/PR/manual dispatch, since this
      submodule has a real GitHub remote
      (`xxvk/infra_ctrl_worflows-install_my_macos_apps`). The workflow is
      untested against actual GitHub Actions infrastructure -- it has not
      been pushed, only locally reviewed -- since commits/pushes are the
      user's own action per this skill's Safety rules.
- [x] Add a JSON Schema validation script for `references/app-catalog.json`
      (required fields, source consistency) as the catalog grows past 128
      entries, to prevent manual-edit data corruption.
      Resolved: added `scripts/validate_app_catalog.py` (hand-rolled, no
      jsonschema dependency; checks required fields, valid `tier` values,
      duplicate names, guide-file existence, at-least-one-source presence,
      and `app_store_url` shape) and wired it into `tests/smoke.sh`. Running
      it immediately found a real bug: 7 entries (LM Studio, Cherry Studio,
      Logi Options+, Solaar, Capacities, Foxglove, PlayCover Learning Apps)
      had `"tier": "option"` instead of `"optional"` -- confirmed via
      `scripts/macos_apps.py`/`audit_core_catalog.py` that only `tier ==
      "core"`/`"heavy"` are ever checked exactly, so this typo caused no
      runtime misbehavior, but was still a genuine schema violation. Fixed
      with a precise 7-line `sed` substitution (not a full JSON re-dump,
      which would have reformatted the entire 1974-line file). Validator now
      reports 0 errors across all 128 entries; `bootstrap_validate.py` still
      passes.
