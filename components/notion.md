---
component_id: "notion"
name: "Notion"
category: "Productivity"
tier: "core"
lifecycle_status: "active"
source: "webcatalog"
delivery_method: "webcatalog-wrapper"
brew_cask: null
brew_formula: null
official_url: "https://www.notion.so/desktop"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 1000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# Notion WebCatalog app

Use Notion through a WebCatalog wrapper, not the native Homebrew desktop app.
The wrapper should point to `https://www.notion.so/` and live under
`~/Applications/WebCatalog Apps/`.

## Migration workflow

1. Force-quit Notion and its helper/updater processes before touching its files.
2. Confirm that the user can access the required workspaces in the Notion web version or web app.
3. Verify that offline files and local cache are not the only copy of important data.
4. Remove the native desktop app after the WebCatalog wrapper is verified:

   ```sh
   brew uninstall --cask notion
   ```

5. Run a disk scan for residual Notion-owned directories. The known large cache/support directory is:

   ```text
   ~/Library/Application Support/Notion
   ```

6. Report the measured size before deletion. After explicit confirmation, remove only the Notion-owned cache/support directories discovered by the scan; do not delete the user's browser profile or unrelated Electron application data.
7. Verify that the desktop app and its known support directory are gone, then refresh the disk-analysis scan and record the reclaimed bytes in the operation log.

The `~/Library/Application Support/Notion` directory may contain cached workspace data and offline data. Do not delete it automatically during this source migration; report its size and request separate cleanup confirmation.
