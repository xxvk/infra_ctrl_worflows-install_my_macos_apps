---
component_id: "swiftmtp"
name: "SwiftMTP"
category: "File transfer"
tier: "optional"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "neighbor-z/swiftmtp/swiftmtp"
brew_formula: null
brew_tap: "neighbor-z/swiftmtp"
brew_tap_repository: "https://github.com/neighbor-z/homebrew-swiftmtp"
brew_tap_revision: "38d356054a70001dc790b5da4cb7cea4e3690f09"
brew_trust_cask: "neighbor-z/swiftmtp/swiftmtp"
official_url: "https://neighbor-z.github.io/swiftmtp-website/"
check_command: "'/Applications/SwiftMTP.app/Contents/MacOS/swiftmtp-cli' --version"
install_after: []
bundle_identifiers: ["me.neighborz.swiftmtp"]
account_required: false
permissions_required: []
secrets_policy: "Never store device serials, file names, device paths, transferred content, or AI service credentials here."
download_estimate_bytes: 5482254
download_estimate_method: "homebrew_cached_cask_artifact"
---

# SwiftMTP

> [!summary] Purpose
> Optional native Swift MTP client for browsing and transferring files between
> macOS and Android devices or cameras. It provides a GUI and a bundled
> `swiftmtp-cli`, works without ADB or USB debugging, and is suitable for
> bounded Agent workflows after the exact device, storage, and paths are
> confirmed.

SwiftMTP overlaps with Android File Transfer. Keep both cataloged as optional,
but never run two MTP clients against the same device simultaneously.

## Parameters

| Parameter | Value |
|---|---|
| Delivery | `homebrew-cask` |
| Package identifier | `neighbor-z/swiftmtp/swiftmtp` |
| Official source | `https://github.com/Neighbor-Z/SwiftMTP` |
| Required tier | `optional` |
| Install order | none |
| Expected download | about 5.5 MB for reviewed 1.2.4 artifact |
| Expected installed size | about 20 MB planning allowance; measure per Mac |
| App path | `/Applications/SwiftMTP.app` |
| Bundle ID | `me.neighborz.swiftmtp` |
| CLI path | `/Applications/SwiftMTP.app/Contents/MacOS/swiftmtp-cli` |
| Account needed | no |
| Permissions | device-side unlock and USB File Transfer/MTP selection |

## Source and security boundary

- Upstream: `https://github.com/Neighbor-Z/SwiftMTP`
- Tap: `https://github.com/neighbor-z/homebrew-swiftmtp`
- Reviewed Tap revision: `38d356054a70001dc790b5da4cb7cea4e3690f09`
- Trusted package: `neighbor-z/swiftmtp/swiftmtp`

The reviewed app is ad-hoc signed and does not carry a Developer ID team.
Gatekeeper may block the first launch. Never disable Gatekeeper or automate
`xattr` removal. Present the exact artifact and signature result; if the user
accepts it, use the visible System Settings → Privacy & Security security flow
and then verify the same bundle ID before launch.

The managed source policy trusts only the exact cask. Do not use
`brew trust neighbor-z/swiftmtp`, because that grants broader whole-Tap trust.
If the whole Tap is already trusted, normalize it only after explicit approval:

```sh
brew trust --cask neighbor-z/swiftmtp/swiftmtp
brew untrust --tap neighbor-z/swiftmtp
```

Verify that package-scoped trust remains before installation. Tap remote or
revision drift is a stop condition and requires a separate source review.

## Installation

- [ ] Confirm SwiftMTP is selected explicitly; optional items are not part of a
      Core deployment.
- [ ] Confirm the app is missing from the latest scan or that a reinstall was
      separately requested.
- [ ] Verify the Tap remote and HEAD against the pinned values above.
- [ ] Review the Cask URL, SHA-256, artifacts, bundle ID, and signature.
- [ ] Obtain explicit approval before tapping, trusting, downloading, or
      installing.
- [ ] Trust only the exact cask and install the fully qualified token.
- [ ] Record version, paths, bytes, source revision, signature and pass/fail
      only in machine-local state.

```sh
brew tap neighbor-z/swiftmtp
brew trust --cask neighbor-z/swiftmtp/swiftmtp
brew install --cask neighbor-z/swiftmtp/swiftmtp
```

The upstream shorthand `brew install --cask swiftmtp` is valid after tapping,
but this skill uses the fully qualified package name to prevent ambiguity.

## Device preparation

Before connecting:

- Quit Android File Transfer, its background agent, Image Capture, Preview and
  any other application holding the MTP session.
- Connect the intended device directly when possible.
- Unlock the device and choose USB **File Transfer / MTP** mode.
- Confirm the intended device before using any returned device ID.

If discovery fails with an open-session or libusb error, do not repeatedly
reset or mutate the device. Quit competing MTP clients, disconnect/reconnect,
unlock the device and retry one bounded discovery.

## Verification

Verify the app identity and bundled CLI without a device:

```sh
test -d '/Applications/SwiftMTP.app'
test "$(defaults read '/Applications/SwiftMTP.app/Contents/Info' CFBundleIdentifier)" = "me.neighborz.swiftmtp"
'/Applications/SwiftMTP.app/Contents/MacOS/swiftmtp-cli' --version
```

The current cask links the GUI executable as `SwiftMTP`; it does not link
`swiftmtp-cli` into Homebrew's bin directory. Use the full Bundle path unless
the user separately approves a stable CLI shim.

After a device is connected, keep initial verification read-only:

```sh
CLI='/Applications/SwiftMTP.app/Contents/MacOS/swiftmtp-cli'
"$CLI" devices
"$CLI" storages '<deviceId>'
"$CLI" ls '<deviceId>' '<storageId>' '/'
"$CLI" info '<deviceId>' '<storageId>'
```

An empty device list proves only that the CLI launched; it does not verify MTP
transfer. Open the GUI once, confirm the first window, then verify the exact
device and storage through both GUI and CLI read-back.

## Agent operation contract

Read-only `devices`, `storages`, `ls`, and `info` may run after the intended
physical device is identified. Treat all other commands as mutations:

- `pull` writes to the Mac.
- `push` writes to the device.
- `mkdir` and `mv` modify the device filesystem.
- `rm` permanently deletes a device item and may recursively delete a tree.

For every mutation, use:

```text
inspect device/storage/path
→ present exact source and destination
→ confirm one operation
→ execute once
→ list and verify both sides
→ record redacted evidence locally
```

The CLI has no native dry-run. Never infer a device, storage ID or remote path.
This skill does not currently register or implement SwiftMTP mutations, so an
Agent must not execute `push`, `mkdir`, `mv`, or `rm`; it may only prepare an
exact command for the user to review and run manually. A future adapter must
add a mutation-contract registry entry and tests before automating any of
these commands. Preserve source files until transfer size and destination
read-back succeed.

## Follow-up

- [ ] Verify one read-only device discovery and directory listing.
- [ ] Test transfer only when a disposable source and destination are provided.
- [ ] Keep device serials, filenames, paths and transferred content out of Git,
      component documentation and diagnostics.
- [ ] Re-run the macOS app scan and write results only to machine-local state.

## Rollback

Uninstall only the cask after explicit approval:

```sh
brew uninstall --cask neighbor-z/swiftmtp/swiftmtp
```

Revoke package trust and untap only after confirming no other managed package
uses the Tap. Uninstalling SwiftMTP does not authorize deletion of transferred
files on the Mac or connected devices.

## Evidence and notes

- Official repository: `https://github.com/Neighbor-Z/SwiftMTP`
- Official website: `https://neighbor-z.github.io/swiftmtp-website/`
- Tap repository: `https://github.com/neighbor-z/homebrew-swiftmtp`
- The bundled `CLI_USAGE.md` is available under the installed App Resources.
- Machine-specific versions, trust state, device results, paths, measurements,
  security approvals and transfer evidence belong only in machine-local state.

Never paste a machine-local record, completed checkbox, device identity,
permission result, detected path, measurement or timestamp into this guide.
