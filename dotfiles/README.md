# Dotfiles reproduction

This directory is the tracked source of truth for reproducing shell/dev
config on a new Mac. It closes the gap `developer_environment_profile`
(`scripts/macos_preferences.py`) deliberately leaves open: that scan only
records the *shape* of startup files (byte size, sha256), never their
contents, so a new machine has nothing to restore from.

## Convention

- A file placed at `dotfiles/home/<relative-path>` mirrors
  `$HOME/<relative-path>`. Example: `dotfiles/home/.zshrc` maps to
  `~/.zshrc`.
- Only add a file here after manually reviewing it and stripping anything
  private: no API keys, tokens, host-specific paths, machine names, or
  anything from `secrets_policy` lists elsewhere in this skill. Treat this
  directory as public-repo-safe.
- Deployment is by symlink, never by copy, so future edits to the live file
  are edits to the tracked file (and vice versa) — there is nothing to keep
  back in sync.
- Nothing in this directory is applied automatically. Use
  `scripts/dotfiles_sync.py status` to preview, and `link` to apply, always
  with an explicit backup of whatever the destination previously held.

## Populating this directory (first-time setup on this Mac)

Nothing is currently tracked here. To seed it:

1. Pick one managed file at a time (start with something low-risk, e.g. a
   `.gitconfig` alias block or `.zshrc` aliases/functions section — not the
   whole file if it sources anything private).
2. Copy only the reviewed, secret-free content into
   `dotfiles/home/<relative-path>`.
3. Run `python3 scripts/dotfiles_sync.py status` to confirm it's tracked
   and see whether the live file already matches.
4. Commit the new tracked file normally.

## Applying on a new Mac

```sh
python3 scripts/dotfiles_sync.py status   # preview: what would change
python3 scripts/dotfiles_sync.py link     # symlink tracked files into $HOME
python3 scripts/dotfiles_sync.py status   # re-verify after linking
```

`link` backs up any pre-existing non-symlink file at the destination to
`<path>.pre-dotfiles-backup-<timestamp>` before replacing it with a symlink;
it never deletes without backing up first, and it never touches a file that
is already the correct symlink.
