# Install My macOS Apps

A personal Codex Skill for setting up a new Mac from a persistent app catalog. It inventories installed apps, selects a storage profile, creates an installation plan, and records follow-up tasks such as account sign-in and permissions.

## Requirements

- macOS
- Python 3 (the scripts use the standard library only)
- Homebrew for automatic Homebrew cask/formula installs
- Codex Chrome extension only when managing an official website download in Chrome

## Start safely

Run every command from this directory. These commands only inspect the Mac and write local records under `state/`:

```sh
python3 scripts/macos_apps.py scan
python3 scripts/macos_apps.py plan --profile auto
```

`portable` applies below 512 GB; `expanded` applies at 512 GB or more. Review the generated plan before choosing one or two apps to install.

```sh
python3 scripts/macos_apps.py install state/PLAN.json --only "App Name"
python3 scripts/macos_apps.py install state/PLAN.json --only "App Name" --apply
```

The first command is a dry run. `--apply` makes external changes and must be used only after explicit review. GUI apps must be opened and checked after installation.

## Docker Desktop retirement

Inspect Docker Desktop before removing it:

```sh
python3 scripts/docker_desktop_cleanup.py inspect
```

Install and verify OrbStack as the default local container backend on every developer Mac, including a new Mac with no Docker Desktop. If Docker Desktop is present, only remove it after OrbStack is verified. Removal permanently deletes Docker Desktop-local containers, images, volumes, build cache, Kubernetes data, and settings. It preserves OrbStack and `~/.docker`.

```sh
python3 scripts/docker_desktop_cleanup.py remove --confirm "REMOVE DOCKER DESKTOP DATA"
```

## Local records

`state/` is intentionally ignored by Git. It contains machine-specific app paths, storage information, and deployment history; keep it locally for continuity but do not commit it.

See [SKILL.md](SKILL.md) for the complete Codex workflow and safety rules.
