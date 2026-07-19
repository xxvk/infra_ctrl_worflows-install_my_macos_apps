---
component_id: "solaar"
name: "Solaar"
category: "Hardware utilities"
tier: "optional"
lifecycle_status: "active"
source: "github"
delivery_method: "vendor-download"
brew_cask: null
brew_formula: null
official_url: "https://pwr-solaar.github.io/Solaar/installation/"
check_command: "test -d '/Applications/Solaar.app'"
install_after: []
permissions_required: ["Any macOS permission requested by the generated app must be approved manually"]
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
---
# Solaar

Optional open-source Logitech receiver manager. On macOS it is a limited,
community-supported path for inspecting and configuring compatible Logitech
devices, including some Nano/Unifying receiver pairings. It is useful for
testing whether a legacy K240/M212 pairing exposes battery telemetry that
macOS and Logi Options+ do not show.

## Hardware-specific rule

The current target hardware is:

- Keyboard: Logitech K240
- Mouse: Logitech M212
- Shared receiver: `VID 0x046d`, `PID 0xc534`

The receiver ID does not by itself prove the physical models. Solaar may show
protocol or internal names such as `MK270` or `M150`; do not map those names to
the physical keyboard or mouse without selecting the device and checking the
right-hand details pane.

## Installation

There is no official Homebrew Solaar cask. Homebrew supplies dependencies, and
the Solaar project supplies the Python package and macOS wrapper script:

```sh
brew install hidapi gtk+3 pygobject3 pipx
pipx install --system-site-packages solaar
bash <(curl -fsSL https://raw.githubusercontent.com/pwr-Solaar/Solaar/refs/heads/master/tools/create-macos-app.sh)
```

This should create:

```text
/Applications/Solaar.app
```

The official macOS documentation describes support as limited. Pairing,
configuration, and some device status may work; Linux-oriented rule and
diversion features do not.

## Receiver access and verification

- Quit Logi Options+ and OpenLogi before launching Solaar; only one utility
  should claim the receiver at a time.
- Open Solaar and expand `Nano Receiver`.
- Select each child device separately.
- Only treat the right-hand device title as authoritative for the selected
  device type.
- Record battery readings as approximate, device-reported observations.
- Interpret `Battery Level: 30% (next reported 5%)` as current 30%; `5%` is a
  future reporting threshold.
- Save current names, readings, and timestamps only in ignored `state/`.

## Verification

```sh
test -d "/Applications/Solaar.app"
```

Then confirm whether Solaar displays the K240 and M212 as separate devices and
whether each details pane reports a battery level. A successful app install
with no detected devices is a compatibility result, not an installation
failure.

## Safety boundary

Use Solaar for read-only battery investigation first. Do not change pairing,
profiles, firmware, or receiver settings unless separately requested and
verified. Do not run Solaar simultaneously with Logi Options+ or OpenLogi.

## Rollback

```sh
rm -rf "/Applications/Solaar.app"
pipx uninstall solaar
```

Only remove the Homebrew dependencies if no other application uses them.
