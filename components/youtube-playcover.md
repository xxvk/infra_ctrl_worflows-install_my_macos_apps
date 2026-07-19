---
component_id: "youtube-playcover"
name: "YouTube (PlayCover)"
category: "Media compatibility"
tier: "core"
lifecycle_status: "active"
source: "app_store"
delivery_method: "app-store"
brew_cask: null
brew_formula: null
official_url: "https://www.youtube.com/"
check_command: null
install_after: ["PlayCover"]
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
preferred_source: "approved-private-source.invalid IPA Library"
installed_measurement_method: "local_du"
---
# YouTube (PlayCover)

This is the iPad/iPhone YouTube app running through PlayCover on Apple Silicon
macOS. It is a Core capability because the user explicitly wants a local
YouTube app rather than the browser site.

## IPA source

Use the current YouTube entry in the already configured `approved-private-source.invalid` IPA
Library (or another explicitly approved, reputable decrypted-IPA source).
IPATool is not a prerequisite: M4a and M4b verified that its Apple account
workflow is not usable for this PlayCover acquisition. Do not hard-code a
direct IPA download URL in the catalog: source links and versions change. A
validated test package was named:

```text
com.google.ios.youtube-21.28.3-Decrypted.ipa
```

The package must be decrypted. An IPA downloaded with `ipatool` from the App
Store is encrypted and is not accepted by PlayCover.

After import, PlayCover may automatically install PlayTools. Open the
YouTube app's Settings → Misc and click **Remove PlayTools** before the first
launch. This is mandatory for the validated YouTube package; leaving PlayTools
installed caused startup failure in the PlayKeychain/DRM path.

## Known-good PlayCover profile

The following profile is required for the tested YouTube 21.28.3 package:

- **PlayTools:** removed/not installed. This is mandatory for this YouTube
  build; with PlayTools installed, startup crashed in `PlayKeychain` while
  YouTube initialized the DRM/keychain path.
- **Keymapping:** on in the saved profile but inactive because PlayTools is
  removed.
- **Smart Keymap:** on but inactive without PlayTools.
- **Scroll Wheel:** on but inactive without PlayTools.
- **PlayChain:** off.
- **Jailbreak Bypass:** on.
- **Introspection libraries:** off.
- **Force Insert iOS Frameworks:** on.
- **Virtual device:** iPad Pro 13-inch (7th generation), M4, 8 GB.
- **Resolution:** 1080p.
- **Aspect ratio:** 4:3.
- **Resolution scaler:** 2.0.
- **Window fixes:** off; method remains Normal.
- **Disable display sleep:** off.
- **Application category:** `public.app-category.video`.
- **Discord activity, LLDB, Metal HUD, and root-directory mode:** off.

## Login persistence limitation

For the validated YouTube 21.28.3 profile, PlayTools must remain removed because
reintroducing it caused startup failure in the PlayKeychain/DRM path. PlayChain
was tested as a possible login-persistence mechanism, but enabling it did not
reliably preserve the YouTube session for this installation. The supported
behavior is therefore **sign in again whenever YouTube is reopened after
quitting**.

Do not delete Keychain items, the PlayChain database, or PlayCover containers
automatically in an attempt to repair this. Persistent login is a future
compatibility task, not a current acceptance criterion.

## Verification

1. Import the decrypted IPA into PlayCover.
2. Open YouTube with PlayTools still removed.
3. Confirm the app reaches its home screen and plays a video.
4. If startup crashes and the report contains `PlayKeychain.copyMatching`,
   `igdrms`, or `PlayTools`, verify that PlayTools was not reinjected.
5. After quitting and reopening, expect that a fresh login may be required.

Machine-specific installed version, launch result, paths, and timestamps belong
in ignored `state/` records, not this guide.
