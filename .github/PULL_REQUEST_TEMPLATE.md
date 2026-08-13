## Purpose

Describe the user need and the bounded change.

## Safety and privacy checklist

- [ ] No secrets, Private files, or machine-local state are included.
- [ ] Public fixtures are fictional and contain no personal identifiers.
- [ ] Read-only and dry-run defaults remain intact.
- [ ] Every mutation has exact scope, confirmation, verification, and rollback documentation.
- [ ] Persistent format changes include schema and migration coverage.
- [ ] User-facing localized messages remain consistent where applicable.

## Validation

```sh
python3 scripts/icloud_git_guard.py inspect --repo .
python3 scripts/release_check.py
git diff --check
```

List any additional targeted tests and any live checks separately. A live check
must not grant permissions, install software, change accounts, or clean data
merely because this pull request exists.
