---
component_id: "google-chrome"
name: "Google Chrome"
category: "Browser"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "google-chrome"
brew_formula: null
official_url: "https://www.google.com/chrome/"
check_command: null
install_after: []
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
---
ogle profile.
- Enable only the extensions needed for this Mac.
- Run the Chrome Codex extension preflight before browser-controlled downloads.
- For a new Mac, inventory profiles with `scripts/chrome_profiles.py` and
  compare `profile_directory` plus `account_email` with the saved seven-profile
  registry. Open missing profiles one at a time and let the user complete
  Google sign-in, Passkey, and Touch ID prompts. Do not store credentials or
  Passkey data.
- Review microphone, camera, notifications, and screen-recording requests when
  a site or extension actually needs them.
