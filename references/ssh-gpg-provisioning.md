# SSH / GPG key provisioning

This is a documentation-only reference. No script here reads, generates,
exports, or persists actual key material — private keys, passphrases, and
`.pem` file contents are permanently out of scope for this skill and must
never appear in `state/`, `settings/`, Markdown, or Git.

## What this Mac's read-only scan already tells you

`developer_environment_profile` in `scripts/macos_preferences.py` records
only the *shape* of `~/.ssh/config` (presence, byte size, sha256) — never
its contents or any key file. A one-time manual inspection of this Mac
(2026-07-19) found:

- No default `~/.ssh/id_ed25519` or `id_rsa` — this Mac does not use a
  single default SSH identity.
- SSH auth is per-project: `~/.ssh/config` maps `Host` aliases to
  project-specific `.pem` files stored under project directories outside
  `~/.ssh/` (e.g. under per-project folders on Desktop), rather than the
  conventional single default identity under `~/.ssh/`. The exact current
  project paths are machine-specific and are intentionally not recorded
  here; see ignored `state/` if a dated snapshot is ever needed.
- An `ssh-agent` socket exists under `~/.ssh/agent/`, but no password
  manager currently supplies SSH-agent forwarding (this user's declared
  secrets source is the system/iCloud Keychain, not 1Password or similar).
- No GPG installation (`gpg` not on `PATH`) and no commit-signing
  configuration — this Mac does not currently use GPG for anything.

## Provisioning strategy for a new Mac

### Project-specific `.pem` keys (the actual current pattern)

These are not reproducible from this repository by design. On a new Mac:

1. Retrieve each `.pem` file from wherever it is actually backed up today
   (a secure note/attachment in the password manager, a project's own
   secrets store, or a teammate/vendor re-issue). This skill does not know
   or manage where that is — it is out of scope the same way license keys
   and account passwords are in `settings/manual-actions.yaml`.
2. Recreate the same project directory structure so `~/.ssh/config`'s
   `IdentityFile` paths resolve without editing the config.
3. Set correct permissions: `chmod 600 <path>.pem`.
4. Verify with `ssh -T <Host alias>` for each entry in `~/.ssh/config`
   before relying on it.

### If a default SSH identity is ever introduced

If a future workflow needs one default keypair (rather than per-project
`.pem` files), generate a fresh one on each new Mac instead of copying a
private key across machines:

```sh
ssh-keygen -t ed25519 -C "<email>@<host>" -f ~/.ssh/id_ed25519
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
```

`--apple-use-keychain` stores the passphrase in the system Keychain,
consistent with this user's declared secrets-manager choice (see
`settings/manual-actions.yaml`). Add the new public key to each remote
service manually; never automate that step, and never commit the private
key or passphrase anywhere.

### GPG (currently unused — optional, only if commit signing is wanted later)

This Mac has no GPG installation today. If the user later wants signed
commits:

```sh
brew install gnupg
gpg --full-generate-key
git config --global user.signingkey <key-id>
git config --global commit.gpgsign true
```

Treat this as a deliberate opt-in, not a default bootstrap step — nothing
today depends on GPG, and adding it unasked would be scope creep.

## Verification checklist for a "new Mac is SSH/GPG-ready" claim

- [ ] Every `Host` alias in `~/.ssh/config` resolves to an existing,
      correctly-permissioned key file.
- [ ] `ssh -T <alias>` succeeds for each configured remote.
- [ ] If GPG signing is in use, `git log --show-signature -1` on a fresh
      commit shows a valid signature.
- [ ] No `.pem` file, private key, or passphrase was ever written to this
      repository's tracked files or to ignored `state/`.
