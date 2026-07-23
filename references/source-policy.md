# Installation source and supply-chain policy

`references/source-policy.json` is the machine-readable policy. The public
catalog declares portable package identity and provenance; tracked `Private/`
configuration may name personally approved high-risk sources; machine-local
state records what a particular Mac actually observed.

## Apply rules

- Never execute a network response directly in a shell.
- Never bootstrap Homebrew automatically from a mutable network script.
- Pin npm globals to exact versions.
- For third-party Homebrew taps, verify the exact repository and full reviewed
  commit before granting trust. Trust only the required cask, never the tap.
- Pin executable GitHub artifacts to a full commit and verify SHA-256 before
  execution.
- Treat every decrypted IPA as critical risk. Keep its approved source label in
  `Private/`, never track a direct download URL, and require per-file hash,
  bundle-ID, decrypted-state, import, and launch verification.
- For vendor downloads without stable hashes, capture the final URL, SHA-256,
  code signature, Gatekeeper assessment, bundle ID, and version in
  machine-local install evidence.

Source drift is a stop condition. Update the policy only after a fresh review;
do not silently accept a changed tap commit, npm version, URL, or artifact hash.
Installed taps that are not catalog-managed remain in
`observed_unmanaged_homebrew` with an explicit disposition; this inventories
them without granting installation authority.

## Commands

Validate tracked definitions without touching the machine:

```sh
python3 scripts/supply_chain.py validate
```

Inspect current Homebrew taps/trust and the two managed npm globals:

```sh
python3 scripts/supply_chain.py inspect
```

After review, capture the observation in machine-local state:

```sh
python3 scripts/supply_chain.py capture \
  --apply \
  --confirm "CAPTURE SUPPLY CHAIN STATE"
```

Capturing is read-only with respect to package managers: it writes evidence but
does not tap, trust, install, update, uninstall, or import anything.
