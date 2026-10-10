# Roles and ownership

[README](../../README.md) · [Simplified Chinese](../zh-CN/roles.md) · [Architecture](architecture.md) · [Installation](installation.md) · [Usage](usage.md) · [Safety and evidence](safety-and-evidence.md)

The package defines nine core FPGA roles and four conditional cross-domain roles. Roles are intentionally narrow: architecture decides, one implementer writes product sources, verification authors test assets, a shadow specialist audits temporal evidence, and independent reviewers sign off without repairing their own findings.

## Complete role matrix

| Role | Trigger | Permission | Required deliverable | Prohibited actions |
|---|---|---|---|---|
| `fpga_architect` | FULL or concrete architecture need; ordinary bounded QUICK can record the contract in the main context | Strictly read-only | Facts/unknowns, scope/non-goals, architecture/data flow, performance budget, clock/reset/CDC impact, interface/regmap impact, vendor boundary, ownership order, acceptance criteria, risks, questions | Editing files; inventing project facts; silently choosing an ambiguous interface; self-signing implementation |
| `fpga_engineer` | Authorized RTL, official-IP, build-flow, physical-implementation, or release-packaging batch | Sole default product-source writer | One active mode, minimal diff, contract delta, official IP/build/QoR/release evidence as applicable, unverified items, review handoff | Overlapping modes without authorization; editing firmware/board design; changing unconfirmed contracts; approximate formal IP stubs; self-signing |
| `verification_engineer` | Concrete verification need or separately assigned test-asset writing; ordinary QUICK uses scoped non-author review without a mandatory separate verification role | Product read-only; may write only test assets in a later sequential batch | Requirement-to-test trace, risk-based test plan, assertions/models/scoreboards/coverage, exact regression evidence, gaps | Editing product RTL to make tests pass; deleting or weakening failures; sharing mutable EDA work areas; claiming unrun tests passed |
| `fpga_temporal_evidence_reviewer` | Shadow review for pipeline/FSM/FIFO/RAM behavior, changed verification assets, false-pass risk, or critical simulation evidence | Strictly read-only; shadow-only initially | Bounded impact-cone cycle table, model/checker independence audit, simulation classification, stable-ID findings, `NEEDS_PARTITION` when scope is unbounded | Scanning an entire large repository by default; editing RTL/TB/models; coaching repair; replacing CDC/STA/final sign-off |
| `fpga_cdc_timing_reviewer` | CDC_STRUCTURE, STA_COVERAGE, PHYSICAL_QOR, or TIMING_CLOSURE when the claim/impact requires it | Strictly read-only | Mode-scoped clock/reset/CDC, constraint, STA, or physical-QoR findings | Treating missing async-FIFO constraints as automatic DUT failure; forcing full P&R on compile/smoke; repairing source |
| `fpga_interface_architect` | CSR, command, mailbox, IRQ, DMA, firmware contract, or compatibility impact | Strictly read-only | Source-of-truth assessment, field/side-effect semantics, concurrency behavior, compatibility risks, firmware acceptance criteria | Editing RTL/firmware; inventing addresses or endianness; independently changing published fields; accepting duplicate hand-maintained regmaps |
| `fpga_vendor_platform_reviewer` | Vendor IP, primitive, target wrapper, clocking, I/O, memory, transceiver, or constraint impact | Strictly read-only | Per-target semantics plus IP_DISCOVERY/PREPARE/ACCEPTANCE proof depth, build/constraint consistency, evidence gaps | Editing wrappers/IP; copying online IP configuration; assuming primitive equivalence; claiming target support without evidence |
| `fpga_board_validation_engineer` | Board bring-up, electrical behavior, ILA/SignalTap, scope, analyzer, or field failure | Strictly read-only | Prerequisites, observable signals, staged procedure, expected readings, stop conditions, recovery, evidence interpretation | Operating hardware for the user; inventing pins/voltages; equating simulation with board proof; bypassing safety gates |
| `fpga_reviewer` | Final integrated review of implemented changes or requested acceptance claims | Strictly read-only and independent | Contract/snapshot/specialist integration, conflict and blocking-finding audit, risk sampling, `PASS`, `PASS WITH CONDITIONS`, or `FAIL` | Repeating every specialist's full traversal; participating in implementation; editing files; demanding untriggered evidence; ignoring missing required evidence |
| `system_architect` | Task crosses FPGA, hardware, and embedded firmware responsibilities | Conditional, strictly read-only | Cross-domain ownership, interfaces, failure propagation, sequencing, safety boundary, integrated acceptance plan | Replacing the FPGA lead for pure FPGA tasks; editing artifacts; inventing electrical or firmware facts |
| `embedded_engineer` | Confirmed FPGA-facing firmware change after interface contract is frozen | Conditional firmware-only sequential writer | Minimal driver/CSR/IRQ/DMA/error-recovery change, ordering/barrier semantics, firmware tests, FPGA handoff | Editing FPGA RTL/constraints; guessing register semantics; overlapping the FPGA write batch; self-signing cross-domain release |
| `hardware_datasheet` | Exact electrical, clock, reset, pin, power, or part behavior needs primary-source evidence | Conditional, strictly read-only | Part number, document title/revision/date, page/table/figure, quoted limit or semantic, applicability and uncertainty | Editing design files; relying on unsourced recollection; mixing revisions or part variants; declaring a board safe from a generic family guide |
| `independent_reviewer` | Cross-domain release or safety-critical/high-energy behavior | Conditional, strictly read-only and independent | Integrated FPGA/hardware/firmware evidence audit, safety-boundary verdict, remaining user actions | Editing artifacts; replacing project certification; accepting inferred electrical facts; signing a release it helped implement |

Ten role TOML files explicitly set `sandbox_mode = "read-only"`: all roles except the three conditional writers or write-capable roles (`fpga_engineer`, `verification_engineer`, and `embedded_engineer`). Write capability does not imply unrestricted scope; it is activated only by explicit task authorization and the assigned sequential batch.

## Five product-writer modes

The single product writer uses exactly one primary mode per coherent batch:

| Mode | Owns | Does not imply |
|---|---|---|
| `RTL_IMPLEMENTATION` | RTL, wrappers, necessary constraints, observable cycle-contract delta | IP regeneration, P&R, or release |
| `IP_INTEGRATION` | Managed official IP configuration, official recipe, project integration, proof packet | Downloading online IP files or using approximate stubs |
| `BUILD_FLOW` | BAT/Tcl/DO, file lists, paths, libraries, native tool entry points | Changing RTL to hide environment/script failures |
| `PHYSICAL_IMPLEMENTATION` | Evidence-triggered implementation QoR and timing-closure experiments | Default seed/strategy/Pblock/phys-opt changes |
| `RELEASE_PACKAGING` | Explicitly authorized bit/bin/mcs, manifest, hash, and release naming | Flash programming or external publishing |

Power acceptance is NOT APPLICABLE unless the user or a real power, thermal,
safety, or release budget activates it.

## FULL/high-risk write order and ordinary QUICK exception

| Phase | Active owner | Product RTL / constraints / wrappers | Firmware | Testbench / assertions / models | Review output |
|---|---|---:|---:|---:|---:|
| Evidence baseline | Coordinator + read-only roles | No | No | No | Yes |
| Architecture and pre-review | FULL/needed `fpga_architect` + relevant specialists; QUICK main-context contract | No | No | No | Yes |
| Product implementation | `fpga_engineer` | **Yes** | No | No simultaneous test writing; ordinary QUICK test assets follow in a scoped self-test phase | No self-sign-off |
| Checkpoint review | Relevant read-only specialists | No | No | No | **Yes** |
| Firmware batch, if required | `embedded_engineer` | No | **Yes** | No | No self-sign-off |
| Verification-asset batch, if required | Ordinary QUICK: same `fpga_engineer` context in later self-test phase; otherwise `verification_engineer` | No | No | **Yes** | Verification evidence |
| Isolated validation | Assigned runner under coordinator control | No source editing | No source editing | No failure suppression | Commands/reports |
| Temporal evidence shadow | `fpga_temporal_evidence_reviewer`, when triggered | No | No | No | Bounded independent evidence findings |
| Specialist re-review | Only affected specialists; ordinary QUICK acceptance-asset review may be covered by the one qualified non-author report | No | No | No | **Yes** |
| FPGA final review | `fpga_reviewer` | No | No | No | **Independent verdict** |
| Cross-domain final review, if required | `independent_reviewer` | No | No | No | **Independent verdict** |

The default order is:

```text
FPGA product sources -> optional firmware -> optional verification assets
                     -> isolated validation -> specialist re-review -> final review
```

No two write batches overlap in the same checkout. A finding returns to the writer that owns the affected artifact. The relevant reviews and validation are then repeated against the integrated result.

## Proportionate review

Roles are routed by risk and by the claim the user needs, not invoked to fill every box. A smoke compile/elaborate/run may finish with `DIAGNOSTIC_ONLY` evidence and does not require a reference model, negative canary, formal audit, CDC report, or final release verdict. Those gates activate when the result is used for the corresponding functional, formal, CDC/timing, electrical, or release acceptance.

Five boundaries remain hard at every profile: one writer per checkout, no author self-signing changed acceptance assets, no fabricated evidence, correct failure ownership, and explicit CDC/electrical safety handling.

When a user explicitly requests a minimal source edit, `fpga_engineer` first gives a brief reasoned statement of root cause, why that location is the narrowest correct owner, contract impact, and the smallest useful check. It then edits without an extra approval pause unless the change would alter interface, latency/throughput, clock/reset/CDC, error, or safety semantics.

## Who supervises the product writer?

During implementation, the final reviewer stays independent. Critical supervision comes from the technical and specialist roles:

- `fpga_architect`: architecture, state machines, buffering, performance, and error behavior;
- `verification_engineer`: observability, assertions, boundaries, backpressure, faults, and recoverability;
- `fpga_cdc_timing_reviewer`: clock/reset structure, CDC/RDC, combinational depth, constraints, and actual critical paths;
- `fpga_interface_architect`: register semantics, IRQ/DMA ordering, concurrency, and compatibility;
- `fpga_vendor_platform_reviewer`: primitive/IP semantics, wrappers, constraints, and per-target consistency;
- `fpga_board_validation_engineer`: electrical prerequisites, instrumentation, safe states, and board-evidence quality.

The coordinator selects only the relevant reviewers for each frozen checkpoint, consolidates disagreements from evidence, and sends one repair list to `fpga_engineer`. Reviewers never compete to edit the product code.

## Finding format

Actionable review findings should contain:

1. severity: `BLOCKER`, `HIGH`, `MEDIUM`, or `LOW`;
2. exact file and tight line range;
3. trigger condition;
4. engineering impact;
5. supporting project or report evidence;
6. required repair rather than a vague preference; and
7. the test or report that must be re-run.

Conflicting conclusions are surfaced, not averaged. A current project report or authoritative project specification outweighs a generic heuristic. If the evidence cannot resolve a decision that changes the interface, clocking, reset, safety, licensing, or acceptance standard, the item becomes an explicit blocking question for the user.

Next: see how these roles are scheduled in the [architecture](architecture.md) and use the copyable prompts in [usage](usage.md).

Local ordinary bounded QUICK uses a necessary main-context contract, one writer with sequential product/self-test phases, and one qualified non-author technical/member acceptance report. The extended default sequence above applies to FULL or triggered specialist needs, not an obligatory ordinary-task role chain. Preserve independent acceptance of changed checkers. See the installed human-checkpoints-and-ila reference.
