---
component_id: "tamnd-x-cli"
name: "tamnd/x-cli"
category: "Developer tools"
tier: "core"
lifecycle_status: "active"
source: "github"
delivery_method: "github-source"
brew_cask: null
brew_formula: null
official_url: "https://tamnd.github.io/x-cli/"
check_command: "x version"
github_repository: "https://github.com/tamnd/x-cli"
github_release: "v0.5.0"
github_revision: "ff9aa9e77c415b724c115a0ee8f7a978784c9b68"
github_artifact: "x_0.5.0_darwin_arm64.tar.gz"
artifact_sha256: "6de9cde491c10aa9455f37e73beaba9b469e58de93940ba8db1aeca2ee77a705"
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store X auth_token, ct0, Cookie headers, guest tokens, session files, or the authenticated data directory in Git, logs, diagnostics, or machine-state records."
download_estimate_bytes: 6509623
download_estimate_method: "release_asset_size_v0.5.0"
---
# tamnd/x-cli

> [!summary] Purpose
> Default X reading CLI for the baseline. It is free, strictly read-only, uses
> public or browser-facing X surfaces instead of paid X API credits, and can
> expose the same read tools to agents through its local MCP mode.

## Parameters

| Parameter | Value |
|---|---|
| Delivery | pinned GitHub release binary |
| Package identifier | `tamnd/x-cli` |
| Official source | `https://github.com/tamnd/x-cli` |
| Required tier | `core` |
| Install order | none |
| Expected download | 6,509,623 bytes for the pinned arm64 archive |
| Expected installed size | unknown; measure per Mac |
| Config path(s) | resolve with `x config path`; all state remains machine-local |
| Account needed | no for Tier 0 and guest reads; optional for session-only reads |
| Permissions | none by default; browser session import requires explicit approval |

## Role in the X toolchain

Use `tamnd/x-cli` first for profiles, posts, threads, timelines, media, search,
and other reads. It has no follow, unfollow, post, like, delete, or other write
command. Retain optional `xurl` only for official X API endpoints or explicitly
confirmed account writes.

| Need | Tool |
|---|---|
| Free read from public or browser-facing X surfaces | `x` |
| Official API endpoint or paid reliability | optional `xurl` |
| Follow, unfollow, posting, or other mutation | optional `xurl`, with confirmation |

Read [X CLI operations](../references/x-cli-operations.md) for the bounded
profile and timeline commands, identity checks, and the handoff to official
`xurl` for confirmed account writes.

## Installation

The baseline uses the signed, pinned macOS arm64 release rather than mutable
`go install ...@latest`. Before installing, stop if `command -v x` resolves to
an unrelated binary. Do not overwrite an existing command without a reviewed
replacement plan.

```sh
curl -fL \
  https://github.com/tamnd/x-cli/releases/download/v0.5.0/x_0.5.0_darwin_arm64.tar.gz \
  -o /private/tmp/x_0.5.0_darwin_arm64.tar.gz
echo "6de9cde491c10aa9455f37e73beaba9b469e58de93940ba8db1aeca2ee77a705  /private/tmp/x_0.5.0_darwin_arm64.tar.gz" \
  | shasum -a 256 -c -
mkdir -p /private/tmp/macomrade-x-cli-v0.5.0 "$HOME/.local/bin"
tar -xzf /private/tmp/x_0.5.0_darwin_arm64.tar.gz \
  -C /private/tmp/macomrade-x-cli-v0.5.0
install -m 0755 /private/tmp/macomrade-x-cli-v0.5.0/x "$HOME/.local/bin/x"
```

The reviewed archive contains only `LICENSE`, `NOTICE`, `README.md`, and `x`.
Its official checksum manifest signature identifies
`https://github.com/tamnd/x-cli/.github/workflows/release.yml@refs/tags/v0.5.0`.
Source drift, a different asset hash, or an unexpected archive member is a stop
condition requiring a fresh supply-chain review.

If `$HOME/.local/bin` is not already in `PATH`, add one labelled, idempotent
PATH block to the active shell startup file. Preserve unrelated shell settings.

## Read tiers

Start with the least privileged tier that can answer the request:

1. Tier 0: no authentication; use it for posts, profiles, recent timelines,
   threads, media, trends, and other public reads.
2. Guest: add `--guest` only when a deeper supported public read is needed.
3. Session: import browser session cookies only after the user explicitly asks
   for a session-only read such as full search, followers/following, home, or
   bookmarks.

```sh
x tweet <post-id>
x user <username>
x timeline <username> -n 20
x timeline <username> --guest -n 50
```

Keep the default request pacing and disk cache. Do not lower the rate delay,
loop aggressively, rotate identities, or automate measures intended to evade X
limits. These browser-facing surfaces are unofficial and may change without
notice; a failure is not authorization to broaden access automatically.

## Optional session import

Session import is not part of installation or core verification. If the user
explicitly requests a session-only read, explain that `auth_token` and `ct0`
are equivalent to login credentials, then let the user provide the Cookie
header interactively without placing secrets in shell history:

```sh
pbpaste | x auth import
x auth status
```

Never extract browser cookies automatically, print them, copy them between
Macs, or include the x data directory in Git, backups, machine state, or a
diagnostic bundle. Determine the local path with `x config path`; do not assume
one cross-platform location.

## Verification

Verify the binary and default no-auth behavior first:

```sh
command -v x
x version
x --tier 0 tweet 20
x doctor
```

- [ ] Confirm `command -v x` resolves to the managed binary.
- [ ] Confirm the detected version matches the pinned release.
- [ ] Confirm a bounded Tier 0 read succeeds without an X Developer account.
- [ ] Confirm no session is required for core verification.
- [ ] Record only non-secret pass/fail, path, version, size, and timestamp in
      machine-local state.

The built-in local MCP server is optional. Enable `x mcp` only for a specific
agent workflow, bind it locally, expose only read operations, and stop it when
the workflow ends.

## Follow-up

- [ ] Test guest mode only if Tier 0 cannot return enough of a public timeline.
- [ ] Import a session only when a named session-only read is required.
- [ ] Use optional `xurl` only when this read-only CLI cannot satisfy an
      official-endpoint requirement.

## Rollback

Removing a saved session is a separate credential action:

```sh
x auth logout
```

Uninstall only when `command -v x` confirms the managed path:

```sh
rm "$HOME/.local/bin/x"
```

Preserve the data directory, local SQLite stores, and caches unless the user
separately approves their deletion after reviewing `x config path`. Remove the
labelled PATH block only when no other tool uses `$HOME/.local/bin`.

## Evidence and notes

- Release: `https://github.com/tamnd/x-cli/releases/tag/v0.5.0`
- Repository revision: `ff9aa9e77c415b724c115a0ee8f7a978784c9b68`
- Apple Silicon artifact SHA-256:
  `6de9cde491c10aa9455f37e73beaba9b469e58de93940ba8db1aeca2ee77a705`
- The release tag and commit are GitHub Verified. The downloaded checksum
  manifest's signature matched its certificate, whose identity is the tagged
  release workflow recorded above.
- Machine-specific installation, path, session, cache, account, and runtime
  results belong only in machine-local state.

Never paste a machine-local record, completed checkbox, detected version,
installed path, session identity, Cookie, cache, measurement, or timestamp back
into this tracked guide.
