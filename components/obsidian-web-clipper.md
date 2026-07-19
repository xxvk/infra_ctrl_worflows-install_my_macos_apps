---
component_id: "obsidian-web-clipper-safari"
name: "Obsidian Web Clipper — Safari"
category: "Browser"
tier: "core"
lifecycle_status: "active"
source: "app_store"
delivery_method: "app-store"
brew_cask: null
brew_formula: null
official_url: "https://apps.apple.com/us/app/obsidian-web-clipper/id6720708363"
check_command: "test -d '/Applications/Obsidian Web Clipper.app'"
install_after: ["Obsidian", "Safari"]
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
---
# Obsidian Web Clipper

Obsidian Web Clipper is a Core browser capability with two required targets:
Chrome and Safari. It saves captured content locally to the configured Obsidian
vault; it is not installed through Homebrew.

## Chrome

Install the official extension from the [Chrome Web Store](https://chromewebstore.google.com/detail/obsidian-web-clipper/cnjifjpddelmedmihgijeibhnjfabmlf). This also covers Chromium-based browsers, but Chrome is the required Core target here.

After installation:

- Pin or enable `Obsidian Web Clipper` in Chrome Extensions.
- Set the target vault and destination folder.
- Review site access; prefer `On click` or selected sites unless broader access is explicitly needed.
- Clip one test page and verify a Markdown note appears in the correct vault.

## Safari

Install the official [Obsidian Web Clipper Safari extension](https://apps.apple.com/us/app/obsidian-web-clipper/id6720708363) from the Mac App Store. Then open Safari → Settings → Extensions, enable Obsidian Web Clipper, and review its website permissions.

Configure the same target vault and destination folder, clip one test page, and verify the resulting Markdown note.

## Safety and privacy

- The extension can read pages only according to the browser permission granted by the user.
- Do not grant all-website access unless required by the user's workflow.
- Clipped content may contain private page text, images, and metadata; it is written into the Obsidian vault and must follow that vault's sync/privacy rules.
- Never automate browser sign-in, App Store authentication, or permission approval.
