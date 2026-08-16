# Mutation transaction contract

Every supported mutation is registered in
[`mutation-contracts.json`](mutation-contracts.json) with a stable action ID,
exact target class, risk, confirmation mode, apply behavior, verification,
record, rollback, interruption recovery, and idempotency rule.

The mandatory phase order is:

```text
inspect → plan → confirm → apply → verify → record
```

High-risk and destructive actions require an exact typed token. Medium and low
risk actions may use an explicit command/flag only when the registry documents
why that boundary is sufficient. A dry run, empty target set, unavailable
interface, interrupted apply, or package-manager receipt is never a successful
verification.

Run:

```sh
python3 scripts/validate_mutation_contracts.py
```

The validator requires all 34 supported mutation entry points, all contract
fields, unique IDs, implementation declarations, runtime-emitted action IDs,
and source-visible exact tokens for high-risk actions. Add a registry entry
and tests before adding a new mutation.

Use `scripts/transaction_contract.py` to resolve an action contract, enforce an
exact confirmation, or stamp a machine-local record with its action ID,
contract hash, phase, status, and exact runtime targets.
