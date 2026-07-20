---
component_id: "logi-options-plus"
name: "Logi Options+"
category: "Hardware utilities"
tier: "option"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "logi-options+"
brew_formula: null
official_url: "https://www.logitech.com/en-us/software/logi-options-plus"
check_command: "test -d '/Applications/logioptionsplus.app' || test -d '/Library/Application Support/Logi/LogiOptionsPlus'"
reboot_required: true
installer_behavior: "homebrew_cask_privileged_installer"
install_after: []
account_required: false
permissions_required: ["Only permissions requested by the app and approved by the user"]
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 500000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# Logi Options+

Optional Logitech device utility for supported keyboards and mice. It may show
battery status, low-battery notifications, firmware information, and device
customization. Support depends on the exact model; the USB receiver alone does
not prove that battery telemetry is available.

## Installation

```sh
brew install --cask logi-options+
```

Homebrew lists `logi-options+` as the current cask. The older `logitech-options`
cask is deprecated and should not be used for new installations.

After a successful privileged install and reboot, the temporary
`/Applications/logioptionsplus_installer.app` may remain. It is installer
residue, not the running application, and may be removed after verifying that
`logioptionsplus.app`, `LogiPluginService.app`, and the Logi support directory
are present. Keep the PluginService, Driver Installer bundle, and
`/Library/Application Support/Logi` because Options+ uses them at runtime.

## Configuration and permissions

- Open Logi Options+ and allow it to detect the connected Logitech devices.
- Prefer Logi Options+ device-level key remapping for MX Keys Mac function
  keys (for example, F1 → ChatGPT and F2 → Claude). This avoids a custom HID
  listener, Fn-layer ambiguity, and Input Monitoring authorization.
- Approve only the macOS privacy permissions requested by the app, manually in
  System Settings when prompted.
- Do not record account credentials or permission state in the catalog.

## Verification

Homebrew may report the cask as installed while the vendor installer is still
staging the application under `/Library/Application Support/Logi/LogiOptionsPlus`.
The cask also requires a reboot. Do not treat `brew list --cask` alone as a
successful application installation: after reboot confirm the app bundle is
present, launch it once, and rerun the macOS app scan.

```sh
test -d "/Applications/logioptionsplus.app" || \
  test -d "/Library/Application Support/Logi/LogiOptionsPlus"
```

Then confirm whether both the keyboard and mouse appear in the app and whether
each device exposes a battery level. If a device is absent or has no battery
field, record that result in ignored machine state; do not treat it as a failed
installation.

## Rollback

```sh
brew uninstall --cask logi-options+
```

This removes the application but does not remove the physical devices or their
receiver pairing.
