# Browser bookmark migration

Documentation only — no script here reads or exports bookmark contents.
`scripts/chrome_profiles.py` already matches Chrome profiles to accounts by
email (see `config/chrome-profiles.json`); this fills the one gap that
leaves open: the bookmarks *inside* each matched profile.

## Where bookmarks actually live

Each Chrome profile stores its bookmarks as a JSON file at:

```text
~/Library/Application Support/Google/Chrome/<Profile Directory>/Bookmarks
```

`<Profile Directory>` (e.g. `Profile 1`, `Profile 4`) is the same
machine-local allocation detail `chrome_profiles.py` already treats as
non-identity — the profile is matched to its owning account by email from
`Local State`, not by this directory name. Confirmed present on this Mac
across all seven tracked profiles (2026-07-19).

## Why this stays manual, not scripted

This skill's existing policy (`chrome_profiles.py`, `settings/privacy.yaml`)
is explicit that cookies, passwords, session tokens, and browsing history
are never read or exported. Bookmark *titles and URLs* are not secrets in
the same sense, but:

- They can still contain sensitive URLs (internal tools, tokens embedded in
  query strings, private document links).
- Chrome already has a supported, safe migration path (its own sync
  account), making a custom script redundant risk for little benefit.

## Recommended migration path (per profile, per account)

1. **If Chrome Sync is enabled for that Google account**: bookmarks sync
   automatically once the profile is signed in and Sync is turned on
   (`chrome://settings/syncSetup`). This is the default path and needs no
   action from this skill beyond the existing account-verification
   checkpoint in `chrome_profiles.py`.
2. **If Sync is intentionally not enabled for that profile**: use Chrome's
   built-in `chrome://bookmarks` → menu → **Export bookmarks** to produce
   an HTML file, transfer it manually (AirDrop, the password manager's
   secure notes, or a private cloud folder — never committed to this
   repository), then **Import bookmarks** on the new Mac's matching
   profile.
3. Verify after migration: open `chrome://bookmarks` on the new Mac and
   spot-check folder structure and a few entries against the old Mac,
   rather than trusting the import silently.

## What this skill will and won't do

- Will: confirm via `chrome_profiles.py` that the expected profile/account
  exists before bookmark migration is attempted, so migration targets the
  right profile.
- Will not: read, export, count, or diff actual bookmark titles/URLs. That
  remains entirely a manual, Chrome-native operation.
