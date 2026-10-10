# Safety and evidence

[README](../../README.md) · [Simplified Chinese](../zh-CN/safety-and-evidence.md) · [Architecture](architecture.md) · [Roles](roles.md) · [Installation](installation.md) · [Usage](usage.md)

The workflow separates engineering evidence by level. “Tested” is not a sufficient claim unless the test, target, tool, result, and remaining gaps are clear. A higher level may depend on lower levels, but passing one level never automatically proves another.

## Evidence ladder

| Evidence level | What it can establish | What it does **not** establish |
|---|---|---|
| Requirements and project SSOT | Intended interfaces, behavior, target facts, constraints, acceptance criteria, and unchanged boundaries | That the implementation matches the specification or that the specification is complete |
| Static source review | Obvious RTL defects, width/sign issues, state-machine gaps, suspicious crossings, constraint intent, interface inconsistencies, and verification gaps | Simulator behavior, synthesized structure, implementation timing, electrical behavior, or hardware operation |
| Lint and elaboration | Parse/elaboration success and tool-detected structural/style issues for the selected files and parameters | Functional correctness, CDC safety, timing closure, complete constraints, or board readiness |
| RTL simulation | Behavior exercised by the exact testbench, parameters, clocks, resets, stimulus, assertions, model, and seed | Untested behavior, analog effects, metastability, structural CDC correctness, implementation timing, or real board operation |
| Formal proof | The asserted property under the exact model, assumptions, bounds, abstractions, and tool result | Properties not asserted, behavior excluded by assumptions, non-vacuity without checks, analog behavior, physical timing, or board readiness |
| CDC/RDC analysis | Tool-classified crossing/reset structures, reconvergence risks, synchronization patterns, and waiver status for the analyzed netlist/design | Functional correctness of payload protocols, acceptable MTBF without assumptions, timing closure, or hardware success |
| Synthesis | Mapping/elaboration for a target, inferred resources, warnings, utilization estimates, and post-synthesis structure | Routed timing closure, final congestion, electrical correctness, a valid bitstream, or board operation |
| Implementation and STA | Placement/routing outcome, analyzed setup/hold and related checks, WNS/TNS, clock interactions, congestion, and target-specific implementation reports | Behavior outside constrained/analyzed paths, correctness of false-path assumptions, power/electrical safety, or board operation |
| DRC and methodology reports | Tool-detected rule and methodology status for the exact run | Functional correctness, complete constraints, timing closure unless explicitly covered, or board proof |
| Power analysis | Estimated or measured power under stated activity, environment, and model assumptions | Safe regulator/thermal behavior under all workloads or actual board temperature without measurement |
| Instrument measurement | Observed voltage, clock, timing, protocol, or signal behavior at specified nodes using stated equipment and setup | Unmeasured nodes, untested operating conditions, complete functional correctness, or long-term reliability |
| Board test | Behavior of the exact bitstream, hardware revision, setup, environment, procedure, and test coverage | Other boards, lots, temperatures, voltages, tool builds, bitstreams, operating modes, or certification |

The evidence chain should preserve identity: source revision/diff, target, parameters, tool and version, exact command, seed where relevant, exit status, significant warnings, and log/report/waveform/counterexample location. A report generated from an older checkpoint cannot validate the latest RTL repair.

## Proportionate evidence profiles

`DIAGNOSTIC_SMOKE` is for source discovery, compile, elaboration, bounded execution, and path/tool diagnosis. It needs enough information to reproduce the command and understand warnings or failure ownership. It does not require an independent reference model, a full scoreboard, or a negative canary, and it cannot establish `SIMULATION_PASS`.

`FUNCTIONAL_ACCEPTANCE` activates the complete simulation-evidence chain because the run is being used to accept DUT behavior. `SPECIALIST_ACCEPTANCE` activates the relevant formal, CDC/RDC, implementation/STA, electrical, or release evidence only when that claim is requested. Evidence that is irrelevant to the scoped claim may remain `NOT RUN` without making a diagnostic task fail.
Qualify each profile with one claim stage: PREFLIGHT, COMPILE, SIM_SMOKE, FUNCTIONAL_SIM, SYNTHESIS, IMPLEMENTATION_QOR, TIMING_CLOSURE, FORMAL, RELEASE, or BOARD_PREP. A stage limits what the result claims; it does not weaken hard ownership, safety, or evidence-integrity rules. Power is NOT APPLICABLE by default. Activate power evidence only for an explicit request or actual power, thermal, safety, or release budget, and state activity provenance when used.

## Required claim language

Use precise labels:

- `CONFIRMED`: directly supported by current project evidence that was read.
- `INFERRED`: a reasoned conclusion whose assumptions are stated.
- `UNKNOWN`: required information is absent or conflicting.
- `NOT RUN`: the check was not executed in the current work.
- `UNVERIFIED`: the evidence is unavailable, unread, stale, or insufficient for the claim.
- `PASS`: all acceptance conditions in scope are met by current evidence and no blocking finding remains.
- `PASS WITH CONDITIONS`: the accepted result has explicit residual conditions or evidence gaps that do not invalidate the scoped conclusion.
- `FAIL`: an acceptance condition failed or a `BLOCKER`/`HIGH` issue prevents completion.

Examples:

- “RTL simulation passed for three listed tests and seeds” is narrower and more useful than “verified.”
- “Synthesis completed; implementation STA was `NOT RUN`” does not mean timing closure.
- “No errors were observed in this board loopback duration” does not prove all addresses, alignment, or absolute sampling margin.
- “CDC report is clean” is not sufficient unless the exact report, tool/version, waivers, clocks, and analyzed revision are identified.

## Evidence integrity rules

- Do not disable a warning, broaden a clock group, add a global false path, or expand a waiver merely to make a report green.
- Every waiver needs a technical reason, exact scope, owner, validity assumptions, and regression method.
- Do not delete, weaken, skip, or change a failing test to claim success unless the requirement itself was explicitly corrected and reviewed.
- Check formal assumptions for over-constraint and proofs for vacuity; retain counterexamples and cover evidence.
- When formal is used for acceptance, have the independent FPGA reviewer check property/harness identity, assumptions, bounds/depth, vacuity, cover reachability, counterexamples, abstractions, tool/version/command, and author independence. Do not require formal work when it is outside the requested claim.
- Use isolated output directories for parallel EDA jobs. Shared mutable project databases or simulation libraries make evidence non-reproducible.
- Record significant warnings even when a command exits successfully.
- Do not use stale DCPs, netlists, reports, bitstreams, or waveforms as proof for a changed source tree.
- Keep target-specific claims target-specific. One vendor or board build does not validate every wrapper.

## High-energy user-action gate

Physical actions that can energize, move, heat, illuminate, switch, or damage hardware remain under qualified human control. This includes, but is not limited to:

- connecting or changing wiring, probes, jumpers, supplies, loads, or termination;
- power-up, configuration/download, reset release, or clock injection;
- motors, actuators, heaters, lasers, relays, solenoids, high-voltage rails, and other energy outputs;
- changing voltage, drive strength, I/O standard, slew, termination, or power sequencing;
- attaching oscilloscopes, logic analyzers, current probes, or other instruments where loading or grounding can cause damage.

An agent may prepare and review the procedure, but the user performs the physical step. Every procedure should state:

1. exact board and hardware revision;
2. exact bitstream/build identity and tool version;
3. authoritative schematic, constraint, and datasheet references;
4. prerequisites and safe initial state;
5. instrument and probe requirements, including ground/reference precautions;
6. one bounded action at a time;
7. expected readings and acceptable limits;
8. immediate stop conditions;
9. de-energization and recovery steps; and
10. evidence to capture before proceeding.

Reset, unconfigured, clock-loss, communication-loss, watchdog, timeout, and fault states should drive energy-controlling outputs to a project-defined safe state. The safe value and polarity must come from project evidence; this package contains no default pin, voltage, or active-level assumptions.

## Board-release boundary

These are useful milestones, but none alone is a board release:

- source review complete;
- lint/elaboration clean;
- simulation or formal checks pass;
- synthesis completes;
- a bitstream is generated;
- CDC/RDC or STA reports are clean;
- one board test passes.

A board-release conclusion requires the project's own acceptance matrix across the applicable design, timing, CDC/RDC, constraints, DRC/methodology, power/electrical, configuration, observability, fault-recovery, and hardware-test evidence. Safety-critical systems may also require organizational processes, certification, independent validation, traceability, and documentation outside this repository.

## Scope of this project

Codex FPGA Engineering Workflow is a process and prompt package. It does not:

- certify functional safety, electrical safety, security, or regulatory compliance;
- supply board-specific constraints or electrical facts;
- replace vendor documentation or qualified engineering review;
- operate physical hardware;
- guarantee that generated RTL is correct, synthesizable, portable, or timing-clean without project evidence; or
- turn package validation into FPGA-project validation.

Use the [workflow modes and prompts](usage.md) to request an evidence-qualified result, and consult [SECURITY.md](../../SECURITY.md) before sharing logs or design artifacts.
