---
component_id: "wordpress-studio"
name: "WordPress Studio"
category: "Web development"
tier: "optional"
lifecycle_status: "active"
source: "homebrew"
delivery_method: "homebrew-cask"
brew_cask: "wordpresscom-studio"
brew_formula: null
official_url: "https://developer.wordpress.com/studio/"
check_command: null
install_after: []
account_required: false
permissions_required: []
secrets_policy: "Never store passwords, API keys, recovery codes, or license secrets here."
download_estimate_bytes: 1000000000
download_estimate_method: "catalog_size_gb_planning_estimate"
---
# WordPress Studio

Optional local WordPress development environment from the WordPress.com team.
It is useful when building or testing WordPress themes and plugins locally, not
as a general-purpose web development runtime.

## When to use

- Create reproducible local WordPress sites with Blueprints.
- Import an existing site or custom theme/plugin code.
- Use local domains, SSL, debug logs, phpMyAdmin, and Xdebug.
- Sync or push to WordPress.com/Pressable only after reviewing the target.

## Install

Preferred installation:

```sh
brew install --cask wordpresscom-studio
```

The official DMG remains a fallback when Homebrew is unavailable. Do not add
it to Core unless WordPress development becomes a recurring requirement.

The `studio` CLI is a separate deliverable. The official installation options
are the WordPress installer script or `npm install -g wp-studio`; install it
only when CLI automation, Studio Sync, previews, or agent workflows require it.
