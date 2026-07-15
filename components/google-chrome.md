---
name: "Google Chrome"
category: "Browser"
tier: core
status: installed
source: homebrew
download_bytes: null
download_estimate_bytes: 1000000000
download_estimate_method: catalog_size_gb_planning_estimate
installed_bytes: 2242318336
installed_version: "150.0.7871.125"
installed_at: "2026-07-16"
secrets_policy: Never store passwords, API keys, recovery codes, or license secrets here.
---
`/Applications/Google Chrome.app`
- Bundle ID: `com.google.Chrome`
- Opened successfully after installation.

## Post-install checklist

- Sign in only with the intended Google profile.
- Enable only the extensions needed for this Mac.
- Run the Chrome Codex extension preflight before browser-controlled downloads.
- For a new Mac, inventory profiles with `scripts/chrome_profiles.py` and
  compare `profile_directory` plus `account_email` with the saved seven-profile
  registry. Open missing profiles one at a time and let the user complete
  Google sign-in, Passkey, and Touch ID prompts. Do not store credentials or
  Passkey data.
- Review microphone, camera, notifications, and screen-recording requests when
  a site or extension actually needs them.
