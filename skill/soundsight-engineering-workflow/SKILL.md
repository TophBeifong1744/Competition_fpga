---
name: soundsight-engineering-workflow
description: Run evidence-gated FPGA or embedded-system competition development from hardware and interface freeze through modeling, RTL, simulation, timing, board measurement, reproducible delivery, and failure review. Use when planning, executing, reviewing, or reporting a competition engineering workflow; do not use it to claim implementation success from plans or lower-level evidence.
---

# Evidence-Gated Engineering Workflow

Use this workflow to decide what may be implemented next, what evidence is missing, and what can be claimed. Preserve the project's scope, repository state, and authorization boundary.

## Start from evidence

Before changing implementation files:

1. Read the applicable competition requirements, project README, roadmap, team boundaries, engineering flow, validation plan, and current hardware/interface audit.
2. Record the allowed paths and actions. Treat a request to inspect, plan, or review as read-only unless implementation is explicitly authorized.
3. Inventory evidence with source, revision or hash, acquisition method, result, limitations, and owner. Classify every item as `verified`, `candidate`, `conflicting`, `missing`, or `failed`.
4. State the current gate and the earliest unmet prerequisite. Do not start downstream RTL, integration, procurement, or performance claims past that point.

Use [record-templates.md](references/record-templates.md) when creating project records. Keep the records in a project-approved location; do not invent an evidence directory without authorization.

## Keep evidence classes separate

Maintain distinct rows and artifacts for:

- model evidence: mathematical or bit-accurate reference behavior on versioned inputs;
- simulation evidence: self-checking RTL or subsystem results from the same contract and vectors;
- synthesis and timing evidence: target device, constraints, clock definitions, utilization, CDC findings, unconstrained paths, WNS, TNS, and WHS;
- board evidence: identified physical hardware, wiring, instruments, firmware/bitstream, procedure, raw measurements, repetitions, and environmental conditions.

Documentation review and static checks are additional evidence classes, not substitutes for any of these four. Never copy `PASS` from one class into another.

## Apply the stage gates

Evaluate gates in order. A later gate may be prepared in parallel only when that work does not assume an unfrozen upstream fact or create a misleading completion claim.

### G0 - Requirements and scope

Require a traceable requirement map, target deliverables, team or division eligibility, anonymity and licensing constraints, success metrics, authorized paths, and explicit exclusions.

### G1 - Hardware and interface freeze

Require physical identity and revision evidence, complete device part and speed grade where tool targeting depends on it, power and I/O levels, clocks and reset, pins or connectors, peripheral data sheets, data formats, synchronization semantics, and a reviewed interface contract. Candidate documents alone do not prove the connected hardware.

Stop downstream interface-dependent RTL when a missing fact could change ports, timing, constraints, clock-domain crossings, numeric format, or safety.

### G2 - Model and acceptance baseline

Require versioned inputs, units and conventions, deterministic seeds or captured-data metadata, expected outputs, edge and failure cases, frozen metrics, and a reproducible floating-point or bit-accurate baseline. Separate predicted performance from measured performance.

### G3 - RTL and simulation

Require a frozen interface and numeric contract, reviewable RTL, assertions or a self-checking testbench, normal/boundary/fault/backpressure cases as applicable, and comparison against the same model/vector revision. Record the first mismatch and identifiers such as sample, frame, transaction, or cycle.

### G4 - Synthesis, implementation, and timing

Require the actual target device and tool version, reproducible project inputs, explained critical warnings, CDC review, constrained clocks and I/O, zero unexplained unconstrained paths, resource results, and timing results against the frozen target. A successful synthesis exit code is not a timing pass.

### G5 - Board measurement

Require the identified board and peripherals, matching build hashes or versions, wiring and instrument setup, test procedure, raw logs, repetitions, acceptance comparison, and observed failure boundaries. Simulation or timing results cannot mark this gate passed.

### G6 - Reproducible delivery

Require clean-build or explicitly recorded dirty-state provenance, exact commands, tool versions, input and output hashes, deploy steps, report/video traceability, and a rerun by the team or an isolated environment. Generated caches and local GUI state are not source-of-truth inputs.

### G7 - Failure review and boundary statement

For every material failure, record observation, affected scope, evidence, attempted corrections, root-cause confidence, stop reason, safe workaround if any, and the condition for reopening. Preserve failed cases that define the system's honest operating boundary.

## Decide gate status

Use exactly one status per gate:

- `PASS`: every acceptance criterion has direct, traceable evidence from the required class;
- `BLOCKED`: required evidence or authority is missing, so the gate cannot yet be evaluated or completed;
- `FAIL`: the gate was executed and an acceptance criterion was not met;
- `NOT_RUN`: execution has not occurred and no blocking judgment is being made.

List evidence IDs beside each criterion. If evidence conflicts, keep both records, mark the gate `BLOCKED`, and resolve the conflict at its source. Never weaken a criterion after seeing results without recording who changed it, why, and which earlier results became incomparable.

## Record AI-visible collaboration

Record only user-visible prompts, assistant answers or summaries, accepted changes, human corrections, reasons, commands, and verification results. Hidden reasoning or chain-of-thought is neither available nor required and must not be presented as a competition deliverable. A human correction is complete only after its effect is revalidated and linked to new evidence.

## Produce the handoff

Return:

1. the current gate and status;
2. verified facts, candidates, conflicts, and missing facts;
3. evidence added or commands run, with actual results;
4. files changed and untouched scope;
5. the next authorized action that does not cross the gate;
6. failed checks and explicit stop conditions;
7. separate model, simulation, timing, and board claims;
8. reproducibility and AI-visible interaction records needed for the competition report.

Stop when the next action needs missing physical evidence, a material user decision, new authorization, unsafe hardware assumptions, or a prerequisite gate that is `BLOCKED` or `FAIL`. Report the blocker; do not fill it with a plausible generic design.
