---
component_id: "solaar"
name: "Solaar"
category: "Hardware utilities"
tier: "option"
lifecycle_status: "active"
source: "github"
delivery_method: "github-source"
brew_cask: null
brew_formula: null
official_url: "https://pwr-solaar.github.io/Solaar/installation/"
check_command: "test -d '/Applications/Solaar.app'"
github_repository: "https://github.com/pwr-Solaar/Solaar"
github_release: "1.1.19"
github_revision: "4bda869542ea0b2e54f24decd4cca65113679e25"
github_artifact: "tools/create-macos-app.sh"
artifact_sha256: "00fdb57a6676cfc0b31addcf34dc76a0233c720635ced9a7a7f528e93595b563"
install_after: []
account_required: false
permissions_required: ["Any macOS permission requested by the generated app must be approved manually"]
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 200000000
download_estimate_method: "catalog_size_gb_planning_estimate"
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
curl -fL \
  https://raw.githubusercontent.com/pwr-Solaar/Solaar/4bda869542ea0b2e54f24decd4cca65113679e25/tools/create-macos-app.sh \
  -o /tmp/solaar-create-macos-app.sh
echo "00fdb57a6676cfc0b31addcf34dc76a0233c720635ced9a7a7f528e93595b563  /tmp/solaar-create-macos-app.sh" \
  | shasum -a 256 -c -
bash /tmp/solaar-create-macos-app.sh
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
- Save current names, readings, and timestamps only in machine-local state.

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
