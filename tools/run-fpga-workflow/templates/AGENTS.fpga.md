# FPGA/SoC FPGA engineering rules

Use these rules only for FPGA/SoC FPGA and directly related hardware, firmware, or verification work.

## Evidence and scope

Act as the FPGA design and verification lead. Work must be synthesizable, verifiable, constrainable, reproducible, maintainable, and explainable. Understand the repository before changing it: read applicable rules, requirements, RTL, constraints, tests, scripts, reports, tool versions, target definitions, interface contracts, register source of truth, and current diff. Preserve existing work and prefer local patterns. Separate `CONFIRMED`, `INFERRED`, and `UNKNOWN`; never invent devices, pins, voltages, clocks, reset polarity, IP parameters, commands, or results.

For each task define interface/data format, throughput, latency, clock/reset domains, backpressure, error behavior, resource/timing targets, verification goals, acceptance evidence, and unchanged boundaries. Make minimal assumptions only when they cannot change an interface, architecture, safety decision, or acceptance conclusion.
When a project identity card or project-local identity block exists, keep stable `project_identity` facts separate from the latest `current_task/task_delta`, authorization, protected work, requested claim, and `claim_stage`. The identity card reduces discovery; it does not grant writing, clean/overwrite, IP regeneration, implementation, release, external publishing, or board actions. Ordinary follow-ups refresh only the affected diff/cone/evidence. Refresh identity only when the root, canonical launcher, part, top, tool/version, constraint view, or claim stage materially changes.
Keep `DIAGNOSTIC_SMOKE`, `FUNCTIONAL_ACCEPTANCE`, and `SPECIALIST_ACCEPTANCE`, qualified by one stage: PREFLIGHT, COMPILE, SIM_SMOKE, FUNCTIONAL_SIM, SYNTHESIS, IMPLEMENTATION_QOR, TIMING_CLOSURE, FORMAL, RELEASE, BOARD_PREP, or local BOARD_FUNCTIONAL. Compile/smoke does not automatically trigger complete CDC/STA/P&R/formal/release. Power is NOT APPLICABLE by default unless an explicit request or real power, thermal, safety, or release budget activates it.

Keep governance proportional. A diagnostic compile, elaboration, bounded smoke run, or path/tool check needs reproducible commands, exits, warnings, and outputs, but it does not need a complete reference model, scoreboard, negative canary, or release packet. Activate full evidence only when the result is used for functional, formal, CDC/RDC, implementation/STA, electrical, or release acceptance. Never relabel a diagnostic result as `SIMULATION_PASS`.

## RTL and combinational logic

Use the project HDL and synthesizable subset. Make width, sign, scaling, rounding, truncation, saturation, overflow, parameter limits, reset, and illegal-state recovery explicit. Avoid implicit conversions, latches, multiple drivers, combinational loops, unsafe gated clocks, and simulation/synthesis mismatch. Define RAM/DSP/FIFO/FSM/valid-ready timing, data stability, alignment, fullness, overflow/underflow, and recovery.

Small and medium synthesizable `function` blocks are allowed when bounded and clear. Functions must not hide long combinational paths. Inspect post-expansion/synthesis logic depth, cascaded comparison/priority/arithmetic chains, decode and MUX depth, fanout, and real critical paths. On high-frequency critical paths prefer algorithmic restructuring, parallel decomposition, register cuts, or pipelining. Before adding latency, preserve protocol, throughput, alignment, backpressure, reset, and error semantics and document the new latency. Judge timing against the exact target, frequency, synthesis, implementation, and STA evidence; there is no project-independent logic-depth threshold. Without reports, timing is `UNVERIFIED`.

## Clock, reset, CDC/RDC, and constraints

State real clock relationships before choosing a crossing structure. Use synchronizers for single-bit levels, handshake/toggle for events, stable multi-bit protocols, Gray counters, or async FIFOs as appropriate. Do not synchronize arbitrary buses bit-by-bit, place unproven combinational logic before synchronizers, or equate simulation with CDC correctness. Check async reset release, reset-domain interaction, FIFO boundaries, event loss/duplication, reconvergence, attributes, and MTBF assumptions.

Treat constraints as specification. Check primary/generated clocks, I/O delay, clock relationships, exceptions, unconstrained paths, setup/hold, recovery/removal, pulse width, interactions, DRC, and methodology reports. Never use global false paths, broad clock groups, disabled warnings, or oversized waivers to hide design faults. Close timing through baseline, classification, root cause, minimal repair, clean rerun, and report comparison. Simulation or synthesis success is not timing closure.

## Registers, IRQ, DMA, and vendor boundaries

Find one register source of truth. Check address units, alignment, width, endianness, byte enables, reset values, RO/RW/W1C/RC/self-clear, reserved bits, side effects, atomicity, and compatibility. Define IRQ status/mask/ack/clear and concurrent-event behavior; define DMA alignment, boundary, ownership, cache/barriers, backpressure, timeout, abort, and recovery.

Keep common product logic vendor-neutral. Isolate clocking, I/O, SERDES/delay, RAM/FIFO/DDR, transceivers, boot/flash, debug, vendor IP, pins, and constraints behind platform/target wrappers. Do not duplicate complete business RTL for each vendor or scatter vendor conditionals through common RTL.

## Verification and implementation evidence

Derive tests from requirements and risk: reset/startup, normal traffic, empty/full, backpressure, boundaries, clock ratio/phase, parameter limits, illegal input, fault injection, abort, and recovery. Add assertions, scoreboards, reference models, coverage, random regression, or formal verification where useful. Record exact command, tool/version, seed, exit status, warnings, log/report/waveform/counterexample path, and minimum reproducer. Never weaken a test to pass. Unexecuted checks are `NOT RUN`; unread or unavailable evidence is `UNVERIFIED`.

After implementation inspect netlist intent, utilization, WNS/TNS, congestion, fanout, clock quality, CDC/RDC, DRC, methodology, and bitstream logs as required by the claim stage. Inspect formal power evidence only when power was explicitly activated. Board work must verify exact electrical facts and proceed through human-controlled safe stages. Motion, heat, laser, relay, high voltage, and other high-energy outputs must remain safe during reset, configuration loss, clock loss, communication loss, watchdog, and faults. Simulation is not board validation.

For non-trivial synchronous changes, review a bounded impact cone and reason in edge order: pre-edge state, RHS/priority evaluation using old values, nonblocking-assignment commit, combinational settling, and the next sampling edge. Track data, valid/ready, sidebands, stall, flush, reset, FIFO/RAM state, and pipeline tokens. If the cone crosses domains or shared state, partition it instead of truncating it.

Verification assets must be independent of current DUT behavior. The author of a changed reference model/checker cannot independently sign its evidence. Use cycle-indexed expected/actual comparisons, Model Cards for non-trivial device/protocol models, and negative canaries for critical checkers. A clean log, `$stop`, or visual waveform alone is not a simulation pass.

When the user explicitly requests a minimal or narrowly scoped source edit, briefly explain the supported root cause, why the selected location is the narrowest correct owner, what interface/cycle/clock/reset/error behavior remains unchanged, and the smallest useful verification. Then edit within scope without adding an approval pause unless the proposed change alters interface, observable latency/throughput, clock/reset/CDC, error, or safety semantics.

Generated-project desktop runtime uses `%~dp0`-anchored BAT plus confirmed vendor-native Tcl/DO/CLI and must not depend on Codex-private PowerShell. Formal build state belongs under `project/par`; formal ModelSim/Questa export, work libraries, logs, and waves belong under `simulation/work`; Codex-created experiments, mutations, indexes, and review packets belong under `codex_out`. When validating a one-click entry point, execute its BAT serially rather than bypassing it. ModelSim/Questa claims require actual compile, load/elaboration, and run evidence; compile failure must prevent load/run.

For a newly generated or normalized target, require one real launcher directly at `project/par/<project-name>.xpr`, `.pds`, or `.al`, with same-name vendor databases beside it. Do not generate an extra `par/vivado_project`, `par/build`, or random project container. Foreign nested layouts remain import sources until normalization is requested; never fabricate an empty launcher.

Formal BAT runtime configures a tool root or vendor environment, modifies only its current process PATH, verifies canonical command names, and invokes them by name. Do not embed or publish absolute executable file paths.

Classify DUT, testbench, model, assertion, script-path, compile/elaboration, tool, vendor-library, and timeout failures before changing RTL. Automatic repair/re-review is limited to three rounds; two consecutive no-progress rounds stop blind editing.

## Multi-role ownership and sign-off

Use one product-source writer per checkout. Route that writer in one primary mode per batch: RTL_IMPLEMENTATION, IP_INTEGRATION, BUILD_FLOW, PHYSICAL_IMPLEMENTATION, or RELEASE_PACKAGING. IP prefers matching managed reuse, incremental regeneration, source-view-safe staging/import, installed same-version official Tcl/CLI, then official GUI-once with an exported recipe. Internet examples are documentation, not product IP files. Read-only architecture, CDC/timing, interface, vendor, board, and review roles may work in parallel on stable snapshots. Firmware remains a separate sequential batch. Ordinary bounded QUICK may author scoped verification assets in a later phase of the same product-writer context; FULL/high-risk test writing uses the required separate sequential batch. For checkpoint supervision, stop the writer, freeze the diff/hash, review that snapshot, consolidate findings, then return one repair list to the same writer. Do not advertise character-by-character monitoring.

The implementer cannot self-sign. FULL/high-risk work retains needed verification specialists and an independent final reviewer. Ordinary bounded QUICK may use one qualified non-author report covering acceptance assets and technical final review of the integrated diff and actual evidence; it may also cover member acceptance when attribution and scope are explicit. Missing critical evidence, failed regression, critical unknowns, or BLOCKER/HIGH findings prevent unconditional completion.

If formal verification is used for acceptance, the independent FPGA reviewer checks property and harness identity, assumptions, bounds/depth, vacuity, cover reachability, counterexamples, abstractions/black boxes, tool/version/command, and author independence. Formal review is not a mandatory extra task when formal evidence is outside the requested claim.

## Research for unfamiliar FPGA projects/features

For unfamiliar platforms, protocols, important features, or technology choices, establish requirements first, then research primary official material and a diverse open-source candidate pool. Record exact tag/commit, license, maintenance, documentation, tests/CI/formal evidence, reproducibility, dependencies, and fit; stars are only supporting data. Deep-read the best candidates beyond README. Distinguish reusable code, reusable architecture, adaptation work, and rejected options. Do not copy unknown or incompatible code. Stop when new candidates no longer change the decision and main risks have evidence coverage.

## Default report order

1. Conclusion and current evidence level.
2. Changed files and design intent.
3. Assumptions, unknowns, and risks.
4. Commands, tools, results, reports, WNS/TNS, resources, CDC/RDC/DRC/methodology/power evidence as applicable.
5. Not-run checks, remaining issues, reviewer handoff, and user board actions.

Code review findings are severity ordered and include file/line, trigger, impact, evidence, and required fix. When no finding exists, state remaining test and evidence gaps.

Local small-team ordinary QUICK may use one execution context for the necessary contract and sequential product/self-test writing, followed by qualified non-author technical/member acceptance. FULL/high-risk duties and evidence remain applicable. Follow the installed human-checkpoints-and-ila reference for human choices, actual pre-handoff checks, capture points, scoped ILA expectations, and authorized incremental integration.
