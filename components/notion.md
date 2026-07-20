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

Notion is **WebCatalog-only** in this baseline. Reject native, Homebrew, and
Mac App Store bundles, even if they launch. The wrapper must point to
`https://www.notion.so/` and live under `~/Applications/WebCatalog Apps/`.

## Migration workflow

1. Force-quit Notion and its helper/updater processes before touching its files.
2. Confirm that the user can access the required workspaces in the Notion web version or web app.
3. Treat the old Notion app data and cache as disposable during this migration;
   do not preserve offline files or local cache unless the user explicitly
   overrides this rule.
4. Remove the old native/App Store desktop app only after the WebCatalog
   wrapper is opened and verified. Move the app bundle to Trash, then remove
   Notion-owned support data and caches.

5. Run a disk scan for residual Notion-owned directories. The known large cache/support directory is:

   ```text
   ~/Library/Application Support/Notion
   ```

6. Report the measured size, then remove the Notion-owned cache/support
   directories as part of the approved Notion cleanup. Never delete the user's
   browser profile or unrelated Electron application data.
7. Verify that the desktop app and its known support directory are gone, then refresh the disk-analysis scan and record the reclaimed bytes in the operation log.

The `~/Library/Application Support/Notion` directory is included in the
Notion cleanup. Record its measured size and deletion result in `state/`.
