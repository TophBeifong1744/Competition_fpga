# fixed4 leaf verification asset

Claim stage: `FUNCTIONAL_SIM`; author result remains `INCONCLUSIVE` pending independent read-only review. DUT SHA-256: `1f2a47956b34872f2625fcb262166eee73d88044c84415c8dedb0e3258254efa`. Fixture SHA-256: `b33788b9d4a42daa9925dd637340275b918cff3ee1f3c41c615ae0a2b4fb6598`. Requirements come from parent commit `cb9118582f3ea09c47cb53e9141f395cbb3ee832`, `A-FIXED4-INTERFACE-20260925.md` sections 3–5 and B r2 integer-domain source.

## Requirement → stimulus → checker → isolated negative case

| Requirement | Positive stimulus and checker | Negative case / designated first checker |
| --- | --- | --- |
| S29 to S25/F23 RNE, tie, overflow | hand-derived bins 0–4; 145 input rows; 513 tags; magnitude quotient/remainder `rne16`; data and sidebands | `numeric` / `m_re`; `sideband` / `m_numeric_valid` |
| Registered beat, II=1, identity, backpressure | per-edge q model; sustained and seeded random stalls; 513 seen bins and exact drain | `timing` / `m_valid`; `tag` / `m_bin` |
| Local ctx/bin fault | accepted wrong bin/ctx; pre-edge public fault bits | `fault` / `fault_bin` |
| Cancel cause and E snapshot | physical old T/new S, first and later 35-bit OR causes, retained N/P/T | `snapshot` / `terminal_causes` |
| Ack/retire pre-state and kill priority | first kill+ack, first ack+retire, duplicate ack, kill+retire and audits | `ack_retire` / `terminal_saved` |
| Same-edge fault suppresses success commit | old T plus wrong-bin S, public logical manager gate | `commit` / `manager_commit_gate` |
| Synchronous reset and active-input guard | startup and retired-state reset; active request negative | `reset` / native `ILLEGAL_RESET_ASSERT` |

Other positive checks cover cancelling a stalled output, last-beat cancel, and occupied terminal slot blocking begin. Each negative changes one model expectation or observation input at the chosen setup. It prints `CANARY_INJECT case=... checker=...`; the first failure must match that case/checker, followed by native XSim `Fatal`, without `FIXED4_PASS`. These faults are test-asset canaries, not DUT failures. The runner's three synthetic verdict probes test its judgment function with marker-only normal exit, wrong first checker, and failed tool stage; they are not simulations.

## Cycle model and proof packet

The reference model is one active context and one expected q beat. It derives accepted input, tag, rounded data, sidebands and fault from public inputs and the approved cycle contract, without reading private DUT state or observed numeric values. Each tick checks settled pre-edge handshakes and post-NBA outputs after `#1`. The old `cycle+1<accepted_at+1` assertion was deleted: it reduced to `cycle<accepted_at` and could not catch a one-cycle-early output. Per-tick `m_valid` versus independent q state is the timing rule; isolated `timing` alters q after the first accepted edge and must fail at `m_valid`. The separate `tag` negative verifies identity.

The positive job writes `accepted-ledger.csv` for **every** accepted input: accepted edge, earliest due edge (`accepted+1`), observed output or cancellation edge, tag, expected data/sidebands and outcome. It must contain no pending token at PASS. `transaction-ledger.csv` records each physical output transfer with expected and actual values plus dynamic PRNG state. `cycle-proof.csv` records finite pre/post edge rows for first beat, stall/resume, E old T/new S and cause, same-E fault/commit, first kill+ack, first ack+retire, kill+retire, and last-beat cancel. It contains actual and independently expected public signals, including `ctx_active`, `active_ctx`, `terminal_saved`, `terminal_cancelled`, terminal context/N/P/untransferred/T-bin, `data_done`, input controls, edge index, simulator time in ps, `seed_init=5a17c0de`, and dynamic PRNG state. The runner compares these state/snapshot columns on every selected pre/post row. In post rows, `s_accepted` and `m_transferred` refer to the just-completed edge; public wires and expected model signals are current post-NBA values. Native `fixed4.wdb` is retained. The CSV is a reproducible selected-window packet, not a replacement for WDB.

The 145 fixture values are signed `input_s29` from immutable parent blob `41c6e4ccbde45310a79dac844fb6312a5694e9fe`; prepared outputs/golden are not used in the expected-value model. RNE uses magnitude division/remainder, independent of the DUT shift/floor implementation. The runner freezes RTL/fixture hashes, records source/tool identities and three-stage exits per case, and emits `run-manifest.json` and schema-shaped `simulation-evidence.json`. Both records identify the actual run source set as `source-set-sha256:<digest>`. To calculate it, take SHA-256 of the exact RTL, TB, fixture, then runner bytes; lowercase each 64-digit hex hash; join the four hashes with ASCII `:` and no newline; SHA-256 the resulting ASCII bytes; lowercase the final hex digest. `parent_candidate=e3483410077fbfbf87cac62fccec916144b84286` is only the frozen product baseline, not the run snapshot or a claim that the shared `HEAD` has that value. The evidence record remains `INCONCLUSIVE` pending independent review even when the author run is self-checked.

Run from repository root after freezing this asset batch, using a new directory:

```powershell
pwsh -NoProfile -File ./simulation/tb/algorithm/fixed4/run_fixed4.ps1 -OutputDirectory ./codex_out/i14-fixed4-evidence-repair-<run-id> -VivadoBin F:/AMD/2025.2/Vivado/bin
```

The path must be a new child of `codex_out` with that prefix. Jobs are isolated by case, each with its own compile, elaboration and simulator workspace/logs. Each job passes one no-equals marker such as `CASE_FUNCTIONAL` through XSim `-testplusarg`; the TB requires exactly one recognized marker and preserves lowercase case names in failure logs. The runner expects 10 cases: functional plus nine negatives. It rejects nonzero tool-stage exits, missing or misplaced injection/failure/Fatal markers, a negative PASS, missing WDB/CSV, incomplete selected windows and ledger mismatches. A separate read-only reviewer must compare machine records with native logs and CSV/WDB before a functional claim.

Scope is one synchronous leaf and logical manager gate. Physical consumer wiring, DMA ownership/drain, external FFT status, real watchdog timeout, identity allocator, CDC/RDC, STA, synthesis, `one`/Vitis and board behavior are outside this test.
