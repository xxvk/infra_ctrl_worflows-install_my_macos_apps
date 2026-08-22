# Runtime state compatibility locator

Runtime observations no longer live in this repository. Resolve the current
machine's directory with:

```sh
python3 scripts/state_paths.py path
```

The default is:

```text
~/Library/Application Support/macomrade/state/<hashed-machine-id>/
```

`--state-dir PATH` overrides the default for one command.
`MACOMRADE_STATE_DIR` overrides it for a process tree, including
bootstrap child commands. The CLI option has higher precedence.

Only this README and `locator.json` belong in the tracked compatibility
directory. Never restore runtime JSON, logs, permission observations, detected
versions, machine paths, cleanup measurements, credentials, tokens, private
keys, raw TCC databases, or session material here.
