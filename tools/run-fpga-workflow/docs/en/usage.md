# Usage

[README](../../README.md) · [Simplified Chinese](../zh-CN/usage.md) · [Architecture](architecture.md) · [Roles](roles.md) · [Installation](installation.md) · [Safety and evidence](safety-and-evidence.md)

Invoke the workflow by naming `$run-fpga-workflow` and stating the desired outcome, write authorization, immutable boundaries, available evidence, and any checks that must or must not run. The workflow will select only the roles relevant to the task.

## Optional project identity card

Use a short identity card to avoid repeated machine-wide discovery:

```text
Project root:
Canonical .xpr/.pds/.al:
Vendor and tool version:
Full part:
Product top / simulation top:
Formal build / simulation / lint entry points:
Long-term protected boundaries:
```

This is stable location and target context, not persistent write authority.
Later prompts create a live task delta and may supplement, supersede, expand,
or narrow the current task. Clean/overwrite, IP regeneration, implementation,
release, publishing, and physical actions still require explicit current
authorization.

## Mode decision table

| Situation | Mode | Why |
|---|---|---|
| Explain RTL behavior, inspect a report, diagnose an error, propose architecture, or perform code/release review without edits | `ANALYZE` | No write authorization is needed or implied |
| Small bug, one clock domain, no interface/latency/constraint/vendor-IP change, low risk, explicit permission to edit | `QUICK` | A minimal product batch and focused review are sufficient |
| New module or significant datapath/FSM change | `FULL` | Architecture, verification, and integration risks need a complete contract |
| Any CDC/RDC, reset-domain, generated-clock, clock muxing, or async FIFO work | `FULL` | Clock relationships and structural evidence are high-risk |
| Register map, IRQ, DMA, external protocol, or published interface changes | `FULL` | Firmware compatibility, atomicity, and sequencing must be frozen |
| Vendor IP, primitives, pins, I/O timing, target wrapper, or constraint changes | `FULL` | Per-target semantics and implementation evidence are required |
| Possible data loss, unsafe output, high-energy control, or board bring-up | `FULL` | Failure behavior and human safety gates must be explicit |
| Uncertain whether a change affects the interface or timing | Start with `ANALYZE` | Resolve uncertainty before authorizing a write |

Risk never grants permission to edit. Conversely, an explicit request to fix a high-risk item does not make it a `QUICK` task.

## Choose the evidence profile

| Needed result | Profile | Minimum honest outcome |
|---|---|---|
| Find path/tool/source problems; compile; elaborate; start and finish a bounded smoke run | `DIAGNOSTIC_SMOKE` | Exact command, tool/version when available, exit state, important warnings, and output paths; `DIAGNOSTIC_ONLY` or `INCONCLUSIVE` |
| Accept DUT behavior from simulation | `FUNCTIONAL_ACCEPTANCE` | Snapshot-bound independent checker/model evidence, cycle alignment, drained scoreboard, relevant negative canary, and independent review |
| Accept a formal, CDC/RDC, implementation/STA, electrical, or release claim | `SPECIALIST_ACCEPTANCE` | Only the evidence family needed by that claim, plus its independent owner/reviewer |

Do not request a full acceptance packet for a simple diagnostic. Do not promote a diagnostic run into `SIMULATION_PASS`.

Qualify the profile with one claim stage:

| Claim stage | Typical meaning |
|---|---|
| `PREFLIGHT` | Locate source, tool, target, case, and library facts |
| `COMPILE` / `SYNTHESIS` | Prove only the corresponding build stage |
| `SIM_SMOKE` | Real compile/load/bounded run, no functional acceptance |
| `FUNCTIONAL_SIM` | Requirement-linked simulation acceptance |
| `IMPLEMENTATION_QOR` | Placed/routed path, congestion, fanout, and QoR work |
| `TIMING_CLOSURE` | Complete timing-coverage and closure claim |
| `FORMAL` | Formal property/harness acceptance |
| `RELEASE` / `BOARD_PREP` | Release artifact or human-controlled board preparation |

Power is NOT APPLICABLE unless explicitly requested or required by a real
budget.

## Copyable prompts

### ANALYZE: CDC failure

```text
Use $run-fpga-workflow in ANALYZE mode. Inspect this CDC failure read-only.
Inventory every relevant source and destination clock, reset domain, crossing
structure, constraint, waiver, and current report. Separate CONFIRMED, INFERRED,
and UNKNOWN facts. Give severity-ordered findings with file/line, trigger, impact,
evidence, and required repair. Do not modify files or claim PASS without current
CDC/RDC and timing evidence.
```

### ANALYZE: code review

```text
Use $run-fpga-workflow to review the current FPGA diff without changing files.
Check requirements, interface and latency behavior, reset, CDC/RDC, combinational
depth, constraints, register semantics, verification coverage, and vendor impact.
Lead with severity-ordered findings. State exactly which reports were read and
which checks remain NOT RUN or UNVERIFIED.
```

### QUICK: interface-preserving RTL fix

```text
Use $run-fpga-workflow in QUICK mode for this explicitly authorized, single-clock,
interface-preserving RTL bug fix. Protect the existing diff, make the smallest
product-source change, preserve latency and protocol behavior, run only confirmed
project tests, obtain verification review, and use an independent final reviewer.
Do not refactor unrelated code.
```

### Diagnostic simulation smoke run

```text
Use $run-fpga-workflow to run the confirmed compile, elaboration, and bounded
simulation smoke path. Record the exact tool, command, exit status, warnings,
and output directory. Keep this DIAGNOSTIC_ONLY: do not require an independent
reference model or negative canary, and do not call it SIMULATION_PASS.
```

### FULL: asynchronous streaming block

```text
Use $run-fpga-workflow in FULL mode to implement this asynchronous streaming block.
First freeze interface, data format, throughput, latency, backpressure, clock/reset
relationships, FIFO behavior, error recovery, target constraints, and acceptance
evidence. Run relevant read-only CDC, timing, interface, vendor, and verification
pre-reviews. Use one product-source writer, stable diff/hash checkpoints, isolated
validation, specialist re-review, and independent final sign-off. Do not guess
missing clock relationships or claim timing closure without implementation STA.
```

### FULL: CSR, IRQ, and DMA change

```text
Use $run-fpga-workflow in FULL mode for this authorized CSR/IRQ/DMA feature.
Identify the register source of truth; freeze address units, alignment, endianness,
byte enables, reset values, access types, side effects, reserved bits, atomicity,
IRQ status/mask/ack/clear concurrency, and DMA ownership/abort/recovery. Pre-review
the FPGA-firmware contract before any write. Serialize FPGA, firmware, and test
asset batches, then validate and obtain independent sign-off.
```

### FULL: timing-critical combinational path

```text
Use $run-fpga-workflow in FULL mode to repair this high-frequency critical path.
Read the exact target and current synthesis/implementation timing reports. Trace
function expansion, logic depth, cascaded priority/comparison/arithmetic chains,
MUX/decode depth, fanout, placement, and routing. Prefer minimal restructuring,
parallel decomposition, register cuts, or pipelining as supported by evidence.
Before adding a stage, freeze latency, protocol, throughput, alignment, backpressure,
reset, and error semantics. Re-run the confirmed implementation and STA flow; do
not invent a project-independent logic-depth threshold.
```

### FULL: official IP integration

```text
Use $run-fpga-workflow in FULL mode with IP_INTEGRATION. Confirm the project
identity, installed vendor tool/version, target part, existing managed IP, and
port/latency/reset contract. Prefer managed reuse, incremental regeneration,
source-view-safe staging/import, then official local Tcl/CLI. Use official GUI
automation only once if the current version cannot be scripted safely, and
export a reproducible recipe. Do not download an online XCI/IDF/IPC as product
configuration. Produce only the IP proof depth needed by this task.
```

### FULL: implementation QoR

```text
Use $run-fpga-workflow with claim_stage=IMPLEMENTATION_QOR. Freeze tool, part,
sources, constraints, seed, and strategy. Classify the highest-impact real
path or congestion bottleneck, change one primary variable, rerun the needed
implementation stage, compare WNS/TNS/hold/route status/congestion/resources/
runtime, and keep or revert from evidence. Do not start with random seeds,
whole-design Pblocks, repeated phys-opt, or pipeline changes.
```

### Board-validation planning

```text
Use $run-fpga-workflow in ANALYZE mode to prepare a board-validation plan.
Read the exact board, device, schematic, constraints, datasheet revisions, and
current reports. Define prerequisites, safe states, observability, instrument
connections, expected readings, stop conditions, recovery, and evidence capture.
All physical wiring, power-up, download, motion, heat, relay, laser, or high-voltage
actions remain mine to execute. Do not claim board PASS from simulation.
```

### FULL: cycle-accurate pipeline and simulation evidence

```text
Use $run-fpga-workflow in FULL mode for this pipeline change. Freeze one bounded
impact cone and a cycle contract, then run the temporal-evidence reviewer in
COMBINED shadow mode. Trace pre-edge values, RHS/NBA behavior, post-edge state,
token/data/valid/sideband alignment, stall, flush, reset, and first/last traffic.
Audit the reference model and checker independently, require a negative canary,
and do not treat a zero simulator exit or clean waveform as SIMULATION_PASS.
```

Additional concise prompts are available in [`examples/`](../../examples/).

## Checkpoint examples

Ask for checkpoints when a `FULL` implementation is long, cross-cutting, or timing-sensitive. A useful request is:

```text
Pause the sole product writer after each coherent slice. Freeze the current diff
and file hashes, have only the relevant read-only specialists review that exact
snapshot in parallel, consolidate severity-ranked findings into one repair list,
and return it to the same writer. BLOCKER/HIGH findings stop the next slice. Keep
the final reviewer independent from checkpoint coaching.
```

Typical checkpoint boundaries and reviewers:

| Checkpoint | Primary reviewers | Questions to resolve |
|---|---|---|
| Ports, parameters, and interface skeleton | Architect, interface, verification | Are widths, handshakes, latency assumptions, error behavior, and compatibility frozen? |
| FSM and error recovery | Architect, verification | Are all states reachable/recoverable, priorities explicit, and timeouts correctly dimensioned? |
| Datapath, FIFO, RAM, DSP, or pipeline | Architect, verification, timing | Are alignment, backpressure, boundaries, overflow/underflow, arithmetic width, and latency correct? |
| CDC and reset structure | CDC/timing, verification | Is each crossing appropriate, reset release safe, reconvergence controlled, and event loss/duplication tested? |
| CSR, IRQ, DMA | Interface, firmware planning, verification | Are side effects, concurrent events, ownership, abort, and compatibility correct? |
| Vendor wrapper and constraints | Vendor, CDC/timing, datasheet when needed | Do primitive/IP semantics, clocks, I/O delays, pins, and target boundaries match authoritative evidence? |
| Integrated diff | All affected specialists | Are repairs coherent across modules and is the evidence plan still sufficient? |

## Expected report sections

A complete workflow result should be easy to audit. Expect these sections, with non-applicable items stated explicitly:

1. **Conclusion and evidence level** — what was achieved, whether the verdict is conditional, and what is not proven.
2. **Mode, scope, and authorization** — selected mode, allowed write batch, immutable boundaries, and non-goals.
3. **Facts, assumptions, and unknowns** — `CONFIRMED`, `INFERRED`, and `UNKNOWN`, including blockers.
4. **Roles and conclusions** — roles invoked, conflicts found, and how evidence resolved them.
5. **Changed files by write batch** — product, firmware, and verification assets kept separate.
6. **Behavior, latency, and throughput** — protocol timing, backpressure, alignment, buffering, and errors.
7. **Clock, reset, CDC, and RDC** — domains, relationships, structures, constraints, and report status.
8. **Registers, IRQ, DMA, and firmware** — source of truth, semantics, sequencing, compatibility, and ownership.
9. **Vendor, target, and board impact** — portable/platform split, target-specific evidence, and user-only actions.
10. **Commands and actual evidence** — exact commands, tools/versions, seeds, exits, warnings, logs, waveforms, reports, WNS/TNS, utilization, CDC/RDC/DRC/methodology/power as applicable.
11. **Independent verdict** — `PASS`, `PASS WITH CONDITIONS`, or `FAIL`, with severity-ordered findings.
12. **Not-run checks and remaining risks** — explicit `NOT RUN`/`UNVERIFIED` items and next steps.

## Getting useful results

- Provide the repository or exact files instead of pasting only an error line.
- Identify the target device/board and tool version when they are already known.
- Share current reports and constraints; a stale report cannot validate a new diff.
- State whether latency, throughput, interfaces, addresses, and target behavior must remain unchanged.
- State which commands are authoritative. The workflow intentionally does not guess vendor commands.
- For a review-only task, say “do not modify files.” For implementation, explicitly authorize the desired scope.
- Keep confidential RTL, schematics, logs, credentials, and customer data out of public issues.
- For a new standard project, use `scripts/new-fpga-project.ps1`, confirm the target/tool/simulator facts, replace the deliberately fail-closed native adapter placeholders, and then use the three double-clickable `run.bat` entry points. The authoritative launcher is a depth-0 `project/par/<project-name>.xpr|.pds|.al`; no extra project container is generated. Runtime configures a tool root/environment, modifies only its process PATH, and invokes canonical commands by name without embedded executable paths. Formal ModelSim/Questa output stays under `simulation/work`, and Codex diagnostics under `codex_out`.

For claim boundaries and board-action gates, continue to [Safety and evidence](safety-and-evidence.md).
