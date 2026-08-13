# Public support and safety contract

This contract defines what may be reported publicly, what must remain private,
and how diagnostic evidence moves from local preview to an explicitly reviewed
attachment. It applies to issues, pull requests, discussions, email, and every
other support channel.

## Public issue or private security report

| Situation | Channel | Minimum safe content |
| --- | --- | --- |
| Reproducible non-security bug with no private data | Public bug form | Version, macOS version, architecture, command, expected result, and manually redacted error category. |
| Feature or documentation request | Public feature form | User need, desired outcome, boundaries, and a fictional example. |
| Suspected vulnerability, unsafe mutation, credential exposure, private-data disclosure, or redaction bypass | Private route in `SECURITY.md` | Smallest safe reproduction and impact; omit live secrets and unrelated personal data. |
| Unsure whether evidence is sensitive | Private route in `SECURITY.md` | Describe the category first and wait for a bounded evidence request. |

A draft issue, maintainer request, successful diagnostic export, or passing
test never authorizes publication of private material. Public reports must use
the issue forms and remain independently understandable without the author's
Private overlay.

## Never share

Do not paste, attach, commit, or upload any of the following:

- passwords, passkeys, recovery codes, API keys, OAuth/access/refresh tokens,
  authorization headers, cookies, sessions, private keys, or signing material;
- `Private/` files or values, account identifiers, profile mappings, private
  URLs, personal filenames, document contents, browser data, message content,
  contact lists, or membership graphs;
- raw TCC databases or rows, Keychain exports, complete preference databases,
  home-directory archives, crash dumps with unreviewed memory, or full vendor
  support archives;
- machine-local state directories, unredacted logs, complete command history,
  Git diffs containing personal data, or screenshots that expose unrelated
  apps, notifications, accounts, or desktop content.

Replacing a secret with asterisks does not make the original secret safe if it
remains in attachment metadata, shell history, Git history, another field, or
a quoted reply. If a live credential was exposed, use the private security
route and rotate or revoke it through the issuing service.

## Safe diagnostic workflow

Start with a local preview. It writes no ZIP:

```sh
./bin/macomrade diagnostics bundle \
  --output ~/Desktop/macomrade-diagnostics.zip
```

Read the payload preview, excluded categories, redaction counters, failure
classes, predicted members, and policy flags. Redaction is defense in depth,
not proof that every future data source is safe.

Export is a second, explicitly confirmed local action:

```sh
./bin/macomrade apply diagnostic-bundle \
  --output ~/Desktop/macomrade-diagnostics.zip \
  --apply \
  --confirm "EXPORT REDACTED DIAGNOSTICS"
```

The verified manifest must retain `sharing_authorized: false` and
`publication_authorized: false`. Successful export means only that a new local
ZIP passed the bounded collector's checks. Reopen the archive, inspect all
three members, and make a separate explicit decision before manually attaching
it to a public issue or sending it privately. This repository provides no
issue-upload, email-send, or publication command.

If preview or export reports a prohibited value, unexpected file, failed
verification, or redaction uncertainty, do not share the artifact. Keep the
failure local, use the private route in `SECURITY.md`, and begin with the error
category rather than the rejected payload. See
[`redacted-diagnostic-bundle.md`](redacted-diagnostic-bundle.md) for the exact
collector and ZIP contract.

## Public mutation safety contract

Public support never weakens the local transaction contract:

```text
inspect → plan → confirm → apply → verify → record
```

- Read-only inspection and dry-run remain the defaults.
- A public issue, comment, patch, test result, or maintainer suggestion is not
  authorization to change a user's Mac or external account.
- Every mutation names its target and risk, uses the registered confirmation
  mode, and performs independent read-back. Consequential actions retain exact
  confirmation even when the surrounding documentation is localized.
- No support workflow may enter credentials, approve a security prompt,
  silently grant TCC access, disable platform security, upload an artifact, or
  broaden the requested scope.
- GitHub-hosted automation is not a substitute for live Mac acceptance and
  must not install software or mutate user state.

See [`mutation-transaction-contract.md`](mutation-transaction-contract.md) for
the implementation-level requirements.

## Maintainer response boundary

Maintainers may request a smaller fictional reproduction, a command's exit
status, a redacted error category, or the preview summary. They should not ask
for a Private directory, secret, raw authorization database, full home archive,
remote login, screen-sharing control, or an unreviewed support bundle.

Unsafe public material may be hidden, removed, or moved to the private security
process. Best-effort support does not guarantee response time, backward
compatibility, data recovery, remote remediation, or acceptance of a proposed
mutation. The reporter retains control of local execution and the separate
decision to share each artifact.
