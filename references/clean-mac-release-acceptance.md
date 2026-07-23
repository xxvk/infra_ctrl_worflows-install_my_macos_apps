# Clean-Mac 0.1.0 release acceptance

This is the deterministic hardware gate for changing 0.1.0 from
`release_candidate` to `shipped`. The tooling is ready; the hardware run is
`blocked_external` until an unused or newly purchased Mac is available.
Previously configured Macs may test the harness but cannot satisfy CM-01.

## Preconditions

- Use an unused/new Mac and explicitly attest that disposition.
- Use one clean Git worktree at a full commit. Do not run acceptance from
  uncommitted source.
- Run the iCloud Git guard before Git-dependent commands.
- Keep the session under machine-local state. Never add its evidence directory
  to Git.
- Do not record passwords, tokens, cookies, private keys, recovery codes,
  session material, or private payload content.

## Workflow

Validate the tracked contract on any Mac:

```sh
python3 scripts/clean_mac_acceptance.py validate
python3 scripts/clean_mac_acceptance.py status
```

On eligible hardware only, initialize a session:

```sh
python3 scripts/clean_mac_acceptance.py init \
  --attest "CLEAN MACHINE: UNUSED OR NEW MAC" \
  --apply \
  --confirm "UPDATE CLEAN MAC ACCEPTANCE"
```

The command itself runs the iCloud Git guard and refuses anything except
`ready`, then refuses a dirty worktree. It records the full source commit,
macOS version, architecture, contract hash, and CM-01/CM-02 results in a new
machine-local bundle. The unused/new disposition is an explicit operator
attestation; macOS exposes no reliable automatic proof of prior human use.

Complete gates CM-03 through CM-13 in order. Record each bounded JSON evidence
artifact after reviewing it:

```sh
python3 scripts/clean_mac_acceptance.py evidence-template --gate CM-05

python3 scripts/clean_mac_acceptance.py record SESSION_DIR \
  --gate CM-03 \
  --outcome passed \
  --evidence /path/to/result.json \
  --note "Hermetic release check passed." \
  --apply \
  --confirm "UPDATE CLEAN MAC ACCEPTANCE"
```

`record` accepts JSON only, rejects secret-bearing keys, redacts email and home
paths, and stores a sanitized copy plus source/bundle hashes. It validates
automated results against the gate's expected output structure. Interactive
gates require the standard `clean_mac_gate_evidence` envelope printed by
`evidence-template`; generic `{"status":"passed"}` JSON is rejected. A passed
gate must meet its required evidence count.

CM-12 must be an actual reversible drill on the clean Mac:

1. Inspect the drift-monitor LaunchAgent.
2. Run its install dry-run and review the target.
3. Install it with explicit apply, verify `launchctl`.
4. Uninstall it with explicit apply, verify the registration is absent and the
   timestamped backup exists.
5. Record separate install/read-back and uninstall/read-back JSON evidence.

After every gate is passed:

```sh
python3 scripts/clean_mac_acceptance.py finalize SESSION_DIR \
  --apply \
  --confirm "FINALIZE CLEAN MAC ACCEPTANCE"
```

Finalize reruns the iCloud Git guard, rechecks the clean worktree and exact
source commit, requires exactly CM-01 through CM-13 in contract order, and
re-reads every sanitized evidence file to verify its path, size, and SHA-256.
It refuses pending, blocked, failed, under-evidenced, missing, or tampered
evidence. Acceptance applies only to that machine session and does not
authorize Git publication or change tracked release status automatically.

After independent review, a later tracked status change may set
`hardware_run_status` to `passed` only with the finalized session manifest's
SHA-256 and review timestamp. That status change is separate from finalization
and still does not authorize publication.

## Failure and interruption

- Record `blocked` for an external prerequisite and `failed` for a real
  acceptance failure; do not convert either to passed without new evidence.
- Resume the same session after interruption. Updates are atomic and retain
  gate history.
- If source commit or contract changes, abandon the session and start a new
  one; never mix evidence from different release candidates.
- Preserve the machine-local bundle until release review is complete. Promote
  only reusable fixes or rules into Git, never machine observations.
