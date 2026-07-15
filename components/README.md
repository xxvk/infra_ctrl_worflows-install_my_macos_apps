# Installed Components

These guides are the operational companion to `references/app-catalog.json`.
The catalog remains the source of truth for install metadata; each catalog entry links to its detailed installation, configuration, and verification guide here.

| Component | Guide | Current status |
|---|---|---|
| GitHub CLI (`gh`) | [github-cli.md](github-cli.md) | Installed and authenticated |
| Ghostty | [ghostty.md](ghostty.md) | Installed and configured |
| mole | [mole.md](mole.md) | Installed; first cleanup review pending |

When adding a new app guide, start from `../templates/app-component.md`, add the guide to this table, and add its relative `guide` path to the matching catalog entry.
