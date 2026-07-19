# TODO

- [ ] Capacities data migration: if any export or verification remains, finish
      it before deleting the preserved Capacities support data. Review those
      paths separately; do not delete them during a generic app scan.
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
- [ ] Run the first permission and preference baseline on this Mac, review it,
      and commit only reusable policy—not raw machine state.
- [ ] Grant Apple Events access to the terminal/skill host if a complete GUI
      Login Items inventory is required; then rerun the preference baseline.
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
- [ ] Re-run System Extension discovery in an approved administrator context
      if the complete extension inventory is required; preserve the current
      OSSystemExtensionError instead of treating it as an empty result.
- [ ] Re-run Background Task Management discovery with visible administrator
      authorization if those records are required; do not automate elevation.
- [x] Classify the current unmatched TCC clients into current helpers, system
      components, current identity variants, and legacy/unlisted items; keep
      genuinely unknown clients in `manual_review`.
- [x] For each application, record reusable identification and current
      evidence: name, bundle identifier, version, path, code-signing
      identifier/team, source, detected entitlement keys, requested permission
      category hints, observed authorization status, evidence method, and
      checked timestamp. Entitlement values are not persisted.
- [ ] Cover the complete permission category matrix: Full Disk Access;
      Accessibility; Input Monitoring; Screen Recording; Automation/Apple
      Events; Files and Folders; Removable Volumes; Desktop/Documents;
      Downloads; Network Volumes; Camera; Microphone; Speech Recognition;
      Contacts; Calendars; Reminders; Photos; Bluetooth; Location Services;
      Motion & Fitness; and any additional category exposed by the current
      macOS release.
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
- [ ] Test the inventory on this M4B, review false positives, then define the
      new-Mac authorization checklist before adding any apply automation.

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
- [ ] Capture network behavior needed for bootstrap: active interfaces,
      preferred DNS split policy, proxies, VPN/Tailscale/ZeroTier intent,
      firewall/Gatekeeper/FileVault posture, and SmartDNS configuration. Keep
      Wi-Fi passwords, VPN credentials, certificates, and private keys out of
      the repository.
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
- [ ] Capture default browser and app-specific WebCatalog/PlayCover settings
      through their documented checks.
- [ ] Capture selected app-specific workstyle policies already documented by
      this skill: K240 mappings, Solaar usage, Claude Developer Mode, PlayCover
      YouTube settings, SmartDNS routing, Dock order, and startup listeners.
- [x] Define a portable-vs-machine-local classification for every preference:
      tracked desired policy, ignored current observation, interactive manual
      step, or deliberately excluded secret/private data.
- [x] Add `--check` drift reporting before adding more apply handlers. Each
      preference must have read, apply, verify, and rollback behavior; do not
      implement a blanket `defaults import`.
- [ ] Run the expanded baseline on this M4B, review it manually, and promote
      only confirmed user preferences into tracked `settings/`. Keep raw
      snapshots in ignored `state/preferences-*.json`.

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
