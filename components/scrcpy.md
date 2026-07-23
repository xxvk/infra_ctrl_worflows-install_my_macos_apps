---
component_id: "scrcpy"
name: "scrcpy"
category: "Android tools"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-formula"
brew_formula: "scrcpy"
brew_cask: null
official_url: "https://github.com/Genymobile/scrcpy"
check_command: "scrcpy --version"
install_after:
  - "Android platform tools"
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or device secrets here."
download_estimate_bytes: 20000000
download_estimate_method: "homebrew_bottle_metadata"
---
# scrcpy

`scrcpy` mirrors and controls a physical Android device or emulator from the
Mac. It is the Core remote-observation tool for the Android Robot workflow.
Install with `brew install scrcpy`; the skill's Homebrew guard prevents this
install from silently upgrading existing formulae such as FFmpeg.

Verify the client with `scrcpy --version`, then verify the device path with
`adb devices`. USB debugging, Android Developer Options, pairing, and wireless
ADB remain explicit device-side steps; this skill never enables them or stores
their credentials automatically. For a network-connected robot, use the
documented `adb pair`/`adb connect` workflow and confirm the device serial before
viewing its screen.

Homebrew supplies runtime dependencies such as FFmpeg, libusb, and SDL3. Do not
install a second ADB copy when the SDK `platform-tools` workflow is already
present. Record the detected scrcpy and dependency versions only in
machine-local state.
