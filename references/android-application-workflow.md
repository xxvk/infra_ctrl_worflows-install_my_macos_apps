# Android application workflow

Lifecycle rules for Android applications, parallel to the macOS application
workflow. The Android catalog is `references/android-app-catalog.json`
(schema `android-app-catalog-v1`); this reference covers inventory and install.

## Inventory (statistics)

- Enumerate the connected device inventory read-only:
  ```sh
  adb shell pm list packages
  adb shell pm list packages -3          # user-installed only
  adb shell dumpsys package <pkg>        # version/installer metadata
  ```
- The Android catalog is desired state; a package record is not proof that an
  app is usable or that accounts are authorized.

## Install (Play Store / APK)

- **Play Store (preferred):** use `apkeep` with a user-provided OAuth/AAS
  token (see [`apkeep.md`](../components/apkeep.md)). Never automate or store
  Google credentials/tokens.
  ```sh
  apkeep -a <play_store_package> -d google-play -e '<user@example.com>' -t <aas_token> .
  adb install --user 0 <app>.apk          # or split-APK install
  ```
- **Aurora Store token dispenser (know-how, verified 2026-08-21):** the
  anonymous dispenser at `https://auroraoss.com/api/auth` returns an
  `email` + `authToken` (`ya29...`) + `aasToken` pair without any personal
  account. POST the gplayapi device properties (e.g. `ad_g3_pro.properties`,
  flattened `key=value` as a JSON object) with header
  `User-Agent: com.aurora.store-4.8.4-76`:
  ```sh
  # response: {email, authToken, aasToken, ...}
  apkeep -a <play_store_package> -d google-play -e <dispenser-email> \
    --auth-token <ya29...> --accept-tos -o split_apk=true .
  ```
  Split APK install requires `-o split_apk=true` and `adb install-multiple`
  over the `<pkg>/` directory (base + `config.arm64_v8a` + `config.xxhdpi`).
- **F-Droid (open source):** `apkeep -d f-droid` verifies F-Droid signing.
- **Third-party mirrors (APKPure etc.):** evaluate signature/trust before
  use; never treat a mirror as Play Store provenance.
- **google-play channel silent-fail (know-how, verified 2026-08-21):** some
  apps exit 0 with an empty output dir on the google-play channel (observed:
  Google Meet, F-Droid, Threads). Detect with `find <pkg> -name '*.apk'`
  after download; fall back to `apkeep -d apk-pure` for those. APKPure may
  emit `.xapk` (zip of base + config splits) — unzip it and
  `adb install-multiple` the inner APKs.
- **Preinstalled system apps (know-how, verified 2026-08-21):** Pixel ships
  Chrome, Gmail, Calendar, Photos etc. (`/product/app/`). A Play install of a
  preinstalled app fails with `INSTALL_FAILED_UPDATE_INCOMPATIBLE` (signature
  mismatch) — check `pm list packages` first and keep the preinstalled copy
  instead of sideloading. Chrome additionally requires the
  `com.google.android.trichromelibrary` shared library, which is also
  preinstalled.
- **Region-locked apps (know-how, verified 2026-08-22):** the anonymous
  dispenser account is US-region. CN/JP-region financial/shopping apps
  (banks, points wallets, PASMO/Suica, CN video/social) silently fail on the
  google-play channel (exit 0, empty dir) and are often absent from APKPure.
  The correct fix is a region-matching Google account (JP or CN) in the
  device Play Store / Aurora Store, not more download retries.
  `jp.co.rakuten.link` has no standalone app on Pixel — Rakuten Link rides on
  `jp.co.rakuten.mobile.rcs` (RCS service, preinstalled).
- **Package-name verification (know-how, verified 2026-08-22):** Play Store
  HTTP 200 checks are unreliable (Cloudflare/UA blocking returns 404 for valid
  packages). Use `apkeep -l -a <pkg> -d google-play -e <email> --auth-token
  <token>` which hits the Play API directly. Also: several JP/CN apps use
  non-obvious packages (e.g. `jp.ponta.myponta`, `jp.co.sbisec.hyperkabu2`,
  `com.mojitec.mojidict`, `com.worldcoin`). When the user manually installs
  from the device Play Store, treat the device package name as authoritative
  and reconcile it into the catalog (`pm list packages | grep <fragment>`).
- Verify the target device serial before any install; never install to an
  unintended device.

## Catalog contract

Each `android-app-catalog.json` entry requires:

- `name`, `category`, `tier` (core/optional/retired)
- `play_store_package` (e.g. `com.tencent.mm`)
- `apk_source` (play_store/apk_pure/fdroid/github_release/vendor_download/
  manual_or_unknown) and optional `allowed_apk_sources`
- `guide` (component path, e.g. `components/android-guides/<app>.md`)
- Optional: supported ABIs, min Android version, size, account scope, follow-up,
  `login_required` (from the device login scan; see "Login-state scan" below)

**This repository is public.** The catalog records properties of the *app*, never
per-device account state. `login_required` ("does this app need an account at
all") is fine and mirrors `account_required` in the iOS and macOS catalogs.
Whether *this user* is signed in is personal information and lives only under
`Private/` -- the dated scan file, `android-inventory.json`'s `login_tracking`,
and `login-evidence.json`. A `login_status` field was carried in the catalog
until 2026-08-22 and was removed for this reason; `backfill_catalog()` now
strips it on sight.

**Ignore list:** apps the user explicitly declines for the Pixel (region
unavailable, product no longer wanted) are recorded in
`references/ignore-list.json` with `reason_category` (`china_region`,
`service_discontinued`, `not_selected`, `user_excluded`). They are *removed*
from the Android catalog rather than kept as `retired` — the catalog stays the
desired state, the ignore list is the rejection ledger. iOS-side equivalents
may stay in the iOS catalog (iOS installs are independent of the Pixel).

**Region variants (know-how, verified 2026-08-22):** several catalog apps ship
separate regional builds under *different package names*, and the one you get
from a generic search is often the wrong one. Confirmed case:

| Catalog name | US/wrong package | JP/device-correct package |
|---|---|---|
| メルカリ | `com.mercariapp.mercari` | `com.kouzoh.mercari` |

Tell them apart on-device without launching: `dumpsys package <pkg>` --
`installerPackageName=com.android.vending` means Play Store (vs `null` for a
side-load), and `pm path <pkg>` lists the split APKs, where `split_config.ja`
indicates the Japanese build. The iOS catalog hit the same Mercari trap
(`com.mercariapp.ios.mercari` vs `com.kouzoh.ios.mercari`); see the bundle-id
table in `references/ios-application-workflow.md`.

## Verification

- After install, verify by `adb shell pm list packages` read-back and a launch
  check on the device.
- Record unavailable interfaces as unavailable, never as success.

## Login-state scan (know-how, verified 2026-08-21; scripted 2026-08-22)

Determining whether an installed app is logged in, without per-app UI
automation:

- **Entry point:** `python3 scripts/android_login_scan.py scan` is the
  reusable implementation of the method below. It diffs
  `pm list packages -3` against the previous scan to find newly installed
  apps, classifies only what's new (`--recheck <pkg1,pkg2>` or
  `--recheck-all` to re-check known apps), writes a new dated
  `Private/android-login-scan-final-<date>.json`, back-fills
  `android-app-catalog.json`'s `login_required` (never `login_status` -- see
  "Catalog contract"), regenerates
  `Private/android-inventory.json`'s `login_tracking`, and regenerates a
  dated `Private/android-login-checklist-<date>.json` grouped by category.
  Use `--confirm-login <pkg1,pkg2>` after the user manually signs in to an
  app, and `--mark-no-login <pkg1,pkg2>` for apps confirmed not to need an
  account. The canonical status vocabulary is exactly `needs_login` /
  `logged_in` / `google_system` / `no_login` — do not invent new status
  strings; a package that genuinely can't be classified stays `needs_login`
  with an explanatory note (never a new status like "not_verified").
- **Method:** for each app, resolve its launcher activity
  (`cmd package resolve-activity --brief <pkg>`), `am force-stop`, press
  HOME, `am start -n <entry>`, wait ~7-12 s, then read the foreground
  activity from `dumpsys activity activities | grep topResumedActivity`.
- **Signal:** an activity whose class name contains
  `login|signin|auth|welcome|onboard|loggedout|firsttimeuse|registration|eula|signup`
  means the app is on a login/onboarding screen (not logged in). A
  `MainActivity`/`HomeActivity` is **not proof of login** — many apps render
  the main UI logged-out (e.g. ChatGPT, Claude, Discord, Mercari, PayPay);
  user confirmed these count as "needs login" for full use.
- **Interference:** serial scans only (parallel launches fight for the
  foreground); repeated 3-sample checks improve capture; a NOTFRONT result
  leaks the *next* app in the task stack, not the target. Google apps
  (`com.google.android.*`) follow the system account and are excluded from
  per-app login tracking.
- **Screenshot disambiguation (know-how, verified 2026-08-22):** when
  `topResumedActivity` is a bare `MainActivity`/`HomeActivity`, the activity
  name alone cannot decide. Capture the screen instead:
  `adb exec-out screencap -p > shot.png`, then read it. This resolved 9 apps
  that the activity-name method had misfiled as "possibly logged in"
  (Tailscale, Termius, Notion, Mercari, 小红书, 知乎, Apple Music, Apple TV,
  CapCut -- all sitting on login/welcome screens) and one filed as "mid-login"
  that was actually done (Reddit). No Japanese banking app tested so far sets
  FLAG_SECURE, so finance screenshots come through normally.
  Keep screenshots outside the repo -- they contain balances and account ids.
- **Timing:** 9 s covers most apps; Netflix, Suica and other splash-heavy apps
  need ~24 s. A launch that lands on `NexusLauncherActivity` means the app
  failed to start, not that it has no login. `am start` returning
  "Activity class does not exist" for the entry that `resolve-activity`
  itself reported means a broken install (seen on both Nikkei apps).
- **Do not `force-stop` when re-verifying a fresh login (know-how, verified
  2026-08-22):** the documented force-stop/cold-start method is right for the
  *first* classification, but some apps re-authenticate on every cold start.
  楽天証券資産形成 (iGrow) was scored `needs_login` twice because the cold start
  threw it into a Chrome passkey flow ("No passkeys available"); relaunching via
  the LAUNCHER intent *without* force-stop showed a fully loaded portfolio. When
  the user says "I just logged in", verify with a plain launch, not a cold one.
- **A connection toggle is not a login state:** Tailscale reads "Not connected"
  while fully signed in to its tailnet -- that is the VPN switch, not the
  account. Look for the tailnet name and account avatar instead.
- **The migration baseline lives in `Private/login-evidence.json`** (know-how,
  verified 2026-08-22): per package, `front_when_logged_in` (the activity a
  warm launch lands on while signed in) plus `evidence` (the on-screen marker
  that actually proves a session). Back-filled for all 58 signed-in apps.
  To check a replacement phone: install, warm-launch each app, compare `front`
  and look for the `evidence` marker.
- **Activity names are the weak half of that pair.** Counterexamples collected
  in one pass: signed in yet sitting on a login-looking activity -- Duolingo
  (`.app.LoginActivity`), Facebook (`.LoginActivity`), Snapchat
  (`.LandingPageActivity`), Revolut (`...login.pin.LoginActivity`), Wise
  (`BiometricUnlockActivity`), IKEA (`.welcomescreen.WelcomeActivity`);
  signed *out* yet on `MainActivity` -- Figma Mirror, Notion, Mercari. Treat
  `front` as a change detector, never as the verdict; `evidence` is the verdict.
- **FLAG_SECURE apps can't be screenshotted** (MS Authenticator, Wise, Revolut,
  PayPay produce an all-black PNG ~16-60 KB). For these the evidence *is* the
  lock screen: landing on a PIN/biometric/device-credential activity means an
  account is configured, since an unconfigured install has nothing to unlock.
- **Some apps look identical signed in and signed out** (Airbnb Explore, Yahoo
  乗換案内 search, Aurora Store's anonymous session, Canva behind its
  notification prompt). Their evidence strings say where to look instead --
  usually the profile/settings tab. Don't force a verdict from the home screen.
- **Never act on what the screenshot shows:** login forms with pre-filled
  credentials, Google Password Manager save/use prompts, passkey dialogs and
  first-run terms-of-service consent screens are all read-only observations.
  Press HOME and record them for the user; signing in, saving a credential or
  accepting terms is the user's decision, not the scan's.
- **Output:** results are written to
  `Private/android-login-scan-final-<date>.json` (each run's date; the
  script above always reads the most recent one as its baseline); login
  status is also
  kept in `Private/` only (the catalog gets `login_required` and nothing
  else), and `Private/android-inventory.json` carries a
  `login_tracking` progress list (move entries from `needs_login` to
  `logged_in` as the user signs in).

## apkeep CLI pitfalls (know-how, verified 2026-08-21/22)

- `-o` options are comma-separated in one flag
  (`-o "device=px_9a,split_apk=true"`); repeating `-o` or mixing formats
  errors out with a usage message.
- `device=` must be a gpapi-supported codename (`px_9a` is the safe default);
  Pixel 11 (`cubs`) is not in the built-in list — don't guess device names.
- Some apps download as a single `.apk` (no splits), some as a split dir, and
  APKPure may emit `.xapk` (zip of base + config) — inspect the output dir
  before installing rather than assuming one layout.
- `--accept-tos` is required on the first google-play login for a fresh
  dispenser account; without it apkeep exits asking for ToS acceptance.
- APKPure single-APK installs can fail with
  `INSTALL_FAILED_VERIFICATION_FAILURE`; `--no-streaming` avoids the streamed
  verification path but a genuinely mismatched signature still fails — fall
  back to the google-play channel in that case.

## Home Screen (launcher) control via adb

Know-how, verified 2026-08-21 on Pixel 11 (`cubs`, Android 17 / API 37).

- **No official adb interface** exists on the stock Pixel launcher
  (`com.google.android.apps.nexuslauncher`, the `android.app.role.HOME`
  holder) for icon positions or app widgets. The desktop layout lives in the
  launcher's private database
  (`/data/user_de/0/com.google.android.apps.nexuslauncher/databases/launcher.db`),
  which is `Permission denied` for the shell user (root required).
- **Widgets:** the system `AppWidgetManager.bindAppWidgetId` API is only
  callable by a launcher; there is no adb command to add a widget to the
  stock home screen.
- **What adb can do without root:**
  - Emulate a long-press drag with
    `adb shell input swipe x1 y1 x2 y2 <ms>` (long press ~600 ms then drag
    moves an icon; widget placement needs the widget picker plus exact pixel
    coordinates — fragile, fine only for small adjustments).
  - Return to home: `adb shell input keyevent KEYCODE_HOME`.
  - Set the default launcher role:
    `adb shell cmd role set-role-holder android.app.role.HOME <package>`.
  - Hide/disable an app icon:
    `adb shell pm disable-user --user 0 <pkg>`.
- **Practical layout paths:**
  - Third-party launcher (Nova Launcher etc.): supports desktop layout
    backup/restore; push the backup file via adb and restore it in the
    launcher — the closest to scripted layout configuration without root.
  - Rooted device: edit `launcher.db` (or the launcher export format)
    directly to set icon positions and inject widgets programmatically.
- **Caveats:** the Pixel app drawer is alphabetical and not reorderable via
  adb; grid size and icon size remain launcher-UI settings.

## Reviewed Apple Passwords export for Pixel Chrome

`scripts/pixel_password_export.py` converts a user-exported Apple Passwords
CSV into Chrome's `url,username,password` format for apps currently marked
`needs_login`. It is a local-only transform: macOS authentication and Apple
Passwords export remain visible, user-owned steps.

- The Private host allowlist assigns exact observed login hosts to Pixel
  packages; title or brand-keyword matching is prohibited.
- The Private decisions file stores only SHA-256 username selectors, never a
  password. It supports `keep_all`, `exclude`, `keep_only_username_sha256`,
  and `exclude_username_sha256` decisions per host.
- `--final` fails closed while any host has more than one username or more
  than one record for the same host and username. Review the password-free
  report, record a decision, then rerun.

```sh
python3 scripts/pixel_password_export.py \
  --apple-csv /absolute/path/to/apple-passwords.csv \
  --allowlist Private/pixel-password-import-host-allowlist.csv \
  --decisions Private/pixel-password-import-decisions.json \
  --output /absolute/path/to/Pixel_Chrome_Import.csv \
  --review Private/pixel-password-import-review.csv \
  --final
```

The output is plaintext and mode `0600`; delete it after Chrome imports it.

## Safety rules

- Never automate Google account login, purchases, or security confirmations.
- Never store Google tokens, AAS tokens, or APK contents in tracked config.
- Never install over an existing app without explicit confirmation and a
  backup of app data where applicable.
