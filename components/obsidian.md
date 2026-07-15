---
name: "Obsidian"
category: "Productivity"
tier: core
status: installed
source: homebrew
download_bytes: null
download_estimate_bytes: 1000000000
download_estimate_method: catalog_size_gb_planning_estimate
installed_bytes: 1460625408
installed_version: "1.12.7"
installed_at: "2026-07-16"
secrets_policy: Never store passwords, API keys, recovery codes, or license secrets here.
---
ian.app`
- Bundle ID: `md.obsidian`
- Opened successfully after installation.

## Post-install checklist

- Set **Settings → General → Language** to **简体中文**, then restart Obsidian
  and verify the interface. This is an application-level setting stored in
  Obsidian's local storage (commonly the `language` key with value `zh`), not a
  vault setting in `.obsidian/app.json`; do not edit Electron/LevelDB files as
  part of deployment.
- Open the synced `XVK_PM` vault and confirm the expected files are visible.
- Choose one synchronization method deliberately: iCloud or Obsidian Sync;
  do not enable two competing sync mechanisms for the same vault without a
  backup and conflict plan.
- Review community plugins before enabling them and keep credentials outside
  the app catalog.
