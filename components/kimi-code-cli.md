---
component_id: "kimi-code-cli"
name: "Kimi Code CLI"
category: "AI developer agent"
tier: "core"
lifecycle_status: "active"
source: "official_web"
delivery_method: "shell-script"
brew_cask: null
brew_formula: null
official_url: "https://code.kimi.com/kimi-code/"
check_command: "kimi --version"
install_after: []
account_required: true
permissions_required: []
secrets_policy: "Never store provider API keys, OAuth tokens, subscription sessions, prompts, repository content, or agent credentials here."
download_estimate_bytes: 50000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---

# Kimi Code CLI

> [!summary] Purpose
> Core terminal coding agent. Kimi CLI supports Moonshot official provider as well as other compatible providers, running tools in the current user account and trusted workspace.

## Parameters

| Parameter | Value |
|---|---|
| Delivery | `shell-script` via official curl |
| Executable | `kimi` (at `~/.kimi-code/bin/kimi`) |
| Account | Requires Kimi login or API key configuration |

## Installation

Install using the official bash script. Note that this installs Kimi into `~/.kimi-code` and updates `~/.zshrc` automatically:

```sh
curl -fsSL https://code.kimi.com/kimi-code/install.sh | bash
```

Reload your shell or source `~/.zshrc` to make `kimi` available in your PATH.

## Verification

```sh
~/.kimi-code/bin/kimi --version
~/.kimi-code/bin/kimi --help
```

To verify the model configuration is working:
```sh
kimi -p "Hello, please reply 'pong' if you hear me."
```

## Authentication and configuration

By default, run `/login` inside the interactive Kimi CLI interface, or authenticate via device flow:
```sh
kimi login
```

### Moonshot API Key (Production)
You can configure Kimi CLI to use the official Moonshot provider with an API key non-interactively:
```sh
kimi provider catalog add moonshotai-cn --api-key <YOUR_API_KEY>
```

Set the default model in `~/.kimi-code/config.toml`:
```toml
default_model = "moonshotai-cn/kimi-k2.7-code"

[providers.moonshotai-cn]
# ...
```

**Note:** For initial testing, `kimi-k3` is an acceptable default. For production-scale tasks, it is highly recommended to switch to `kimi-k2.7-code` to significantly reduce API cost without sacrificing code generation capability.


### Multi-Agent and Mixed Model Roles
Kimi Code CLI supports delegating to specific subagents configured via Markdown files. You can mix flagship models (e.g., `kimi-k3`) for complex planning and specialized/cheaper models (e.g., `kimi-k2.7-code`) for routine tasks to optimize cost.

1. **Configure Model Tiers**
   Define a `secondary_model` alongside the `default_model` in `~/.kimi-code/config.toml`:
   ```toml
   default_model = "moonshotai-cn/kimi-k3"
   [secondary_model]
   model = "moonshotai-cn/kimi-k2.7-code"
   ```

2. **Define Agent Preferences**
   In your custom agent profile (e.g., `agents/code-reviewer.md`), declare `model_preference: secondary` in the YAML frontmatter:
   ```yaml
   ---
   name: code-reviewer
   description: Specialized agent for routine linting and reviews
   model_preference: secondary
   ---
   # Code Reviewer
   Instructions...
   ```
   When invoked via `--agent-file` or delegated by the main agent, Kimi will automatically switch to the `secondary_model`.

## Rollback

To remove Kimi CLI, simply delete the installation folder and remove its reference from `~/.zshrc`:
```sh
rm -rf ~/.kimi-code
```

## Evidence and notes

- Official Documentation: `https://moonshotai.github.io/kimi-code/`
- Configuration file location: `~/.kimi-code/config.toml`
- Machine-specific version, authentication and verification evidence belongs only in machine-local state.
