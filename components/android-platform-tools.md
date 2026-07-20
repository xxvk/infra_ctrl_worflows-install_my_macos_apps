---
component_id: "android-platform-tools"
name: "Android platform tools"
category: "Android tools"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "android-platform-tools"
preferred_install_method: "sdkmanager"
avoid_duplicate_with: "Android command-line tools SDK platform-tools"
brew_formula: null
official_url: "https://developer.android.com/tools/releases/platform-tools"
check_command: "adb"
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 100000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# Android platform tools

Provides `adb` and related Android device tools. For the Core Android SDK
workflow, install it through `sdkmanager --sdk_root="$ANDROID_SDK_ROOT"
platform-tools` so it shares the selected Emulator/platform packages. The
Homebrew cask remains a fallback for a standalone ADB-only machine; do not
install both copies on the same Mac. See
[`references/environment.md`](../references/environment.md).
