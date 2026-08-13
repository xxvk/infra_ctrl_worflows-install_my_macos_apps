# Contributing

Thank you for helping improve macomrade. Contributions should preserve its
local-first, privacy-bounded, preview-before-mutation behavior.

## Before opening an issue

- Search existing issues and documentation.
- Remove account identifiers, machine usernames, private URLs, credentials,
  raw authorization databases, sessions, private filenames, and document
  contents.
- Do not upload `Private/`, machine-local state, full support archives, or
  unredacted command output.
- Report security-sensitive findings through `SECURITY.md`, not a public issue.

Use the repository's structured issue forms and read
[`references/public-support-safety.md`](references/public-support-safety.md)
before sharing command output or diagnostic evidence.

## Development workflow

Use macOS and Python 3. Make one focused change, update tests and relevant
documentation together, and keep public fixtures fictional. Before submitting:

```sh
python3 scripts/icloud_git_guard.py inspect --repo .
python3 scripts/release_check.py
git diff --check
```

The hermetic release check is the default authority. Live macOS checks are
supplementary and must never grant permissions, install software, alter an
account, or perform cleanup merely because a pull request runs them.

## Change requirements

- Preserve read-only defaults and explicit confirmations.
- Keep detected state outside Git and personal intent under Git-ignored
  `Private/`.
- Add or update a JSON Schema when a persistent format changes.
- Add tests for new behavior and negative safety boundaries.
- Keep component frontmatter complete and machine state out of component docs.
- Update English, Japanese, and Simplified Chinese user-facing messages
  together when localization applies.
- Document rollback and independent read-back for every mutation.

By submitting a contribution, you agree that it is provided under the Apache
License 2.0 unless you clearly state otherwise before submission. No separate
contributor license agreement is currently required.
