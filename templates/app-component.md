---
component_id: "<stable-kebab-case-id>"
name: "<App or component name>"
category: "<AI|Browser|Developer tools|Network|Productivity|...>"
tier: "<core|developer|optional|heavy>"
lifecycle_status: "<planned|active|retired|blocked>"
source: "<app_store|homebrew|npm_global|official_web|manual>"
delivery_method: "<homebrew-cask|homebrew-formula|app-store|vendor-download|manual>"
brew_cask: "<identifier or null>"
brew_formula: "<identifier or null>"
official_url: "<official vendor URL>"
check_command: "<command or null>"
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
---

# <App or component name>

> [!summary] Purpose
> <What this app/component is for, and why it belongs in the Mac setup.>

## Parameters

| Parameter | Value |
|---|---|
| Delivery | `<homebrew-cask / homebrew-formula / app-store / vendor-download / manual>` |
| Package identifier | `<brew cask, formula, or store identifier>` |
| Official source | `<official URL>` |
| Required tier | `<core / developer / optional / heavy>` |
| Install order | `<dependencies or none>` |
| Expected download | `<bytes or unknown>` |
| Expected installed size | `<bytes or unknown>` |
| Config path(s) | `<paths or none>` |
| Account needed | `<yes / no>` |
| Permissions | `<macOS permissions or none>` |

## Installation

- [ ] Confirm the app is missing from the latest scan.
- [ ] Confirm the selected plan and available disk space.
- [ ] Run the dry run with no external changes.
- [ ] Obtain explicit approval before download or installation.
- [ ] Install using the verified delivery method.
- [ ] Record `download_bytes`, `installed_bytes`, version, and timestamps in frontmatter and the install log.

### Command or user action

```sh
<dry-run or installation command>
```

<For App Store, vendor-download, or manual items, describe the user-only steps and the verified vendor domain.>

## Configuration

- [ ] Create or update: `<configuration path>`
- [ ] If shell environment is required, add one labelled idempotent block to the active shell startup file; preserve unrelated lines and record a backup in `state/`.
- [ ] Apply required settings:

```ini
<configuration snippet or commands>
```

- [ ] Preserve unrelated user settings.
- [ ] Never automate sign-in, license entry, VPN approval, device management, or privacy permissions.
- [ ] Record non-secret configuration choices in `completion_notes` or this document.

## Verification

- [ ] Confirm the expected app/binary is present.
- [ ] Open the GUI app and confirm the first window appears without a crash or security warning.
- [ ] Run the health check:

```sh
<check command>
```

- [ ] Confirm the configured behavior works.
- [ ] Re-run the macOS app scan.
- [ ] Set `verification_status: passed` and record `verified_at`.

## Follow-up

- [ ] <Account, license, permission, or operational follow-up>
- [ ] <Documentation or team setup follow-up>

## Rollback

<Describe the narrow, reversible removal or reset procedure. State what data is preserved and what would be permanently deleted.>

## Evidence and notes

- Install record: `<state/install-YYYYMMDD-HHMMSS.json>`
- Scan record: `<state/scan-YYYYMMDD-HHMMSS.json>`
- Source checked: `<URL and date>`
- Notes: <non-secret observations>
