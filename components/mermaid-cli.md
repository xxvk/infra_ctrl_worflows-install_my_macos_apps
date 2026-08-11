---
component_id: "mermaid-cli"
name: "Mermaid CLI"
category: "Developer CLI"
tier: "core"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-formula"
brew_cask: null
brew_formula: "mermaid-cli"
official_url: "https://github.com/mermaid-js/mermaid-cli"
check_command: "mmdc --version"
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store browser sessions, private diagram contents, credentials, or rendered private documents here."
download_estimate_bytes: 500000000
download_estimate_method: "formula_plus_puppeteer_browser_planning_estimate"
cli_path: "/opt/homebrew/opt/mermaid-cli"
---
# Mermaid CLI

> [!summary] Purpose
> Core command-line renderer for turning Mermaid source and Mermaid blocks in
> Markdown into SVG, PNG, or PDF. The installed command is `mmdc`. Use it for
> reproducible documentation diagrams, generated reports, and visual
> verification without requiring a browser editor.

## Parameters

| Parameter | Value |
|---|---|
| Delivery | Homebrew formula |
| Package identifier | `mermaid-cli` |
| Official source | `https://github.com/mermaid-js/mermaid-cli` |
| Required tier | Core |
| Install order | none; Homebrew resolves Node |
| Expected download | 500 MB formula + Puppeteer browser planning estimate |
| Expected installed size | measure formula and Puppeteer cache separately |
| CLI path | derive from `brew --prefix mermaid-cli`; command is `mmdc` |
| Account needed | no |
| Permissions | none by default |

## Installation

- [ ] Confirm Homebrew does not already own `mermaid-cli`.
- [ ] Resolve `command -v mmdc` before installation and stop if it belongs to
      an unknown package.
- [ ] Record the current Node and existing Mermaid CLI versions in
      machine-local state.
- [ ] Confirm the selected plan and available disk space.
- [ ] Run the managed dry run with no external changes.
- [ ] Obtain explicit approval before changing package ownership.
- [ ] Install from the official Homebrew formula.

```sh
brew install mermaid-cli
```

The formula depends on Homebrew Node. Follow the Homebrew dependency-upgrade
guard: do not silently upgrade Node or unrelated packages as part of this
installation.

Homebrew's bottle can install the formula without running Puppeteer's browser
download hook. `mmdc --version` then succeeds while rendering fails with
`Could not find chrome-headless-shell`. Complete the installation with the
Puppeteer CLI bundled inside the exact formula instead of invoking a mutable
`npx ...@latest` package:

```sh
"$(brew --prefix mermaid-cli)/libexec/lib/node_modules/@mermaid-js/mermaid-cli/node_modules/.bin/puppeteer" \
  browsers install chrome-headless-shell
```

This resolves the browser build pinned by the installed Puppeteer release and
writes it under `~/.cache/puppeteer`. Treat that cache as a required
machine-local runtime asset, not as disposable application cache. Record its
measured size locally and include it in disk planning.

## Existing npm-global source replacement

An existing `/opt/homebrew/bin/mmdc` may be the symlink created by the global
package `@mermaid-js/mermaid-cli`. Treat that as a source mismatch, even when
its version matches the Homebrew formula. Inspect before replacement:

```sh
command -v mmdc
readlink "$(command -v mmdc)"
npm list -g --depth=0 @mermaid-js/mermaid-cli
brew list --formula --versions mermaid-cli
```

After the user explicitly approves Homebrew ownership, remove only the global
npm package, verify that the old symlink is gone, then install the formula:

```sh
npm uninstall -g @mermaid-js/mermaid-cli
brew install mermaid-cli
```

Do not remove `~/.cache/puppeteer` during source replacement. It is a
machine-local browser asset that may be reused by the Homebrew package. Measure
and review it separately before any cleanup. Do not remove project-local
Mermaid dependencies from `package.json`, lockfiles, or `node_modules`.

## Usage

Render a Mermaid file:

```sh
mmdc -i diagram.mmd -o diagram.svg
mmdc -i diagram.mmd -o diagram.png --backgroundColor transparent
mmdc -i diagram.mmd -o diagram.pdf --pdfFit
```

`mmdc` also extracts Mermaid blocks from Markdown. Generated assets are outputs,
not automatically tracked source: inspect them before adding them to Git.
Icon-pack options may download remote data; use them only from reviewed URLs.

## Verification

```sh
command -v mmdc
brew list --formula --versions mermaid-cli
mmdc --version
"$(brew --prefix mermaid-cli)/libexec/lib/node_modules/@mermaid-js/mermaid-cli/node_modules/.bin/puppeteer" \
  browsers list
printf '%s\n' 'flowchart LR' '  A[Input] --> B[Verified SVG]' \
  | mmdc -i - -o /private/tmp/mermaid-cli-smoke.svg
grep -q '<svg' /private/tmp/mermaid-cli-smoke.svg
```

- [ ] Confirm `command -v mmdc` resolves to Homebrew's linked command.
- [ ] Confirm the formula receipt exists and version output succeeds.
- [ ] Confirm the formula-pinned `chrome-headless-shell` is listed in the
      Puppeteer cache.
- [ ] Confirm a bounded stdin diagram renders to a non-empty SVG.
- [ ] Confirm the SVG contains an `<svg` element.
- [ ] Record path, version, formula size, Puppeteer cache size, and smoke-test
      pass/fail only in machine-local state.

If Chromium/Puppeteer cannot launch, inspect the error, configured executable
path, and machine architecture. Do not weaken Gatekeeper, disable sandboxing,
or download an unreviewed browser binary as a workaround.

A render launched inside a restricted Codex filesystem/process sandbox may
fail on macOS with `sandbox_parameters_mac.mm` and `Input/output error (5)`
even though the installation is valid. Repeat the same bounded smoke test in
the normal host execution context. If it succeeds there, record the restricted
sandbox as the failing interface; never add Chrome's `--no-sandbox` flag.

## Rollback

Uninstalling the formula does not authorize deleting generated diagrams,
project dependencies, or Puppeteer caches:

```sh
brew uninstall mermaid-cli
```

Restoring the npm-global package is a separate external installation and
requires explicit approval. Preserve project-local Mermaid versions because a
repository may intentionally pin a release different from the Core CLI.

## Evidence and notes

- Mermaid CLI repository: `https://github.com/mermaid-js/mermaid-cli`
- Homebrew formula: `mermaid-cli`
- Installed command: `mmdc`

Never paste a machine-local record, completed checkbox, detected version,
rendered private diagram, cache inventory, or timestamp back into this tracked
guide.
