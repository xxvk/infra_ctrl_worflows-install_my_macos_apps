---
component_id: "opencode"
name: "OpenCode"
category: "Developer CLI"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-formula"
brew_cask: null
brew_formula: "anomalyco/tap/opencode"
official_url: "https://opencode.ai/docs/"
check_command: "opencode --version"
install_after: ["ripgrep"]
account_required: true
permissions_required: []
secrets_policy: "Never store provider API keys, OAuth tokens, prompts, repository content, or agent credentials here."
download_estimate_bytes: 150000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---

# OpenCode

> [!summary] Purpose
> Open-source, provider-neutral terminal coding agent and structured Open
> Design runtime. It is the Core BYOK fallback when a subscription-backed
> agent is unavailable or a different model/provider is required.

## Parameters

| Parameter | Value |
|---|---|
| Delivery | Homebrew formula from the upstream-maintained tap |
| Formula | `anomalyco/tap/opencode` |
| Executable | `opencode` |
| Official source | `https://opencode.ai/docs/` |
| Required tier | Core |
| Install order | `ripgrep`, then OpenCode |
| Account | provider authentication is interactive |
| Permissions | none at installation; agent tool authority is task-specific |

## Installation

The upstream tap is preferred over Homebrew Core because OpenCode documents
that Core may update less frequently. The tap and formula remain subject to
the exact-revision and formula-scoped trust policy in
`references/source-policy.json`.

```sh
brew tap anomalyco/tap
brew trust --formula anomalyco/tap/opencode
brew install anomalyco/tap/opencode
```

Do not trust the entire tap. A package installation does not authorize a
provider login, an API key, repository access, or unattended agent execution.

## Configuration

**Provider Authentication:**
While `opencode providers login` (or `/connect` in older versions) provides an interactive login, configuring API keys via environment variables (e.g., `MINIMAX_API_KEY`, `ARK_API_KEY` in `~/.zshrc`) is strongly recommended for stability, especially when using domestic or custom models. 
*CRITICAL: The user completes every browser login or secret entry. Preserve existing OpenCode configuration and never copy credentials into this guide, the catalog, diagnostics, or Git.*

**Custom Agent Architecture (Multi-Agent Routing):**
OpenCode supports a Primary/Subagent routing architecture. To bypass potential CLI auto-generator (`opencode agent create`) network timeouts, the best practice is to manually author Agent profiles as Markdown files with YAML frontmatter (e.g., `agents/AgentName.md`).
- Define `mode` (`primary` or `subagent`) and `model`.
- Enforce strict `permission` blocks (e.g., restrict subagents to `read`/`webfetch`, reserving `bash`/`edit` for the primary).
- Launch with: `opencode --agent ./agents/<AgentName>.md`.

For Open Design, keep `opencode` on the normal login-shell `PATH`. Open Design
detects it and invokes structured JSON mode; no wrapper or application-bundle
link is required.

## Verification

```sh
command -v opencode
opencode --version
brew list --versions anomalyco/tap/opencode
brew outdated anomalyco/tap/opencode
```

Run an authenticated test only in a trusted disposable repository. A version
result proves package health, not provider access or safe project authority.

## Updates and rollback

Update through the same reviewed source after checking tap revision drift:

```sh
brew upgrade anomalyco/tap/opencode
```

Remove only the formula after explicit approval:

```sh
brew uninstall anomalyco/tap/opencode
```

Do not delete configuration, sessions, authentication state, or project files
during package rollback. Untap `anomalyco/tap` only after confirming no other
installed formula depends on it.

## Evidence and notes

- Documentation: `https://opencode.ai/docs/`
- Repository: `https://github.com/anomalyco/opencode`
- Tap: `https://github.com/anomalyco/homebrew-tap`
- Machine-specific version, path, size, authentication, and verification
  evidence belongs only in machine-local state.
