# Installed Components

These guides are the operational companion to `references/app-catalog.json`.
The catalog remains the source of truth for install metadata; each catalog entry links to its detailed installation, configuration, and verification guide here.

| Component | Guide | Current status |
|---|---|---|
| ChatGPT | [chatgpt.md](chatgpt.md) | Installed; account and version verification required |
| Claude | [claude.md](claude.md) | Installed via Homebrew; VM images reclaimed before replacement |
| Google Chrome | [google-chrome.md](google-chrome.md) | Installed via Homebrew; Codex extension preflight pending |
| Tailscale | [tailscale.md](tailscale.md) | Installed via Mac App Store; connection pending |
| Notion | [notion.md](notion.md) | Installed via Homebrew; workspace verification pending |
| Visual Studio Code | [visual-studio-code.md](visual-studio-code.md) | Installed via Homebrew; extensions/settings pending |
| Cursor | [cursor.md](cursor.md) | Installed via Homebrew; account/settings pending |
| GitHub Desktop | [github-desktop.md](github-desktop.md) | Installed via Homebrew; account/Git settings pending |
| Postman | [postman.md](postman.md) | Installed via Homebrew; workspace verification pending |
| Slack | [slack.md](slack.md) | App Store copy installed; old direct-download copy pending retirement |
| DBeaver Community | [dbeaver-community.md](dbeaver-community.md) | Installed via Homebrew; database connections pending |
| VLC | [vlc.md](vlc.md) | Installed via Homebrew; first-run update choice pending |
| Cyberduck | [cyberduck.md](cyberduck.md) | Installed via Homebrew; server bookmarks pending |
| LM Studio | [lm-studio.md](lm-studio.md) | Installed via Homebrew; model storage pending |
| WebCatalog | [webcatalog.md](webcatalog.md) | Installed via Homebrew; web-app wrappers pending |
| TypeScript | [typescript.md](typescript.md) | Installed via Homebrew; project-local versions may differ |
| fd | [fd.md](fd.md) | Installed via Homebrew |
| fzf | [fzf.md](fzf.md) | Installed via Homebrew; shell integration optional |
| bat | [bat.md](bat.md) | Installed via Homebrew |
| eza | [eza.md](eza.md) | Installed via Homebrew |
| zoxide | [zoxide.md](zoxide.md) | Installed via Homebrew; shell integration optional |
| yq | [yq.md](yq.md) | Installed via Homebrew |
| httpie | [httpie.md](httpie.md) | Installed via Homebrew |
| wget | [wget.md](wget.md) | Installed via Homebrew |
| tree | [tree.md](tree.md) | Installed via Homebrew |
| btop | [btop.md](btop.md) | Installed via Homebrew |
| git-lfs | [git-lfs.md](git-lfs.md) | Installed via Homebrew; Git config pending |
| direnv | [direnv.md](direnv.md) | Installed via Homebrew; shell hook pending |
| just | [just.md](just.md) | Installed via Homebrew |
| shellcheck | [shellcheck.md](shellcheck.md) | Installed via Homebrew |
| shfmt | [shfmt.md](shfmt.md) | Installed via Homebrew |
| pre-commit | [pre-commit.md](pre-commit.md) | Installed via Homebrew |
| cmake | [cmake.md](cmake.md) | Installed via Homebrew |
| ninja | [ninja.md](ninja.md) | Installed via Homebrew |
| pkgconf | [pkgconf.md](pkgconf.md) | Installed via Homebrew |
| Obsidian | [obsidian.md](obsidian.md) | Installed via Homebrew; vault verification pending |
| GitHub CLI (`gh`) | [github-cli.md](github-cli.md) | Installed and authenticated |
| Ghostty | [ghostty.md](ghostty.md) | Installed and configured |
| mole | [mole.md](mole.md) | Installed; first cleanup review pending |
| Docker Desktop | [docker-desktop.md](docker-desktop.md) | Retired; OrbStack retained as the default replacement |

When adding a new app guide, start from `../templates/app-component.md`, add the guide to this table, and add its relative `guide` path to the matching catalog entry.
