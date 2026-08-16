---
component_id: "xcodes"
name: "Xcodes"
category: "Developer tools"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "xcodes-app"
brew_formula: null
official_url: "https://github.com/XcodesOrg/XcodesApp"
check_command: "test -d '/Applications/Xcodes.app'"
install_after: []
account_required: true
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
---

# Xcodes

> [!summary] Purpose
> Xcodes is the required Xcode version manager. It installs Apple release and
> prerelease builds side by side, resumes downloads, selects the active
> developer directory, and avoids repeated manual `.xip` handling.

## Parameters

| Parameter | Value |
|---|---|
| Delivery | `homebrew-cask` |
| Package identifier | `xcodes-app` |
| Official source | `https://github.com/XcodesOrg/XcodesApp` |
| Required tier | `core` |
| Install order | none; Xcodes does not require a preinstalled full Xcode |
| Expected download | approximately 100 MB planning allowance; measure locally |
| Expected installed size | unknown; measure locally |
| Config path(s) | Xcodes preferences and macOS Keychain; never export credentials |
| Account needed | yes, only when Apple requires authentication for Xcode downloads |
| Permissions | administrator authentication may be required to install or select Xcode |

## Installation

- [ ] Confirm Xcodes is missing from the latest scan.
- [ ] Confirm the selected plan and available disk space.
- [ ] Run the dry run with no external changes.
- [ ] Obtain explicit approval before download or installation.
- [ ] Install the signed and notarized Homebrew Cask.
- [ ] Record versions, paths, timestamps, and pass/fail only in machine-local state.

```sh
brew install --cask xcodes-app
```

`brew upgrade --cask xcodes-app` updates the manager. Xcode releases are
downloaded and managed inside Xcodes; upgrading the cask does not upgrade an
installed Xcode release.

## Configuration and Xcode installation

1. Open Xcodes and refresh the release list.
2. Choose the Apple Silicon variant on Apple Silicon Macs.
3. Prefer the latest verified release that supplies the SDK required by the
   selected macomrade feature. Do not assume the newest beta is production-safe.
4. Apple Account password, passkey/security-key interaction, two-factor code,
   license acceptance, and administrator authentication are user-only steps.
5. Never persist Apple credentials, session cookies, or two-factor codes in
   Git, Private configuration, logs, diagnostic bundles, or machine state.
6. Keep the previous working Xcode until the new build passes the checks below.

Xcodes can automate download, resume, archive expansion, installation, and
selection, but Apple prerelease builds are generally full downloads rather
than small Homebrew-style incremental upgrades.

### Authentication and helper recovery

- An Xcode download that fails with `HTTP 401` normally needs an authenticated
  Apple session inside Xcodes. Open the Xcodes account UI and hand Apple ID,
  password/passkey, and two-factor authentication to the user. Never copy those
  values into a command, log, state record, or tracked file. Retry only after
  the account UI visibly reports a signed-in session.
- Approve installation of the Xcodes **Privileged Helper** only as a separate,
  visible action. The helper supports privileged post-install operations and
  developer-directory selection; any administrator password remains a
  user-only handoff.
- A row labelled `Selected` is not sufficient proof that the system developer
  directory changed. Select the intended row, use **Make active**, and then
  perform the CLI read-back below.

## Verification

- [ ] Confirm `/Applications/Xcodes.app` launches without a security warning.
- [ ] Confirm the intended Xcode appears as installed and selected in Xcodes.
- [ ] Confirm the developer directory, Xcode build, and SDK path agree:

```sh
test -d /Applications/Xcodes.app
xcode-select -p
xcodebuild -version
xcrun --sdk macosx --show-sdk-path
```

- [ ] Confirm `xcode-select -p` resolves inside the intended Xcode application;
      do not infer activation from Xcodes UI wording alone.
- [ ] For a version-specific API, verify its declaration exists in the selected
      SDK and compile the exact symbol in a minimal fixture before removing the
      previous Xcode. Type-checking only the enclosing class is insufficient.
- [ ] In sandboxed automation, direct Swift/Clang module caches to a writable
      temporary path rather than treating a cache permission error as an SDK
      failure:

```sh
xcrun swift -module-cache-path /tmp/macomrade-swift-module-cache \
  -e 'import SafariServices; print("SafariServices import passed")'
```

- [ ] Re-run the macOS app scan and store the result only in machine-local state.

## Xcode replacement guard

Treat Xcodes and Xcode as separate components. Xcodes is Core; individual full
Xcode installations remain workload- and SDK-dependent. Before removing an old
Xcode:

1. install and select the replacement;
2. accept required Apple license and first-launch components;
3. verify `xcodebuild`, `xcode-select`, the target SDK, and one representative build;
4. measure the old application separately from DerivedData, simulators, and
   Command Line Tools;
5. obtain explicit approval for the old application removal.

Never delete `/Library/Developer`, SDK directories, simulator runtimes, or
Command Line Tools as a side effect of replacing the Xcode application.

### Root-owned old Xcode fallback

An Xcode installed by the Mac App Store can be `root-owned`. Xcodes may then
fail to move it to the user's Trash even when its Privileged Helper is present.
Treat this as a permission-bound cleanup failure, not as evidence that the new
Xcode is inactive.

Inspect the exact old bundle first:

```sh
ls -ldeO@ /Applications/Xcode.app
xcode-select -p
xcodebuild -version
```

Only when the replacement has passed the replacement guard, the active path is
not `/Applications/Xcode.app/Contents/Developer`, and the user explicitly
confirms `CONFIRM REMOVE OLD XCODE`, hand this exact permanent fallback to the
user in a visible Terminal:

```sh
sudo rm -rf -- /Applications/Xcode.app
```

Do not generalize the target with a wildcard and do not automate the password.
Afterward, verify both sides independently:

```sh
test ! -e /Applications/Xcode.app
test -d "$(dirname "$(dirname "$(xcode-select -p)")")"
xcode-select -p
xcodebuild -version
```

If the old bundle is at another path, freeze and review that exact path instead
of adapting this command implicitly. This fallback is permanent; the ordinary
Xcodes move-to-Trash path remains preferred when it works. This is a visible
operator recovery handoff, not a repository-implemented mutation; macomrade
must never run the `sudo rm` command itself.

## Rollback

Removing the manager does not remove Xcode applications it installed:

```sh
brew uninstall --cask xcodes-app
```

Before uninstalling Xcodes, select a valid remaining Xcode or Command Line
Tools developer directory. Sign out inside Xcodes before removing any saved
Apple session; Keychain credential removal is a separate, explicit user action.

## Evidence and notes

- Install and scan evidence belongs only in machine-local state.
- The public guide records desired behavior and source, never this Mac's login,
  selected beta, detected version, or installation result.
- Xcodes upstream: `https://github.com/XcodesOrg/XcodesApp`
