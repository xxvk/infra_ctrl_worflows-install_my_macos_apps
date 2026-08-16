# Browser URL normalization and duplicate review

## Scope

BR-04 is a private, read-only review layer. It proposes canonical URLs and
duplicate groups for already parsed browser items. It does not fetch a URL,
write browser data, confirm a canonical value, merge items, move folders, or
delete anything.

The public policy is
[`settings/browser-url-normalization.json`](../settings/browser-url-normalization.json).
Its Schema is
[`browser-url-policy-v1.schema.json`](../schemas/browser-url-policy-v1.schema.json).
Validate it with:

```sh
python3 scripts/browser_review.py validate-policy
```

Review one explicitly supplied Safari Bookmarks-and-Reading-List-only export with:

```sh
python3 scripts/browser_review.py inspect-safari-export \
  /private/path/to/Safari\ Export.zip
```

The command prints counts and booleans only. URLs, titles, paths, fingerprints,
item IDs, group IDs, and parameter values remain private in memory and are not
logged.

## Normalization policy

Only `http` and `https` URLs are eligible. Scheme and host are lowercased and a
default `:80` or `:443` port may be removed. The path bytes, fragment, retained
query segments and order, repeated parameters, unknown parameters, empty
query/fragment delimiter, and non-default port are preserved.

The removable allowlist contains only parameters whose attribution purpose is
documented by their owner:

- Google Analytics campaign parameters: `utm_id`, `utm_source`, `utm_medium`,
  `utm_campaign`, `utm_source_platform`, `utm_term`, `utm_content`,
  `utm_creative_format`, and `utm_marketing_tactic`;
- Google advertising click identifiers: `gclid`, `dclid`, `gbraid`, and
  `wbraid`;
- Microsoft Advertising click identifier: `msclkid`.

Names such as `id`, `ref`, `source`, `page`, `q`, `query`, `lang`, and `locale`
are explicitly retained. Any unknown key is retained. A new removable key must
have primary-source evidence, a policy/schema update, negative tests, and
review; a CLI run never edits the tracked policy.

## Fail-closed boundaries

The whole normalization proposal is blocked when the URL has:

- credentials/userinfo, an unsupported scheme, missing/invalid authority or
  port, control characters, or a backslash;
- a semicolon query separator whose legacy interpretation is ambiguous;
- a token, OAuth, authorization, password, signature, expiry, or other
  protected key;
- an `x-amz-` or `x-goog-` signed-URL key prefix.

A blocked result does not echo the URL or parameter values. This intentionally
prefers a missed duplicate over changing a signed, identity-sensitive, or
ambiguous URL.

## Duplicate evidence and identity

Review groups are formed only when normalized comparison URLs match inside the
same browser, profile scope/reference, and account reference. A matching URL in
another identity boundary is counted as a suppressed collision and never
enters the group.

Each group records whether evidence is an exact URL match or a proposed
canonical URL match. Title and collection differences are explicit mismatch
evidence. Every proposed action is `review_only`, and both policy and result
keep `execution_authorized: false`.

BR-06 must separately provide a restorable export, frozen plan, exact
confirmation, transaction-safe write, and browser-visible read-back before any
merge, move, archive, or delete can exist.

## Primary evidence

- [Google Analytics URL builder and UTM parameters](https://support.google.com/analytics/answer/10917952)
- [Google Ads click identifier (`gclid`)](https://support.google.com/google-ads/answer/9744275)
- [Google Analytics `dclid` and UTM collection](https://support.google.com/analytics/answer/11242870)
- [Google `gbraid` and `wbraid`](https://support.google.com/analytics/answer/11367152)
- [Microsoft Advertising auto-tagging (`msclkid`)](https://help.ads.microsoft.com/apex/index/3/en/60000)
