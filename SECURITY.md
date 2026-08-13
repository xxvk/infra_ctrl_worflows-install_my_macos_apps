# Security policy

## Supported versions

This project has not published a stable release. Security fixes target the
current `main` branch and active 0.1.x release-candidate line. Rewritten,
superseded, or archived commits are not supported.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability, exposed credential,
private account identifier, unredacted diagnostic bundle, or unsafe mutation.
Use GitHub's private vulnerability-reporting interface when it is available.
If it is unavailable, email `xxvk@outlook.com` with the subject
`[macomrade security]`.

Include the smallest safe reproduction, affected commit or version, expected
impact, and whether the report contains sensitive data. Do not attach tokens,
passwords, cookies, private keys, raw TCC databases, private documents, or a
complete home-directory archive. Use the repository's redacted diagnostic
preview workflow when diagnostic evidence is necessary.

Reports are handled on a best-effort basis. Receipt, severity, remediation,
embargo, and disclosure timing will be coordinated privately; this policy does
not promise a fixed response or release deadline.

## Security boundary

macomrade plans and executes local macOS changes. A successful test does not
authorize an install, permission grant, account login, destructive cleanup,
history rewrite, or external publication. Mutations retain their documented
inspection, confirmation, verification, and rollback requirements.
