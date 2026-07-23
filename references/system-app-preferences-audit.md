# System App Preference Audit

This is the portable-policy boundary for built-in macOS applications. The
machine's current values are written to machine-local `preferences-*.json` by
`scripts/macos_preferences.py`; only confirmed values belong in tracked
`settings/system-preferences-values.json`.

## Completed read-only coverage

| App/domain | Safe coverage | Cross-device status |
| --- | --- | --- |
| Contacts | Person-name presentation defaults | Tracked allowlist |
| Calendar | View, sidebar, time range, timezone, travel-advisory policy | Observed partial; account selection manual |
| Reminders | Preference-domain presence; no safe scalar policy found | Manual/account setup |
| Mail | Thread, sort, filter, favorites, viewer policy | Observed partial; accounts manual |
| Safari | Homepage type, search, Reader, sidebar, developer, extension policy | Observed partial |
| Finder | Sidebar, desktop icons, iCloud folders, extensions, Trash, view policy | Observed partial |
| Notes | Checklist auto-sort | Observed partial; account/folder setup manual |
| Messages | Filtering, retention, attachment retention, Focus-list policy | Observed partial; account setup manual |
| Photos | Grid, zoom, launch chooser, shared-library presence | Observed partial; iCloud/library setup manual |
| Music / TV / Podcasts | Limited playback/download fields | Observed partial; account/library setup manual |
| Preview / TextEdit / Quick Look | Preview display fields; no safe TextEdit/Quick Look scalar found | Observed partial |
| Shortcuts / Automator | Shortcuts layout; no safe Automator scalar found | Manual automation setup |
| App Store / Software Update | Limited App Store UI field; no portable update policy found | Manual system setup |

## Exclusion boundary

Never export or track passwords, tokens, Apple IDs, account identifiers,
message/note/event/photo contents, attachments, browsing data, purchase
history, private paths, recent-item lists, window coordinates, databases, or
automation actions that may contain secrets.

## Recovery rule

On a new Mac, restore only values explicitly promoted into the tracked
allowlist. Re-authenticate accounts and manually configure account-backed
libraries, calendars, mail, messages, notes, photos, and media services.
