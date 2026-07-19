---
component_id: "lm-studio"
name: "LM Studio"
category: "Local AI"
tier: "optional"
lifecycle_status: "retired"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "lm-studio"
brew_formula: null
official_url: "https://lmstudio.ai/"
check_command: null
install_after: []
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
---
## Retirement status

Classic LM Studio is retired in this catalog in favor of LM Studio Bionic.
Bionic and classic LM Studio use the same `llmster` daemon and must not run
their local backends concurrently. See [bionic.md](bionic.md) for the active
workflow. Preserve shared `~/.lmstudio` model data unless cleanup is explicitly
approved.

## Historical role and Gateway boundaries

LM Studio is the local inference backend. Start its server from the Developer
tab or with `lms server start`; the default local address is
`http://localhost:1234`. It exposes OpenAI-compatible endpoints and an
Anthropic-compatible `POST /v1/messages` endpoint. This makes it suitable as a
Claude Desktop-compatible local backend for models loaded into LM Studio.

LM Studio should not be treated as a cloud-provider key vault or transparent
proxy. In particular, do not assume that a DeepSeek official API key can be
entered into LM Studio and forwarded to DeepSeek's hosted endpoint. For one
Claude Desktop profile covering OpenRouter, DeepSeek, Google, and LM Studio,
place a separately evaluated routing layer in front and keep provider secrets
there. Verify the exact model ID, streaming, tool calls, and error behavior per
provider.

## Bionic migration

The active Bionic guide is [bionic.md](bionic.md). Do not reinstall classic
LM Studio merely to manage a daemon already used by Bionic.

## Bionic capability map

The installed Bionic preview should be verified against the following official
capability map:

- **Work Projects:** research, writing, analysis, and document work in a
  Bionic-managed workspace. It can work with PDFs, images, text, spreadsheets,
  presentations, and other non-code files, and can create deliverables.
- **Code Projects:** connect a local repository or folder, index it for search,
  inspect and explain code, edit multiple files, use Git and shell tools, add
  tests, update documentation, and review multi-file changes.
- **Sessions and tabs:** keep separate task threads inside projects, run
  sessions in the background, open project files and browser pages as tabs,
  compare sessions side by side, and fork eligible responses.
- **Model choices:** use a local model on this Mac, a model on another device
  through LM Link, or an open model through LM Studio Secure Cloud. The model
  picker can expose reasoning controls when the selected model supports them.
- **Web Search:** available for Work Projects when enabled in Settings and
  when the account has billing configured.

### Data-routing and billing rules

Local and LM Link models do not consume Bionic cloud credits and can be used
without an LM Studio account. Secure Cloud models require network access, a
signed-in account, available personal or organization credits, and transient
processing under LM Studio's Zero Data Retention policy. Verify the selected
model route before sending private documents or source code.

For every first-use verification, record only the route (`local`, `remote`, or
`cloud`), model name, feature tested, and pass/fail. Never store account
credentials, billing data, API keys, or document contents in this guide.

## Operational guardrails

- Keep model storage capacity under review; downloaded models are separate from
  the app footprint and can be much larger.
- Do not expose a local model server to the network without explicit review.
- If using DGX Spark, enable LAN serving only on a trusted network and require
  authentication where available.
