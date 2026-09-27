# fixed4 leaf verification asset

Claim stage: `FUNCTIONAL_SIM` when the runner and both negative canaries complete and a separate reviewer accepts the evidence. Until then: `NOT RUN` or `INCONCLUSIVE`. DUT identity is SHA256 `1F2A47956B34872F2625FCB262166EEE73D88044C84415C8DEDB0E3258254EFA`. Requirements come from the immutable `cb9118582f3ea09c47cb53e9141f395cbb3ee832` version of `A-FIXED4-INTERFACE-20260925.md`, sections 3–5.

## Requirement → test → checker

| Requirement | Stimulus | Checker |
| --- | --- | --- |
| S29 to S25/F23 integer RNE; tie and overflow | bins 0–4, all 145 prepared `input_s29` values in bins 5–149, and deterministic varied values in the remaining 513-beat run | `rne16` uses integer quotient/remainder of the input magnitude; compares both data fields, per-component overflow, numeric-valid, zero placeholder and sticky overflow |
| One registered beat, II=1, no loss/duplication | 513 sequential tags with sustained and seeded random backpressure | cycle-indexed accepted beat and earliest transfer edge; one-entry expected queue, ctx/bin/data/sideband check; `seen[0:512]` and exact 513 counts |
| Cancel withdraws stalled beat | permanent `m_ready=0`, repeated cancel | N/P/T/untransferred snapshot; empty queue, quiescence, OR of late causes |
| Same-edge cancel with physical old output/new input | `m_ready=1`, valid new beat, cancel together | T and S-transfer flags, T bin and unchanged semantic N/P |
| Local ctx/bin error and external cause union | illegal bin; ctx+bin error with external cancel | combinational fault bits before edge, terminal 35-bit cause, discarded input |
| Last output and cancel priority | 513th output pending, cancel on transfer edge | N=513/P=512/T=1, `data_done=0`, terminal snapshot |
| Ack and retirement use pre-edge predicates | first kill with ack; duplicate ack; valid ack concurrent with retire; retire concurrent with kill when all other retire conditions hold; unsafe normal retire | retained context and first terminal snapshot, exact increments of manager reject-audit counters, following-edge retire, directed cover counters |
| One reserved cancel slot rejects a new context | new nonzero begin while cancelled context remains active | `begin_ready=0`, old active ctx and terminal remain unchanged |
| Same-edge protocol fault blocks manager success commit | old output transfers while next input has the wrong bin | public `protocol_fault_now` checked against independent fault calculation before E; logical manager gate `m_valid && m_ready && !cancel && !protocol_fault_now` remains low and success count unchanged |
| Cold reset only in safe state, suppresses requests | initial and retired-state reset; active input/reset negative canary | synchronous reset values and explicit environment assertion |
| Critical checkers really reject defects | isolated `+CANARY` and `+ILLEGAL_RESET` jobs | deliberate expected-data corruption; active-reset assertion; runner requires each failure marker and rejects a false PASS |

## Model card

The reference model is one active context and one expected output beat. It is derived from the cited cycle contract. It records accepted input edge, tag, data, numeric status and earliest output transfer edge. It advances on each `clk` edge using pre-edge handshakes, then compares DUT outputs after the nonblocking assignment region (`#1`). Signed RNE uses mathematical quotient and remainder of the nonnegative magnitude, independently of the DUT's shift/floor implementation. It does not read private DUT signals or learn expected latency from observed output. The deterministic PRNG starts at `5a17c0de`; the first failure prints cycle, current seed, context and counters. The runner preserves separate compile/elaboration/simulation logs and hashes per job.

The 145 input values were mechanically extracted in array order from the immutable Git blob `41c6e4ccbde45310a79dac844fb6312a5694e9fe` at commit `cb9118582f3ea09c47cb53e9141f395cbb3ee832`. Each generated 29-bit hex row was decoded and compared back to that object's signed `input_s29`; the fixture SHA256 is `B33788B9D4A42DAA9925DD637340275B918CFF3EE1F3C41C615AE0A2B4FB6598`. The runner rejects any fixture hash change. No `expected_integer`, `output_s25`, or `overflow` field from that JSON is used by the expected-value model.

This model covers only the leaf's single clock. The commit gate is a logical manager model; it does not verify a physical downstream consumer. `retire_safe` is a test-manager assumption, not proof of physical reader/DMA drain. External FFT status has no leaf port; the last-beat test checks only the leaf-side cancel decision. Real watchdog threshold, DMA ownership, identity allocation, CDC/RDC, STA, board timing and full frame abort storage remain outside this claim.

Run from any directory with a fresh path under repository `codex_out`, for example:

```powershell
pwsh -File simulation/tb/algorithm/fixed4/run_fixed4.ps1 -OutputDirectory codex_out/fixed4-unique-run
```

The output path must resolve under `codex_out`; use an absolute path if invoking outside the repository. `run-manifest.json` records each stage, log, actual simulator version banner, and the positive job's native WDB path, size and SHA256. The positive job compiles with `xelab --debug typical` and uses a Tcl batch containing `log_wave -r /tb_fixed4/*` before `run -all`; negative jobs retain native logs. The positive job must print `FIXED4_PASS` and produce a nonempty WDB; both isolated canaries must fail with their designated markers. A test-asset author cannot independently sign functional acceptance.
