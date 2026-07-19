---
component_id: "google-slides"
name: "Google Slides"
category: "Productivity"
tier: "core"
lifecycle_status: "active"
source: "official_web"
delivery_method: "vendor-download"
brew_cask: null
brew_formula: null
official_url: "https://slides.google.com/"
check_command: "test -d '/Applications/Google Slides.app'"
install_after: []
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
---
# Google Docs / Sheets / Slides

These are Google Workspace web-app shortcut bundles, not standalone native
document editors. Keep the shortcuts as Core workflow entries because they
provide direct access to the user's Docs, Sheets, and Slides surfaces.

Current macOS paths:

```text
/Applications/Google Docs.app
/Applications/Google Sheets.app
/Applications/Google Slides.app
```

The web applications and account authentication remain controlled by Google
and Chrome. Do not store account credentials in the catalog or state.
