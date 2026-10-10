---
name: run-fpga-workflow
description: Evidence-driven FPGA/SoC FPGA workflow for architecture, cycle-accurate RTL, registers, CDC/RDC, timing, three-vendor toolflows, verification, board evidence, single-writer implementation, and independent sign-off. Use only for FPGA and directly related hardware/firmware/verification tasks.
---

# FPGA multi-role engineering workflow

Use the main conversation as coordinator. Invoke only roles relevant to the task. The goal is a traceable engineering result, not maximum agent count.

## 1. Authorization and mode

Writing requires an explicit request to implement, change, fix, or build. Risk never expands authorization.

- `ANALYZE`: read-only analysis, diagnosis, design, or review.
- `QUICK`: authorized, small, interface-preserving, single-clock, low-risk change.
- `FULL`: authorized new RTL, pipeline/FIFO/RAM behavior, CDC/RDC, regmap/IRQ/DMA, constraints, vendor IP, external timing, high-energy control, or significant refactor.

Do not use QUICK for clock/reset crossings, published interfaces, observable latency, external timing, vendor IP/constraints, safety/energy outputs, possible data loss, or critical ambiguity. Read [task profiles](references/task-profiles.md) for detailed routing.

## Small-team human-assisted policy (local adaptation)

For authorized project work, Codex implements project-owned RTL, BD recipes, XDC, IP configuration/generation recipes, and Vitis sources/configuration, performs focused self-tests and repairs, and adds a short Chinese purpose comment to each new or materially changed logical block. Do not hand-edit vendor-generated products or assume a format supports comments. The human chooses consequential goals, interfaces, numerical precision, architecture, clocks, device/IP versions, and resource tradeoffs from feasible options, pros/cons, and a reasoned Codex recommendation. Reuse prior choices; continue routine equivalent repairs within scope. Preserve explicit read-only tasks and protected files. Physical programming, reset, wiring, and motion remain authorized human actions.

Hand off when the candidate is ready for the next useful human operation. State its exact project/run, performed checks, limits, short steps, and screenshot/raw-report capture points. The human can open a matching existing run without rebuilding it. Codex analyzes raw evidence; screenshots support presentation rather than replace raw data. Read [human checkpoints and ILA](references/human-checkpoints-and-ila.md) for pre-handoff readiness, board scope, and integration.

For an ordinary bounded QUICK task, one execution context may state the necessary contract, write product and test assets in sequential phases, and self-test. Use one qualified non-author review for the exact candidate and acceptance assets; it may fulfill technical final review and member acceptance in one scoped report. A separately spawned architect or verification author is optional for this path, not an extra gate. FULL/high-risk work keeps the affected architecture, verification, CDC/STA/IP and other independent responsibilities. All 13 role files remain available.

## 2. Establish one evidence baseline

Read applicable `AGENTS.md` files, requirements, project SSOT, interface/register sources, RTL, constraints, tests, scripts, installed tool versions, current reports, and the current diff. Protect user work. Label facts `CONFIRMED`, `INFERRED`, or `UNKNOWN`. Never invent device/package, pin, voltage, clock/reset, address, protocol, IP configuration, vendor command, or result.
When an identity card or project-local identity block exists, read [project identity and live task delta](references/project-identity-and-task-delta.md). Normalize stable `project_identity` separately from the latest `current_task/task_delta`, authorization, sticky protected work, requested claim, and claim stage. An ordinary follow-up refreshes only the affected snapshot and cone; it does not repeat machine-wide discovery or silently retain stale task goals.

Create only the artifacts needed to support the requested claim under `codex_out/<run-id>/`. A small diagnostic or smoke run may need only a command/result record; a functional, timing, CDC, formal, or release acceptance claim needs the applicable stable artifacts:

- `task-contract.json`: scope, immutable behavior, authorization, and acceptance evidence;
- `snapshot-manifest.json`: revision, dirty-diff hash, source hashes, target, parameters, defines, and constraints;
- `impact-manifest.json`: affected modules/processes, clock/reset domains, forward data, reverse backpressure, sidebands, shared state, constraints, and tests;
- `cycle-contract.json`: accepted/completed edges, latency or window, throughput, alignment, stall, reset, flush, abort, and error behavior;
- `verification-plan.json`: Requirement -> Test -> Checker -> Cover and model independence;
- `ip-proof-packet.json`: official IP identity, generation method, configuration ownership, contracts, products, constraints, simulation, OOC, and reopen evidence;
- `run-manifest.json`: exact command, cwd, tool/version, target, seed, exits, libraries, logs, waves, and reports;
- `simulation-evidence.json`: cycle-indexed expected/observed behavior, first failure, checker drain, negative canaries, and proof packets;
- `findings-ledger.json`: stable IDs, snapshot, owner, status, evidence, repair, and reruns.

Use the templates in [workflow artifacts](references/workflow-artifacts.md). Do not create a full proof packet merely because the task is small. Artifacts organize evidence; they never replace source, elaboration, simulation, CDC/RDC, STA, or board results.

Separate formal user tool state from Codex diagnostics. Formal vendor project databases, native logs, and reports belong in `project/par`; formal ModelSim/Questa export files, local work libraries, logs, and wave databases belong in `simulation/work`; release artifacts belong in `release`. Codex-created experiments, parallel diagnostic copies, indexes, temporary libraries, mutations, and review packets belong in `codex_out/<run-id>`. If the user asks Codex to validate the formal desktop entry point, execute that BAT serially and allow its native output directories; a direct inner command does not prove the BAT works.

For newly generated or normalized targets, the canonical launcher is a depth-0 child of `project/par`: `project/par/<project-name>.xpr`, `.pds`, or `.al`. Same-name vendor databases are direct siblings. Do not wrap the formal launcher in `par/vivado_project`, `par/build`, or random job directories. Existing nested projects may remain as foreign import sources until normalization is requested; never create a fake launcher without confirmed target facts.

Formal generated BAT runtime does not embed absolute tool executable files. Configure a project-confirmed tool root or vendor environment, extend only the current process PATH, verify canonical commands, and invoke `vivado`, `vsim`, `vlog`, `vlib`, `vmap`, or the confirmed Pango/Anlogic command by name. Never persist PATH changes or publish a machine-specific executable path.

## 3. Lead, bounded impact, and specialist routing

The required task, impact, and cycle contracts, Requirement -> Design -> Test traceability, ownership, and acceptance are frozen by `fpga_architect` for FULL or when specialist architecture is needed; ordinary bounded QUICK records the necessary contract in the main execution context. Bound temporal review to one primary clock domain and one transaction/dataflow impact cone, including reverse `ready`/backpressure and aligned data, valid, last/keep, ID/tag, error, enable, reset, stall, flush, abort, FSM, counter, FIFO, and RAM state.

Return `NEEDS_PARTITION` rather than truncating when the cone crosses clock domains, touches shared state or common packages/macros, includes an unknown vendor black box, lacks stable unchanged boundaries, or exceeds the review context. Partition by domain, transaction, or shared resource and merge findings through one ledger. Read [temporal evidence](references/temporal-evidence.md) for the cycle and simulation protocol.

Run only relevant read-only specialists in parallel:

- CDC/RDC, clocks, constraints, STA: `fpga_cdc_timing_reviewer`;
- CSR/commands/IRQ/DMA/firmware contract: `fpga_interface_architect`;
- primitives/IP/wrappers/three-vendor target: `fpga_vendor_platform_reviewer`;
- electrical evidence and bring-up: `fpga_board_validation_engineer`;
- exact manual/model evidence: `hardware_datasheet`;
- cross-domain architecture: `system_architect` when needed;
- bounded cycle/simulation evidence: shadow `fpga_temporal_evidence_reviewer` in `STATIC_CYCLE`, `SIMULATION_EVIDENCE`, or `COMBINED` mode.

The temporal reviewer is the 13th role and is initially `SHADOW`: it is strictly read-only, does not coach repairs, does not replace CDC/RDC or STA, and does not issue the overall final verdict. QUICK does not invoke it by default. See [shadow rollout](references/shadow-rollout.md).

## 4. Single-writer implementation

Skip in ANALYZE. In one checkout, only `fpga_engineer` writes product RTL, constraints, platform wrappers, regmap implementation, or FPGA build scripts. Freeze and summarize its diff when done. If required, run `embedded_engineer` later as a firmware-only batch. In ordinary bounded QUICK work, the same `fpga_engineer` execution context may then write scoped TB/checker assets in a sequential self-test phase; use `verification_engineer` for independent test design or a separately assigned test-only batch when needed. Full/high-risk product and test writing retain their required separate sequential batches. No overlapping writers in one checkout. A test-asset author cannot independently sign their own evidence.
Route that writer in exactly one primary mode per batch: `RTL_IMPLEMENTATION`, `IP_INTEGRATION`, `BUILD_FLOW`, `PHYSICAL_IMPLEMENTATION`, or `RELEASE_PACKAGING`. After one coherent module/cone/IP/domain/toolflow slice, freeze a diff/hash checkpoint, run only relevant read-only reviewers against that snapshot, merge one findings ledger, and return stable IDs to the writer. Read [official IP integration](references/ip-integration.md) for IP work and [evidence-triggered physical implementation](references/physical-implementation.md) only for implementation-QoR or timing-closure work.

Repairs that answer existing review findings cite their stable IDs. Report a Cycle Contract Delta and affected cone only when observable cycle behavior changes. Verification authors cannot independently sign evidence produced by models/checkers they created or changed. Reviewers never edit findings away.

When the user requests a minimal or narrowly scoped source edit, the product writer briefly states the supported root cause, why the selected location is the narrowest correct owner, what interface/cycle/clock/reset/error behavior remains unchanged, and the smallest useful verification before editing. This is reasoning guidance, not an extra approval gate. Pause only when the proposed change would alter a published interface, observable latency or throughput, clock/reset/CDC behavior, error semantics, electrical safety, or another user-controlled contract.

For long/high-risk work, use stable checkpoints: stop the writer after a coherent slice; freeze diff/hash; have relevant read-only specialists review that exact snapshot; consolidate one repair list; return it to the owning writer; recheck only affected evidence. The final reviewer remains outside implementation coaching.

## 5. Deterministic project toolflow

Generated and formally normalized projects use the exact canonical directories `project/`, `project/par/`, `project/script/`, `simulation/`, `linter/`, `release/`, and `codex_out/` as described in [project layout](references/project-layout.md). Never generate numbered standard directories such as `project2`, `par2`, or `script2`. Existing foreign projects may be inspected or imported, but normalized output uses the canonical names. Keep visible script roots as entry-point surfaces: `project/script` contains the BAT, project setting, canonical source list, and one confirmed vendor Tcl/CLI flow; normalized `simulation/script` contains exactly `run.bat`, `setting.txt`, `src_list.txt`, and `vsim.do`. Generated exports, `modelsim.ini`, `.Xil`, libraries, logs, and waves stay under `simulation/work`. The formal user desktop runtime uses BAT plus vendor-native Tcl/DO/CLI and must not depend on a `pwsh.exe` visible only inside Codex. Package installation, Codex-side scanning, and scaffolding may still use PowerShell internally.
Treat copied or legacy XCI/IDF/IPC files as untrusted output-path carriers. Before generation, prove that the source view belongs to the current checkout; otherwise stage/import under the current project output or recreate through the installed same-version official tool. After Xilinx export, inspect actual compile order, defines, and include directories. A canonical `vsim.do` may recompile project RTL/TB with a confirmed missing define only after official IP models compile; approximate IP models remain prohibited.

Automatic vendor selection supports only:

- `project/par/*.xpr` -> AMD/Xilinx Vivado;
- `project/par/*.pds` -> Pango PDS;
- `project/par/*.al` -> Anlogic TD;
- fallback `*.xci` -> Xilinx, `*.idf` -> Pango, and `*.ipc` -> Anlogic only with Anlogic/TD/EG text markers.

Multiple supported vendors, unsupported vendor project markers, or missing evidence fail closed and prompt the user. A generated standard project contains exactly one selected adapter. Use [vendor adapters](references/vendor-adapters.md) and the deterministic helpers in `scripts/`; do not guess commands, fabricate primitive models, silently substitute versions, or modify global tool/library mappings.

Each `run.bat` locates itself with `%~dp0`, verifies deterministic RTL/IP/TB lists and preflight facts, invokes exactly one native adapter, and returns the real exit code. Build BAT defaults to a bounded compile/synthesis checkpoint and writes formal state under `project/par`. Simulation BAT defaults to the configured GUI simulator, supports `batch`, and writes formal state under `simulation/work`. An official library recipe may compile only for an exact supported vendor/tool/family/simulator tuple; Codex-built caches remain under `codex_out/_cache/simlibs`, while a confirmed user-maintained compiled library may be referenced by a project-local simulator mapping.

If the selected simulator is ModelSim/Questa, validate its actual `vlib/vmap/vlog/vcom`, load/elaboration, and run stages—XSim is not substitute evidence. Xilinx IP simulation generates output products and exports IP user/static files first. Inspect the actual Windows export artifacts instead of assuming a filename: Vivado can emit `.sh + compile.do` rather than `compile.bat`. A BAT/DO wrapper may invoke the emitted `compile.do`, create its required parent library, correct only a local `modelsim.ini`, return nonzero on compile failure, and block load/run after that failure. Never edit global simulator mappings.

## 6. Proportionate evidence profiles

Choose the profile from the claim, not from a desire to maximize process:

- `DIAGNOSTIC_SMOKE`: source discovery, compile, elaboration, bounded run, log collection, or path/tool diagnosis. Record the exact command, tool/version when available, exit codes, important warnings, and output paths. An independent model, full scoreboard, and negative canary are optional. The result is `DIAGNOSTIC_ONLY` or `INCONCLUSIVE`, never `SIMULATION_PASS`.
- `FUNCTIONAL_ACCEPTANCE`: activate the complete simulation-evidence rules below because the result will be used to accept DUT behavior.
- `SPECIALIST_ACCEPTANCE`: activate only the evidence family being claimed—formal, CDC/RDC, implementation/STA, electrical, bounded board behavior, or release—and keep all other evidence levels `NOT RUN` or `UNVERIFIED`. Board behavior uses an independent expectation, matched artifacts, known stimuli and raw captures; it does not automatically require a duplicate full simulation campaign.

The hard gates remain constant: one writer per checkout, no author self-signing their changed acceptance assets, no fabricated evidence, no weakening CDC/electrical safety, and failure routing to the correct owner.
Keep these three profiles and qualify the current claim with one `claim_stage`: `PREFLIGHT`, `COMPILE`, `SIM_SMOKE`, `FUNCTIONAL_SIM`, `SYNTHESIS`, `IMPLEMENTATION_QOR`, `TIMING_CLOSURE`, `FORMAL`, `RELEASE`, or `BOARD_PREP`, or local-adaptation `BOARD_FUNCTIONAL`. Do not create a competing profile system. Power is `NOT APPLICABLE` by default unless an explicit request or real power, thermal, safety, or release budget activates it.

## 7. Simulation evidence integrity

Verification derives from requirements and independent primary evidence, not current DUT behavior. Non-trivial device/protocol models require a [Model Card](references/model-card.md). Do not copy DUT RTL into the reference model, read internal DUT state to change expectations, adapt expected latency to observed implementation, or claim a forced/bypassed function was verified.

For `FUNCTIONAL_ACCEPTANCE`, scoreboards are cycle-indexed: record the accepted input edge and tag, due cycle/window, expected data/sidebands/error, observed edge, and early/late/drop/duplicate/reorder result. Critical acceptance checkers need an isolated negative canary. A `$stop`, clean log, or waveform without an independent checker is not proof of functional acceptance.

Classify failures before routing repairs:

`DUT_FAIL`, `TESTBENCH_FAIL`, `REFERENCE_MODEL_FAIL`, `ASSERTION_FAIL`, `SCRIPT_PATH_FAIL`, `COMPILE_ELAB_FAIL`, `TOOL_ENV_FAIL`, `VENDOR_LIBRARY_FAIL`, `TIMEOUT_HANG`, or `INCONCLUSIVE`.

Only `DUT_FAIL` routes directly to product RTL. Manual waveform evidence that contradicts automation revokes `SIMULATION_PASS` and first repairs/reviews the verification asset. Simulation never signs CDC/RDC or STA.

## 8. Bounded repair and independent sign-off

Use stable finding IDs and these statuses: `OPEN`, `FIXED_PENDING_REVIEW`, `VERIFIED_CLOSED`, `DUPLICATE`, `DISPUTED`, `NOT_APPLICABLE`, and `ACCEPTED_RISK`. Writers do not close their own findings. No new diff or evidence means a finding cannot be renamed and reopened as progress.

Allow at most three automatic repair/re-review rounds. At the first no-progress round, stop blind editing and rebuild the root cause with the architect and affected specialists. At two consecutive no-progress rounds, or after round three with an open BLOCKER/HIGH, stop and report the evidence boundary. Progress means fewer open BLOCKER/HIGH findings, a later first-failure point, an explainable changed failure signature, or added required evidence—not rewording or unrelated diffs.

After all write batches, re-run only affected specialists read-only against the same integrated snapshot. Then invoke separate `fpga_reviewer` when an implemented change or acceptance verdict requires it; add `independent_reviewer` for cross-domain or safety-critical releases. When formal verification is actually used for acceptance, `fpga_reviewer` independently audits the property/harness identity, assumptions, bounds/depth, vacuity and cover evidence, counterexamples, abstractions/black boxes, tool command/version, and author independence. Do not add a formal gate when formal evidence is not part of the requested claim. Shadow findings are specialist input and must be resolved by evidence, not automatically promoted or ignored. Missing critical evidence, failed regressions, disputed blocking findings, or open BLOCKER/HIGH prevents unconditional completion.
The final reviewer integrates the task contract, claim stage, snapshot identity, specialist reports, open blocking findings, conflicts, and claim boundaries. It samples the highest risks but does not repeat every specialist's complete traversal. Missing, stale, or contradictory required evidence routes back to the owning specialist; untriggered domains do not fail compile/smoke.

## 9. Private fault-library hook and improvement

The workflow improves through curated evidence, not model-weight retraining. A private after-sales fault library may be configured outside the public package. Query it only as a diagnostic lead, store sanitized match output in `codex_out/<run-id>/knowledge/`, and revalidate vendor/tool/version, subsystem, clock/reset, interface, trigger, and counterexamples against the current project. Never put private source documents, customer data, paths, or project facts in the public package, Memory, or global prompts.

Read [private fault library](references/private-fault-library.md) for schema, statuses, and the empty/config/query hook. Only cases with confirmed root cause and verified repair may become reusable; board-confirmed status is recorded separately. Follow [improvement policy](references/improvement-policy.md) and use the blank [evidence ledger](references/improvement-evidence.md).

## Minimum orchestration

- ANALYZE: main-context contract/analysis -> only relevant specialists -> independent final reviewer only for a requested sign-off verdict. No product writes.
- QUICK: necessary contract in the execution context -> one product writer with sequential scoped self-test assets -> one qualified non-author acceptance/technical-final review. Invoke architect/verification specialists only for concrete need; temporal shadow off by default. Self-checking never replaces non-author review.
- FULL: architect and stable artifacts -> relevant parallel pre-review -> sequential writers -> isolated validation -> affected specialists and optional temporal shadow -> final reviewer -> cross-domain reviewer when required.

Final output states mode/scope, assumptions/unknowns, roles and conclusions, changed files by write batch, behavior/latency/throughput, clock/reset/CDC/RDC, registers/IRQ/DMA/firmware, vendor/board impact, commands and actual evidence, sign-off verdict, remaining risks, and user board actions. Unexecuted checks are `NOT RUN`; unavailable or unread evidence is `UNVERIFIED`.

Ordinary small-team updates use a concise expected -> observed -> evidence -> next step report with candidate, scope, limitations and next owner; reference unchanged identity and approvals instead of repeating every final-output field. Preserve required missing-evidence disclosures.
