# X CLI operations

Use this reference for X profile discovery, recent-post reads, and explicitly
confirmed account mutations. It complements the component guides for
[`tamnd/x-cli`](../components/tamnd-x-cli.md) and
[`xurl`](../components/xurl.md); it does not store account IDs, targets,
credentials, cookies, or API prices.

## Tool boundary

| Need | Default |
| --- | --- |
| Public profile or recent posts | `x` from `tamnd/x-cli` |
| Official user lookup/search or an API-specific response | official `xurl` |
| Follow, unfollow, post, like, delete, or another account write | official `xurl`, only after explicit confirmation |

`x` is the free, read-only default, but it uses public or browser-facing X
surfaces and can break when X changes them. Do not bypass rate limits, scrape
private data, or import browser cookies unless a named session-only read has
been separately approved.

`xurl` calls the official X API and may consume paid API credits. Check current
endpoint availability and pricing immediately before paid automation; never
copy a historical price into policy as if it were current.

## Safe preflight

```sh
command -v x
x version
command -v xurl
xurl --version
xurl auth status
xurl whoami
```

The last two checks identify the active API account before a billable call or
write. Never run `xurl token` in an agent workflow: it prints a bearer token to
standard output. Avoid verbose or trace output in captured logs unless token
and authorization-header redaction has been verified.

## Find a person and read recent posts

When a handle is known, use the free read-only client first:

```sh
x user <handle> -o json
x timeline <handle> -n 10 -o json
```

Do not treat display-name matches as identity proof. Confirm the handle,
display name, biography, verification state where available, and other public
context before selecting a person.

For an official lookup or fuzzy person search, use bounded `xurl` requests:

```sh
xurl user <handle>
xurl posts <handle> -n 10
xurl '/2/users/search?query=Trevor%20Noah&max_results=10&user.fields=description,verified,public_metrics'
```

URL-encode user-supplied search text. `xurl search <query>` searches recent
posts, not people; do not use it as a user-directory lookup.

## Follow and unfollow transaction

Following and unfollowing change the user's account and may be billable. Apply
the repository mutation sequence: check, dry-run, explicit confirmation,
single apply, and read-back.

1. Run `xurl whoami` and show the active account.
2. Resolve the target with `xurl user <handle>` and show the canonical handle
   and public identity evidence.
3. Present the planned command without running it:

   ```sh
   xurl follow <handle>
   ```

   or:

   ```sh
   xurl unfollow <handle>
   ```

4. Obtain explicit confirmation immediately before the write.
5. Execute exactly once.
6. Read back the targeted relationship through the official API:

   ```sh
   xurl '/2/users/by/username/<handle>?user.fields=connection_status'
   ```

If the response does not expose `connection_status` for the current account or
product tier, stop and report that the write result cannot yet be independently
verified. Do not repeat the mutation as a verification strategy.

## Failure handling

- `client forbidden`, enrollment, product-access, or billing errors: inspect
  the X Developer Console; do not reauthenticate or retry in a loop.
- OAuth scope failure: request only the minimum scope required for the named
  operation. Installation or login does not authorize account writes.
- Rate limit or credit exhaustion: stop and report the bounded request that was
  attempted; do not switch to scraping or cookie extraction automatically.
- Ambiguous identity: return candidates and require target selection before a
  write.

## Authoritative references

- X Developer Platform xurl documentation: <https://docs.x.com/tools/xurl>
- Official xurl repository: <https://github.com/xdevplatform/xurl>
- X API user lookup: <https://docs.x.com/x-api/users/lookup/introduction>
- X API user search: <https://docs.x.com/x-api/users/search/introduction>
- X API follows: <https://docs.x.com/x-api/users/follows/introduction>
