---
component_id: "eliza-agent-cli"
name: "Eliza Agent CLI (GrokBot)"
category: "AI developer agent"
tier: "core"
lifecycle_status: "active"
source: "github"
delivery_method: "github-source"
brew_cask: null
brew_formula: null
official_url: "https://github.com/elizaOS/eliza"
check_command: "eliza"
install_after: []
account_required: true
permissions_required: []
secrets_policy: "Never store provider API keys, OAuth tokens, subscription sessions, prompts, repository content, or agent credentials here."
download_estimate_bytes: 1000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---

# Eliza Agent CLI (GrokBot)

> [!summary] Purpose
> Core terminal OSINT and autonomous agent framework (Eliza). Supports Grok (xAI) and other LLM providers. Runs locally as a background runtime or interactive Terminal UI (TUI).

## Parameters

| Parameter | Value |
|---|---|
| Delivery | Github clone & `bun` build |
| Executable | `eliza` (Global wrapper script) |
| Account | Requires API keys (e.g., `XAI_API_KEY`) in `.env` |

## Installation & Known Issues

Eliza is a fast-moving monorepo. Installing from the `main` branch directly often fails due to missing plugins or unstable commits.

1. **Clone the repository**:
   ```sh
   git clone https://github.com/elizaOS/eliza.git eliza-agent
   ```

2. **Avoid iCloud Sync Paths**:
   > [!WARNING]
   > Eliza's internal build scripts (`biome` formatting via `execSync`) fail when executed in a path containing spaces (e.g., `Mobile Documents/iCloud~md~obsidian`).
   > You MUST place the `eliza` directory in a local path without spaces (like `~/workspace/eliza` or `/tmp/scratch`) and symlink it to your iCloud vault if access is needed.

3. **Checkout a Stable Tag**:
   Always checkout a stable `beta` or `alpha` tag instead of `main` to ensure the core API server and plugins are linked correctly.
   ```sh
   git fetch --tags
   git checkout v2.0.11-beta.7
   ```

4. **Install and Build**:
   Eliza strictly uses `bun`. Do not use `pnpm` or `npm`.
   ```sh
   bun install
   bun run build
   ```

5. **Fix Missing API Server Plugins**:
   In v2.0-beta versions, the core API server (`serve`) hard-codes imports for edge plugins (e.g. `plugin-x402`), which often fail to build during the bulk `bun run build`. If the API server refuses to start, manually build the missing plugin:
   ```sh
   cd plugins/plugin-x402
   bun run build
   ```

## Configuration

Create a `.env` file from the template and add your API keys:
```sh
cp .env.example .env
# Add XAI_API_KEY=...
```

Create a character JSON file (e.g. `characters/grok_character.json`) to define the persona, set `"modelProvider": "grok"`, and leave `"clients": []` empty if running locally without integrations like Twitter.

> [!IMPORTANT] Database Migration Crashes
> If you switch Eliza versions (e.g., downgrading from `main` to `v2.0.11`), the internal SQLite/PGlite database will be incompatible with the older schema migrations.
> If you encounter SQL migration errors (`Failed query: ALTER TABLE...`), you must wipe the local database to start fresh:
> ```sh
> rm -rf packages/agent/.elizadb
> ```
> *(Note: The database is stored inside the project workspace, not just in `~/.local/state/eliza`)*.

## Execution and Verification

Eliza v2 uses a decoupled architecture. The Terminal UI (`tui`) is just a client and **will fail to connect** if the backend API server (`serve`) is not running simultaneously on port 2138.

Create a global wrapper script (e.g., `~/.local/bin/eliza`) to automate starting both processes and handling clean exit:

```bash
#!/bin/bash
echo "🚀 Starting Eliza Agent Backend..."
cd "/path/to/your/safe/eliza/workspace" || exit 1

# Start backend daemon
bun run start serve > /tmp/eliza-backend.log 2>&1 &
BACKEND_PID=$!

# Wait for API to come online
echo "⏳ Waiting for core engine on port 2138..."
for i in {1..15}; do
    if curl -s http://127.0.0.1:2138 > /dev/null; then
        break
    fi
    sleep 1
done

echo "🖥️ Starting TUI Client..."
bun run start tui

# Clean up backend when TUI exits
echo "🛑 Shutting down backend..."
kill $BACKEND_PID 2>/dev/null
wait $BACKEND_PID 2>/dev/null
echo "👋 Offline."
```

Make it executable and ensure it's in your `$PATH` (or add an alias). Verify by running `eliza`.

## Rollback

To remove Eliza, simply delete the cloned directory, local state, and the wrapper script:
```sh
rm -rf eliza-agent
rm -rf ~/.local/state/eliza
rm ~/.local/bin/eliza
```

## Evidence and notes

- Official Documentation: `https://elizaos.github.io/eliza/`
- Machine-specific version, authentication and verification evidence belongs only in machine-local state.
