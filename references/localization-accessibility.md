# Localization and accessibility contract

## Contents

- [Scope](#scope)
- [Locale policy](#locale-policy)
- [Message contract](#message-contract)
- [Accessibility requirements](#accessibility-requirements)
- [Validation](#validation)

## Scope

Machine-readable fields, action IDs, schema kinds, file paths, and CLI route
names remain stable English identifiers. Human-facing text added after this
contract must use declared message IDs from the locale catalogs. The initial
supported locales are Simplified Chinese (zh-Hans), Japanese (ja), and English
(en).

This contract does not falsely claim that every historical script line is
already translated. New role and adapter flows are the first migrated surface;
existing output is migrated when its workflow changes materially.

## Locale policy

Default output follows LC_ALL, LC_MESSAGES, or LANG; unknown system locales fall
back to English. Commands that expose a human message accept zh-Hans, ja, en,
or system. JSON identifiers remain language-neutral, so automation never parses
translated prose.

Every locale catalog must have exactly the same message IDs and placeholder
names. Do not concatenate translated fragments in code. Use named placeholders
and retain them across all languages.

## Message contract

[localization.json](../settings/localization.json) is the tracked policy. The
message catalogs are public portable policy, never a place for account
identifiers, paths, session data, or observed machine state.

    python3 scripts/localization.py validate
    python3 scripts/localization.py message role.selected --lang ja --roles developer,robotics

## Accessibility requirements

- Meet WCAG AA contrast for future HTML/native visual status indicators.
- Never communicate status only by color, icon, emoji, or sound.
- Every future TUI action must have keyboard-complete operation and readable
  plain-text fallback.
- Future HTML reports use semantic headings, table headers, labels, and
  text-equivalent status; VoiceOver must not depend on layout order.
- CLI error/action IDs stay stable across languages and destructive operations
  retain their exact confirmation tokens without translation.

## Validation

The locale validator rejects missing locale files, divergent message IDs,
placeholder drift, unsupported locale names, and malformed schema documents.
The hermetic test suite covers those negative cases.
