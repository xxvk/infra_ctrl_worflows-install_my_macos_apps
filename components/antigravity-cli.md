---
component_id: "antigravity-cli"
name: "Antigravity CLI"
category: "Developer CLI"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "antigravity-cli"
brew_formula: null
official_url: "https://antigravity.google/product/antigravity-cli"
check_command: "agy"
install_after: []
account_required: true
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
---

# Antigravity CLI (`agy`)

> [!summary] Purpose
> Google Antigravity's terminal interface for agent workflows. This is the replacement path for the retired Homebrew `gemini-cli` package.

## Parameters

| Parameter | Value |
|---|---|
| Delivery | Homebrew cask |
| Package identifier | `antigravity-cli` |
| Official source | https://antigravity.google/product/antigravity-cli |
| Required tier | core |
| Install order | none |
| CLI command | `agy` |
| Account needed | yes, interactive only |
| Permissions | Review any requested workspace or code-access permissions |

## Installation

```sh
brew install --cask antigravity-cli
```

The cask links the Antigravity CLI binary as `agy`. Treat versions as runtime
state: verify with `agy --version` and use `agy changelog` plus `agy update`
instead of keeping a release number in this reusable guide.

## Configuration

Run sign-in or credential setup interactively when prompted. Never store tokens, passwords, recovery codes, or API keys in this guide, the catalog, or state logs.

## Verification

```sh
command -v agy
agy --version
agy models --output-format json
agy -p '/help' --output-format json
agy -p '/usage' --output-format json
```

- [ ] Confirm the binary is on PATH.
- [ ] Confirm the version output.
- [ ] Complete account sign-in yourself if required.
- [ ] Confirm the CLI can access only the intended workspace and repositories.

## Headless operation and quota accounting

Use print mode for scripts. Prefer JSON whenever the caller needs stable status,
token accounting, or quota values:

```sh
agy -p 'Reply exactly OK' \
  --model 'Gemini 3.1 Pro (Low)' \
  --mode plan \
  --output-format json \
  --print-timeout 120s
```

The result's `usage` object reports `input_tokens`, `output_tokens`,
`thinking_tokens`, `cache_read_tokens`, and `total_tokens`. Thinking tokens are
reported as a subset of output accounting: verify totals from the returned JSON
rather than summing every displayed field independently.

`/usage` (alias `/quota`) is a local slash command that reports the shared
Gemini and third-party quota buckets without starting an agent turn:

```sh
agy -p '/usage' --output-format json
```

Read `command.data.groups[].buckets[].remaining_fraction` for the precise
balance and `reset_time` for the window reset. The human-readable response is
rounded to a whole percentage. Gemini Flash and Gemini Pro share a weekly
bucket and a five-hour bucket. Claude and GPT models use a separate weekly and
five-hour group. Quota consumption is proportional to token cost, so it cannot
be reconstructed reliably from request count alone. `/usage` should return
`num_turns: 0` and zero tokens; treat any nonzero result as a behavior change.

Useful non-agent slash commands include `/help`, `/config` (`/settings`),
`/credits`, `/model`, `/skills`, `/permissions`, `/changelog`, and `/usage`.
Discover the current list instead of assuming it is stable:

```sh
agy -p '/help' --output-format json
```

## Account and compatibility boundaries

`agy` does not currently expose a supported `account`, `auth`, or `whoami`
subcommand, and model/usage JSON does not identify the signed-in email. Verify
the visible account in Antigravity Settings before a sensitive run. Never infer
account identity from a successful model call and never automate account
switching.

Personal Google-account OAuth for the legacy `gemini` CLI may authenticate in
the browser and still fail at the Code Assist eligibility step with
`UNSUPPORTED_CLIENT`, directing the user to Antigravity. This is not an invalid
authorization-code diagnosis. For a subscription-backed individual workflow,
test the same account through `agy`; keep Gemini API-key, Vertex AI, and
enterprise Code Assist routes as separate authentication and billing paths.

## Replacement procedure

Install and verify `agy` first. Only then retire and remove `gemini-cli`:

```sh
brew uninstall gemini-cli
```

Record the uninstall evidence in `state/`; do not delete the old CLI before the replacement passes verification.

## Rollback

To restore the previous CLI, reverse the lifecycle change in the catalog and reinstall its verified formula:

```sh
brew install gemini-cli
```

## Evidence and notes

- Homebrew availability checked 2026-07-16.
- `gemini-cli` is marked `lifecycle_status: retired` in the catalog after this replacement is verified.
- Keep subscription counts, account identifiers, current balances, installed
  versions, and dated test results in Private or machine-local state, never in
  this reusable public guide.
