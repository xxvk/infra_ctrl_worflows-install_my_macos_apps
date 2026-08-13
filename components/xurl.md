---
component_id: "xurl"
name: "xurl"
category: "Developer tools"
tier: "optional"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "xdevplatform/tap/xurl"
brew_formula: null
official_url: "https://github.com/xdevplatform/xurl"
check_command: "xurl --version"
install_after: []
account_required: true
permissions_required: []
secrets_policy: "Never store X Developer client secrets, OAuth tokens, API credentials, or any content from ~/.xurl here."
download_estimate_bytes: 20000000
download_estimate_method: "catalog_size_gb_planning_estimate"
brew_tap: "xdevplatform/tap"
brew_tap_repository: "https://github.com/xdevplatform/homebrew-tap"
brew_tap_revision: "58d30f39afe2eff87c683be40b53f246f00efc89"
brew_trust_cask: "xdevplatform/tap/xurl"
---
# xurl

> [!summary] Purpose
> Optional official X API command-line client with curl-like raw endpoint
> access and OAuth account management. Prefer core `tamnd/x-cli` for ordinary
> free reads; retain xurl for official-only endpoints and confirmed writes.

## Parameters

| Parameter | Value |
|---|---|
| Delivery | `homebrew-cask` |
| Package identifier | `xdevplatform/tap/xurl` |
| Official source | `https://github.com/xdevplatform/xurl` |
| Required tier | `optional` |
| Install order | none |
| Expected download | 20 MB planning estimate |
| Expected installed size | unknown; measure per Mac |
| Config path(s) | `~/.xurl` (local sensitive YAML) |
| Account needed | yes, for API requests |
| Permissions | X Developer app and endpoint-appropriate OAuth scopes |

## Installation

- [ ] Confirm `xurl` is missing from the latest scan.
- [ ] Confirm the selected plan and available disk space.
- [ ] Run the dry run with no external changes.
- [ ] Obtain explicit approval before download or installation.
- [ ] Verify the Tap remote and HEAD against the pinned values above.
- [ ] Trust only the exact `xurl` cask; never trust the whole Tap.
- [ ] Install from the verified X Developer Platform Tap.
- [ ] Record observed version, path, sizes, timestamps, and pass/fail only in
      machine-local state.

```sh
brew tap xdevplatform/tap
brew trust --cask xdevplatform/tap/xurl
brew install --cask xdevplatform/tap/xurl
```

The managed installer must stop if the Tap remote or commit differs from the
frontmatter. Review and update the pinned revision in a separate supply-chain
change before accepting a newer Tap state.

## Configuration and authentication

X API access requires an X Developer account and an app configured in the X
Developer Console. The default local OAuth callback is
`http://localhost:8080/callback`.

Register an app profile and begin OAuth only in an interactive terminal. Never
paste the client secret into tracked documentation, logs, diagnostics, shell
history intended for sync, or machine-state records.

```sh
xurl auth apps add <app-name> \
  --client-id <client-id> \
  --client-secret <client-secret> \
  --redirect-uri http://localhost:8080/callback
xurl auth oauth2 --app <app-name>
```

The operator completes the browser sign-in and consent flow. Current xurl
stores credentials and tokens in local YAML at `~/.xurl`; that file must remain
machine-local, excluded from Git and diagnostic bundles, and treated as a
secret. Do not copy it between Macs as a bootstrap shortcut.

X API usage may require prepaid or pay-per-use credits. Before automated or
large reads, check the current terms and prices at
`https://docs.x.com/x-api/getting-started/pricing`; do not rely on a persisted
per-request price.

## Verification

Verify installation before starting authentication:

```sh
command -v xurl
xurl --version
```

After the user completes OAuth, verify the selected app and identity without
printing secrets:

```sh
xurl auth status
xurl whoami
```

- [ ] Confirm the binary resolves to the managed Homebrew installation.
- [ ] Confirm the intended app and X account are active.
- [ ] Confirm scopes are limited to the planned endpoints.
- [ ] Confirm the current API credit/billing arrangement before billable calls.
- [ ] Run a bounded read-only request and record only non-secret pass/fail in
      machine-local state.

If X reports that the client is forbidden or not enrolled, stop. Resolve the
app environment, API product enrollment, billing, and OAuth settings in the X
Developer Console; do not retry repeatedly or broaden scopes automatically.

## Agent operation contract

Use core `tamnd/x-cli` for ordinary read-only discovery, profiles, timelines,
threads, and searches when its free surfaces can answer the request. Use xurl
only when the user requires an official endpoint, paid API reliability, or an
account write that `tamnd/x-cli` deliberately does not support.

Read-only user search and timeline requests may run after verifying account,
scope, query bounds, and credit impact. For follow, unfollow, posting, deletion,
or any other write endpoint, always:

1. Check the active X account, target identifier, required scope, and likely
   credit impact.
2. Present a dry-run containing the exact method, endpoint, and redacted body.
3. Obtain explicit confirmation immediately before the mutation.
4. Execute once, then read back the resulting relationship or resource.

Installation or OAuth approval never authorizes later X account writes.

Read [X CLI operations](../references/x-cli-operations.md) for bounded user
lookup and timeline examples, the prohibition on exposing `xurl token`, and the
follow/unfollow dry-run and read-back sequence.

## Follow-up

- [ ] Verify user search and a small recent-timeline read when those workflows
      are first needed.
- [ ] Keep endpoint examples in an operation-specific skill rather than storing
      account IDs or personal targets in this component guide.
- [ ] Re-check official API pricing and endpoint availability before automation.

## Rollback

Clearing all local xurl credentials is destructive and requires separate
explicit confirmation:

```sh
xurl auth clear --all
```

Uninstalling the CLI does not authorize deleting `~/.xurl`:

```sh
brew uninstall --cask xdevplatform/tap/xurl
```

Untap `xdevplatform/tap` only after confirming no other managed package uses
it. Preserve `~/.xurl` unless the user separately approves credential removal.

## Evidence and notes

- Official repository: `https://github.com/xdevplatform/xurl`
- Official documentation: `https://docs.x.com/tools/xurl`
- Source-policy evidence: the exact Tap repository and reviewed full commit are
  pinned in this guide, the catalog, and `references/source-policy.json`.
- Machine-specific installation, version, authentication, billing, and request
  results belong only in machine-local state.

Never paste a machine-local record, completed checkbox, detected version,
installed path, account identity, scope grant, billing state, or timestamp back
into this tracked guide.
