# Workflow artifacts

These artifacts bind acceptance claims to one project snapshot. Store the applicable subset under `codex_out/<run-id>/` and validate structured records against the JSON Schemas in `references/schemas/`. Omitted facts are `UNKNOWN`; an empty field does not silently become an assumption. A diagnostic smoke job normally needs only a concise command/result record; it does not need the complete artifact set unless its result is promoted into an acceptance claim.

## Artifact set

| File | Owner | Minimum purpose |
|---|---|---|
| `task-contract.json` | Coordinator + architect | Stable project identity, live task delta, authorization, claim stage, protected work, scope, immutable behavior, and acceptance evidence |
| `snapshot-manifest.json` | Coordinator | Git/diff/source identity, target, defines, parameters, and constraints |
| `impact-manifest.json` | Architect | Bounded affected cone, domains, shared state, reverse backpressure, and tests |
| `cycle-contract.json` | Architect | Accepted/completed edges, latency, throughput, alignment, and recovery |
| `verification-plan.json` | Verification engineer | Requirement -> Test -> Checker -> Cover and model independence |
| `run-manifest.json` | Runner | Command, cwd, tool/version, exits, seed, libraries, and evidence paths |
| `simulation-evidence.json` | Runner + independent evidence reviewer | Functional-acceptance profile, cycle comparisons, checker drain, negative canaries, first failure, proof packet |
| `findings-ledger.json` | Coordinator | Stable finding lifecycle across snapshots and repair rounds |
| `ip-proof-packet.json` | FPGA engineer + vendor reviewer | Official IP identity, generation method, source-view ownership, contracts, products, OOC/constraints/simulation/reopen evidence |

## Common identity

Every artifact contains `schema_version`, `run_id`, and `snapshot_id`. A report or waveform whose snapshot does not match the reviewed RTL is stale and cannot support a verdict. Paths are project-relative wherever practical; private absolute paths stay in ignored local configuration.

## Templates

Use the schema examples as the starting template:

```json
{
  "schema_version": "1.0.0",
  "run_id": "2026-01-01T000000Z-example",
  "snapshot_id": "sha256:replace-with-real-snapshot-hash",
  "status": "UNVERIFIED"
}
```

Do not create artifacts merely to make a checklist green. Populate them from inspected files, actual commands, and actual reports. Artifact validation proves shape only, not engineering correctness.
