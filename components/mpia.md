---
component_id: "mpia"
name: "mpia"
category: "Developer CLI"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "xxvk/tap/mpia"
brew_formula: null
official_url: "https://github.com/xxvk/mpia-cli"
check_command: "mpia --version"
install_after: []
account_required: false
permissions_required: ["Full Disk Access"]
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here. Inline --params/--body JSON is visible in process arguments and shell history."
download_estimate_bytes: 7500000
download_estimate_method: "github_release_asset_metadata"
---

# mpia

Local, scriptable macOS data access layer. It is the skill's preferred live
Safari bookmark and Reading List adapter; see
[browser-workflow-cli.md](../references/browser-workflow-cli.md) for the route
contract.

`mpia` is the renamed `macos-data-cli`. Two things changed together, and both
matter operationally:

- **Command surface.** 0.9.3 removed adapter/subcommands. Every call is
  `mpia METHOD "/path" [--params JSON] [--body JSON] [--dry-run|--apply]
  [--confirm PHRASE]`. There is no `--stdin`.
- **Identity.** The bundle identifier is now `com.xvk.mpia.cli`, so **every
  prior TCC grant was reset**. A Mac that worked under `macos-data` must be
  authorized again.

## Installation

The cask lives in a personal tap. Trust the cask, never the whole tap:

```sh
brew tap xxvk/tap
brew trust --cask xxvk/tap/mpia
brew install --cask xxvk/tap/mpia
```

## Gatekeeper boundary

The published binary is **ad-hoc signed, has no Team ID, and is not
notarized**. Homebrew verifies the SHA-256 but does not clear the quarantine
attribute, so the binary is killed by Gatekeeper on first run:

```text
mpia --version   ->  exit 137 (SIGKILL), no output
spctl --assess   ->  rejected
```

The cask's own caveats direct the user to remove only mpia's quarantine
attribute. Treat that as the user's decision, not an instruction to automate:
never run `xattr -d` on their behalf, and never disable Gatekeeper globally.
After the attribute is cleared, `spctl` still reports `rejected` — that is the
normal state for an ad-hoc signed binary and does not mean it is broken.

## Authorization

Safari bookmark reads need Full Disk Access granted to `/Applications/mpia.app`
in System Settings → Privacy & Security. Granting it requires an
authentication prompt, so hand that step to the user.

```sh
mpia OPTIONS "/safari/permission"   # bookmarksReadable must be true
```

## Verification

```sh
mpia --version
mpia GET "/agent/manifest"          # every route, method, schema, exit code
mpia OPTIONS "/resources"           # adapters, selection state, limitations
python3 scripts/browser_sources.py inspect-safari
```

`inspect-safari` reports three independent gates — routes, authorization, and
whether the adapter can parse this Mac's `Bookmarks.plist`. All three must pass
before the CLI is selected as the live path.

## Known limitation

`mpia 0.9.3` cannot parse Safari 27's `Bookmarks.plist`; every
`/safari/bookmarks/*` and `/safari/reading-list/*` read returns
`SAFARI_SCHEMA_UNSUPPORTED` even with Full Disk Access granted. Until an
upstream fix lands, the live Safari path is the explicit export, and the skill
must say which gate failed rather than reporting the CLI as available.
