---
component_id: "slack"
name: "Slack"
category: "Communication"
tier: "core"
lifecycle_status: "active"
source: "app_store"
delivery_method: "app-store"
brew_cask: null
brew_formula: null
official_url: "https://slack.com/downloads/mac"
app_store_url: "macappstore://itunes.apple.com/app/id803453959"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 1000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# Slack

Slack is a Core communication app. Prefer the Mac App Store edition. A direct
download and the App Store edition may use the same Bundle ID, so the source
must be verified with the App Store receipt rather than the app name alone.

## App Store migration

1. Quit Slack and open the Mac App Store page directly:

   ```sh
   open "macappstore://itunes.apple.com/app/id803453959"
   ```

2. Install or update Slack from the Mac App Store.
3. Open `/Applications/Slack.app` and confirm the required workspaces are
   still available and signed in before cleaning any old data.
4. Verify the App Store receipt:

   ```sh
   test -f "/Applications/Slack.app/Contents/_MASReceipt/receipt"
   ```

5. If an additional direct-download Slack bundle exists, keep only the
   verified App Store copy in `/Applications` after workspace verification.

## Storage migration and cleanup

The direct-download build commonly leaves legacy data under:

```text
~/Library/Application Support/Slack
```

After the App Store copy opens successfully and all required workspaces have
been verified, measure this directory and remove it only when it is confirmed
to be the old direct-download data. Do not remove the App Store sandbox:

```text
~/Library/Containers/com.tinyspeck.slackmacgap
```

The container holds the App Store build's sandboxed data and may contain the
active login/session state. Never delete it as part of routine source cleanup.
Do not delete Slack data before interactive workspace verification, and do not
store workspace tokens, passwords, or message content in `state/` or Markdown.

## Verification

```sh
test -f "/Applications/Slack.app/Contents/_MASReceipt/receipt"
du -sh "$HOME/Library/Application Support/Slack" 2>/dev/null || true
test -d "$HOME/Library/Containers/com.tinyspeck.slackmacgap"
```

Record only source evidence, installed version, paths, measured cleanup size,
and verification time in the ignored `state/` installation record.
