---
name: soundsight-engineering-workflow
description: Plan, execute, or review FPGA and embedded-project work using versioned interfaces, scoped integration decisions, separate validation evidence, and reproducible handoffs. Use when deciding what can proceed, what can be claimed, or how to deliver a tested package; not for board pin selection or algorithm design itself.
---

# Evidence-based engineering workflow

Turn the requested outcome and available evidence into a scoped action and handoff. Development permission, integration approval, acceptance evidence, and publication state are independent. An incomplete hardware milestone does not stop unrelated software or provisional-interface development.

## Establish this run's inputs

Read the current user request, applicable project rules, current status and the relevant interface, test or review artifacts. Use their actual paths; do not require SoundSight's filenames, roles, board, tools or milestone labels in another project. Old snapshots explain history, not current instructions. Identify explicit newer decisions that supersede older plans; unresolved contradictions only block the actions or claims that depend on them.

Record the requested outcome, author/reviewer, allowed paths and actions, input versions, existing approved work and any exclusions. Resume existing work rather than regenerate completed deliverables. Do not start from every historical audit or demand a complete evidence inventory for a small task.

For draft records or a competition handoff, read [record-templates.md](references/record-templates.md) and select only the needed sections. For examples and demonstrated limits, read [README.md](README.md). Neither file grants operational authority.

## Decide by action, not by the earliest incomplete milestone

| Decision | Evidence needed | What it does not mean |
|---|---|---|
| Develop within a working package | Authorized scope, sufficient software/interface assumptions, versioned provisional fields, isolated outputs | Hardware is frozen or active production files may be overwritten |
| Integrate a specified module/version | Project-designated reviewer, input/output and numeric contract, golden/tests, compute/storage/transfer budget, explicit approved scope | Every algorithm, measurement or later revision is approved |
| Accept a capability | Direct evidence for every claimed criterion on the specified input/build/environment | Another evidence class, board, operating condition or whole system passes |
| Publish/close a batch | Approved exact version and destinations, authorized integrator, post-integration checks, material disposition and local/remote reconciliation | A successful push proves hardware function or closes another person's work |

### Independent development

Proceed with parsers, models, testbenches, interface scaffolding and isolated prototypes under explicit versioned assumptions when authorized. Preserve old configurations; interface changes must not silently reinterpret old data. Fixed-code format tests are not acoustic or physical-performance simulations. Respect the project's actual research exclusions.

Allow a short, parseable real capture to start diagnostic work without waiting for long-duration acceptance. Preserve original sample IDs, discontinuities, errors, source and capture-point metadata. Unknown geometry or calibration may permit format/amplitude diagnostics while preventing validated direction or accuracy claims. Synthetic data and hardware test patterns must not be relabeled as physical recordings.

Stop only the relevant hardware operation when power, levels, pins or competing drivers are unknown or unsafe. Do not generate deployable guessed IO or connect it to hardware. Where a project explicitly defers noncritical margin measurements, record the authorized deferral and its symptom/reopening condition; do not recreate a blanket measurement gate. A known short circuit or driver conflict is not a deferred margin issue. Continue safe independent work.

### Package integration

Use the project's existing handoffs. A typical arrangement is a minimal versioned contract, early diagnostic data, and a complete algorithm package for one integration review; these are not mandatory names or extra review checkpoints for other teams.

At algorithm-package review, evaluate input/output, units/signs, validity/errors, golden and boundary tests, numeric ranges, per-frame operations, scheduling, storage and data movement. A feasibility budget can support limited prototype admission before final place-and-route reports exist. Missing final timing is not by itself a reason to prohibit all algorithm research. No budget or admission supports an unmeasured real-time claim.

Experiments inside the existing package do not need per-function or per-parameter approval. Material changes to an approved interface, budget or integration scope require renewed integration review; publication approval always binds the exact content being published. An author or author-side assistant cannot self-approve/self-integrate a review-required delivery. Follow the current project's designated reviewer/authorized integration role, not a name from an old example.

## Keep evidence and acceptance scoped

Maintain independent results for the classes actually involved:

| Class | Minimum useful record |
|---|---|
| Model (floating or bit-accurate) | Input/configuration/seed or raw-capture identity, assumptions, expected/actual outputs, errors and failure cases |
| RTL simulation | Source and vector versions, simulator, self-check/scoreboard, normal/boundary/fault cases, first mismatch and sample/frame/cycle |
| Synthesis/implementation/timing | Tool/device/build, constraints/clocks, resource report, CDC and warnings, WNS/TNS/WHS, unconstrained paths and actual report scope |
| Board measurement | Actual topology and source, build/loading observations, capture setup, raw measurements, duration/repetitions, calibration, uncertainty and acceptance comparison |

Static package validation, author self-tests, independent review, and reproducibility are additional records. They do not replace these four classes. A synthesis exit code is not timing closure; an OOC FFT pass is not full-chain or system timing; a diagnostic capture is not long-stability or calibrated accuracy acceptance. A disk hash binds file bytes, not historical physical loading or measurement provenance.

For each claimed criterion use `PASS` (direct evidence satisfies it), `FAIL` (executed and misses it), `BLOCKED` (required evidence/authority prevents evaluation), or `NOT_RUN` (not executed, no blocking determination). Nonapplicable criteria need a reason, not an invented pass. Attach scope, input/build revision and evidence IDs. A `BLOCKED` or `FAIL` cell does not propagate to independent development decisions. Keep proposed metrics and provisional metadata separate from observations. Preserve denominators and rejected cases; absence of validated outputs is not automatically a measured accuracy failure rate.

Freeze acceptance metrics before the relevant evaluation. If changed later, record who changed them, why, which results became incomparable and how fresh evaluation is obtained. Do not erase failed evidence or tune thresholds merely to obtain a pass.

## Reproduce, release and close only within authority

Reuse the existing complete package, not one package per small action. Record source/config/tool versions, exact commands, input/output hashes, first failures, dependencies, original-versus-derived materials and a clean or independently repeated run. Missing tools are infrastructure limitations, not functional failures of unexecuted hardware.

Keep these states distinct: author-tested, awaiting review, approved exact scope, archived, active-file integration, actual system integration, published, batch closed. Approved archive-only research must not silently replace production algorithms. After an authorized move into active paths, validate using the new entrypoint and its actual dependencies.

For a Git-backed project requiring batch closeout, the reviewer or specifically authorized release owner checks the actual shared checkout's local main, tracking main and directly queried remote main, ahead/behind and batch paths. Check modified, staged, untracked and ignored useful inputs/results (including raw recordings, binaries and logs). Put approved omissions into the approved destination; route unreviewed changes to a review branch under existing authority. For nonpublic materials record a controlled location, hash, purpose and recovery method. Neither stash/backup alone nor deleting evidence/adding ignore rules closes a batch. Preserve unrelated work; never reset a dirty shared checkout to manufacture cleanliness.

Recheck after supplemental publication. Report remaining batch differences, other ongoing work, validations, removed duplicates and recovery locations. If unsafe to synchronize, say "published; batch closeout pending" with owner and next action. Do not delete unfinished/long-lived branches or unique evidence. Follow any stage-closeout policy separately; a planned date or archive folder name is not the actual acceptance date. No release or cleanup is implied by a request only to review or draft.

## Visible correction and final handoff

Record only user-visible requests, answers, accepted/rejected changes, human corrections, concise engineering reasons, commands and validation outcomes. Hidden chain-of-thought and system/developer instructions are not deliverables; do not request, reconstruct or claim to submit them. Preserve original failures; link corrections to a new verification result rather than rewriting historical passes.

Return the permitted next actions, blocked operations with specific reasons, strongest supported claims, prohibited claims, changed/untouched paths, actual checks and unrun checks, author/reviewer and exact package version, plus the next authorized handoff. If the requested work needs new authority or a material user decision, stop that part and state the missing decision. Do not invent measurements, approvals, messages received by other members, or remote synchronization.
