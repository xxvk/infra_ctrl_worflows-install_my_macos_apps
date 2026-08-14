# Component guides

These guides are the operational companion to `references/app-catalog.json`.
The catalog remains the source of truth for install metadata; each catalog entry links to its detailed installation, configuration, and verification guide here.

This index describes desired lifecycle and reproducible source only. Installation
and verification status belongs to machine-local state.

| Component | Guide | Desired role / source |
|---|---|---|
| ChatGPT | [chatgpt.md](chatgpt.md) | Core; Homebrew; verify account per Mac |
| Claude | [claude.md](claude.md) | Core; Homebrew; inspect VM policy per Mac |
| Google Chrome | [google-chrome.md](google-chrome.md) | Core; Homebrew; profile verification required |
| Obsidian Web Clipper | [obsidian-web-clipper.md](obsidian-web-clipper.md) | Core; Chrome extension and Safari extension required |
| Tailscale | [tailscale.md](tailscale.md) | Core; Mac App Store; connect per Mac |
| Notion | [notion.md](notion.md) | Retired; use the web version or web app |
| Visual Studio Code | [visual-studio-code.md](visual-studio-code.md) | Core; Homebrew; reusable settings apply separately |
| Cursor | [cursor.md](cursor.md) | Core; Homebrew; verify account per Mac |
| GitHub Desktop | [github-desktop.md](github-desktop.md) | Core; Homebrew; verify account and Git settings per Mac |
| Sourcetree | [sourcetree.md](sourcetree.md) | Core; Homebrew; embedded Git and multiple hosting accounts |
| Postman | [postman.md](postman.md) | Core; Homebrew; verify workspace per Mac |
| Slack | [slack.md](slack.md) | Core; Mac App Store; retain one verified bundle |
| DBeaver Community | [dbeaver-community.md](dbeaver-community.md) | Core; Homebrew; connections are per Mac |
| Redis CLI | [redis-cli.md](redis-cli.md) | Core; Homebrew formula; local service stays stopped by default |
| VLC | [vlc.md](vlc.md) | Core; Homebrew; review first-run update choice |
| Cyberduck | [cyberduck.md](cyberduck.md) | Core; Homebrew; bookmarks apply separately |
| LM Studio | [lm-studio.md](lm-studio.md) | Retired; Bionic is the replacement |
| WebCatalog | [webcatalog.md](webcatalog.md) | Core; Homebrew; wrappers apply separately |
| TypeScript | [typescript.md](typescript.md) | Core; Homebrew; project-local versions may differ |
| fd | [fd.md](fd.md) | Core; Homebrew |
| fzf | [fzf.md](fzf.md) | Core; Homebrew; shell integration optional |
| bat | [bat.md](bat.md) | Core; Homebrew |
| eza | [eza.md](eza.md) | Core; Homebrew |
| zoxide | [zoxide.md](zoxide.md) | Core; Homebrew; shell integration optional |
| yq | [yq.md](yq.md) | Core; Homebrew |
| httpie | [httpie.md](httpie.md) | Core; Homebrew |
| wget | [wget.md](wget.md) | Core; Homebrew |
| tree | [tree.md](tree.md) | Core; Homebrew |
| btop | [btop.md](btop.md) | Core; Homebrew |
| git-lfs | [git-lfs.md](git-lfs.md) | Core; Homebrew; Git config applies separately |
| direnv | [direnv.md](direnv.md) | Core; Homebrew; shell hook applies separately |
| just | [just.md](just.md) | Core; Homebrew |
| shellcheck | [shellcheck.md](shellcheck.md) | Core; Homebrew |
| shfmt | [shfmt.md](shfmt.md) | Core; Homebrew |
| pre-commit | [pre-commit.md](pre-commit.md) | Core; Homebrew |
| cmake | [cmake.md](cmake.md) | Core; Homebrew |
| ninja | [ninja.md](ninja.md) | Core; Homebrew |
| pkgconf | [pkgconf.md](pkgconf.md) | Core; Homebrew |
| Obsidian | [obsidian.md](obsidian.md) | Core; Homebrew; verify vault per Mac |
| GitHub CLI (`gh`) | [github-cli.md](github-cli.md) | Core; Homebrew; authenticate per Mac |
| tamnd/x-cli (`x`) | [tamnd-x-cli.md](tamnd-x-cli.md) | Core; free, strictly read-only X access; pinned GitHub release |
| Mermaid CLI (`mmdc`) | [mermaid-cli.md](mermaid-cli.md) | Core; Homebrew; Mermaid-to-SVG/PNG/PDF rendering |
| Ghostty | [ghostty.md](ghostty.md) | Core; Homebrew; tracked visual baseline |
| deno | [deno.md](deno.md) | Core; Homebrew |
| fnm | [fnm.md](fnm.md) | Core; Homebrew |
| jenv | [jenv.md](jenv.md) | Core; Homebrew |
| Maven | [maven.md](maven.md) | Core; Homebrew |
| Android command-line tools | [android-commandlinetools.md](android-commandlinetools.md) | Core; SDK workflow in [environment.md](../references/environment.md) |
| Android platform tools | [android-platform-tools.md](android-platform-tools.md) | Core; ADB workflow in [environment.md](../references/environment.md) |
| scrcpy | [scrcpy.md](scrcpy.md) | Core; Android Robot remote display/control |
| Temurin Java | [temurin.md](temurin.md) | Core; Android/Java runtime |
| Google Cloud CLI | [gcloud-cli.md](gcloud-cli.md) | Core; Homebrew |
| Kimi | [kimi.md](kimi.md) | Core; Homebrew cask preferred |
| Cloudflare Wrangler | [cloudflare-wrangler.md](cloudflare-wrangler.md) | Core; npm |
| WordPress Studio CLI | [wordpress-studio-cli.md](wordpress-studio-cli.md) | Core; official npm package |
| mole | [mole.md](mole.md) | Core; Homebrew; review every cleanup |
| Docker Desktop | [docker-desktop.md](docker-desktop.md) | Retired; OrbStack retained as the default replacement |
| Antigravity CLI | [antigravity-cli.md](antigravity-cli.md) | Core replacement for retired Gemini CLI |

## Optional components

These guides are cataloged for review but are not installed automatically during a Core deployment.

| Component | Guide | Preferred source |
|---|---|---|
| Brave Browser | [brave-browser.md](brave-browser.md) | Homebrew |
| DingTalk | [dingtalk.md](dingtalk.md) | Official website |
| Redis Insight | [redis-insight.md](redis-insight.md) | Mac App Store; advanced visual Redis workflows |
| Microsoft Excel | [microsoft-excel.md](microsoft-excel.md) | Mac App Store |
| FileZilla | [filezilla.md](filezilla.md) | Official website; Homebrew cask unavailable |
| Android File Transfer | [android-file-transfer.md](android-file-transfer.md) | Official website |
| Xcode | [xcode.md](xcode.md) | Mac App Store |
| Android Studio | [android-studio.md](android-studio.md) | Official website |
| Android Studio Preview | [android-studio-preview.md](android-studio-preview.md) | Official website |
| WordPress Studio | [wordpress-studio.md](wordpress-studio.md) | Official website |
| Cherry Studio | [cherry-studio.md](cherry-studio.md) | Optional multi-model and Agent workbench |
| Logi Options+ | [logi-options-plus.md](logi-options-plus.md) | Homebrew Cask |
| Solaar | [solaar.md](solaar.md) | GitHub source; Homebrew dependencies |
| xurl | [xurl.md](xurl.md) | Optional official X API CLI; credits and OAuth required for API calls |
| Affinity | [affinity.md](affinity.md) | Official website |
| CapCut | [capcut.md](capcut.md) | Mac App Store |
| Compressor | [compressor.md](compressor.md) | Mac App Store |
| DaVinci Resolve | [davinci-resolve.md](davinci-resolve.md) | Mac App Store / Blackmagic website |
| Final Cut Pro | [final-cut-pro.md](final-cut-pro.md) | Mac App Store |
| Logic Pro | [logic-pro.md](logic-pro.md) | Mac App Store |
| MainStage | [mainstage.md](mainstage.md) | Mac App Store |
| Motion | [motion.md](motion.md) | Mac App Store |
| Capacities | [capacities.md](capacities.md) | Retired and removed |
| Foxglove | [foxglove.md](foxglove.md) | Optional robotics development |
| Google Docs / Sheets / Slides | [google-workspace-web-apps.md](google-workspace-web-apps.md) | Core web-app shortcuts |
| Apple Developer | [apple-developer.md](apple-developer.md) | Mac App Store |
| PlayCover Learning Apps | [playcover-learning-apps.md](playcover-learning-apps.md) | Optional PlayCover apps |

When adding a new app guide, start from `../templates/app-component.md`, add the guide to this table, and add its relative `guide` path to the matching catalog entry.
