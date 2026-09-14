# soundsight-engineering-workflow

This competition Skill turns an FPGA or embedded-system project plan into an evidence-gated engineering workflow. It is derived from SoundSight, but its gates and records apply to other projects that combine real hardware, models, RTL or firmware, tool implementation, measurements, and a reproducible competition handoff.

## When to use it

Use the Skill when a team needs to:

- decide whether hardware facts are sufficient to start interface-dependent implementation;
- keep model, RTL simulation, synthesis/timing, and board evidence from being conflated;
- review a milestone or recover from a failed experiment;
- assemble reproducible build/test records and user-visible AI collaboration for a report;
- state honest completion boundaries before submission or demonstration.

Do not use it as an algorithm tutorial, a board-specific pin guide, or permission to edit files outside the current request.

## Usage

Invoke `$soundsight-engineering-workflow` with the project path, requested outcome, allowed files/actions, current gate, and available evidence. Example:

```text
Use $soundsight-engineering-workflow to review whether this four-channel FPGA project may enter RTL implementation. Read the project roadmap and hardware audit, do not modify implementation files, and return the gate status, evidence IDs, blockers, allowed claims, and next in-gate action.
```

The Skill loads [the record templates](references/record-templates.md) only when records or a competition-report trace are needed.

## Failure and stop conditions

The workflow stops rather than guessing when physical hardware identity, electrical levels, clocks, pins, formats, synchronization, acceptance criteria, authority, or prerequisite evidence is missing or conflicting. An executed test that misses a criterion is `FAIL`; unavailable evidence or authority is `BLOCKED`; a test not attempted is `NOT_RUN`.

It also rejects these shortcuts:

- treating a roadmap, static document check, or generated report as functional proof;
- treating model success as RTL simulation success;
- treating synthesis success as timing closure;
- treating timing closure as board functionality;
- hiding failed samples, warnings, unconstrained paths, or human corrections;
- submitting hidden chain-of-thought instead of user-visible prompts, answers, reasons, changes, and validation results.

## Forward-tested effect

The first forward test applied the Skill to the repository's current SoundSight M0 evidence. It produced `BLOCKED` for G1 rather than allowing acquisition-dependent RTL or downstream acoustic RTL:

- verified project inputs: the physical board can be identified as the `ATK-DF7010P_7020P` series, baseboard revision `V3.9`, and Zynq `XC7Z020` device family; Vivado is fixed at `2025.2`;
- verified eligibility input: all three members have the same grade and education level and meet the junior-division condition;
- still missing for G1: full FPGA part and speed grade, PYNQ image and board support, DDR evidence, final pins and clocks, and the real four-channel acquisition device/interface/timing;
- resulting boundary: M0/G1 is not passed; these missing items cannot be presented as verified, and interface-dependent RTL remains stopped.

This is a workflow-behavior test against real project facts, not a hardware test. It does not prove SoundSight model accuracy, RTL behavior, timing closure, PYNQ operation, four-channel capture, or board performance.

## Failures and observations behind the Skill

The reusable parts were extracted from these concrete project observations rather than invented as a generic checklist:

- project roadmaps and design targets existed before matching model, simulation, timing, or board artifacts, which required the four evidence classes and the rule that a lower class cannot mark a higher class passed;
- the board family, baseboard revision, device family, and Vivado version could be identified while the speed grade, PYNQ support, DDR, pins, clocks, and acquisition timing remained unresolved, which required the G1 `BLOCKED` state and the downstream stop condition;
- an initial review confused the 28-page AMD selection guide with the separate 3-page competition FAQ, which required evidence records to identify the exact file, page, revision or hash, and to retain human correction plus revalidation;
- the first `quick_validate.py` attempt used a bundled Python without `PyYAML`, while the same validator passed under the recorded `C:\Python314\python.exe` environment, which required tool failures to be separated from Skill-content failures and exact runtime dependencies to be recorded.

These observations currently validate the workflow's evidence identification, stopping behavior, and correction trace. They are not evidence that the FPGA design itself has passed.

## Validation status and boundary

The Skill package has been checked with the system `quick_validate.py`, owned-path and internal-link checks, and the M0 forward scenario above. The validation proves package structure, internal-link integrity, and the intended blocked-gate behavior for that scenario. It does not prove that every future project will supply adequate evidence or that any FPGA design passes its gates.

The current SoundSight boundary is therefore explicit: documentation and workflow scaffolding are available, while full hardware/interface freeze and all model, RTL simulation, timing, and board-performance results remain dependent on their own evidence.

## How to describe its creation in the competition report

Report the process, not hidden reasoning: identify the original engineering risk, show the requirement-to-gate mapping, include one or two user-visible prompt/answer/correction/revalidation records, explain how the team converted project failures or missing evidence into stopping conditions, and show the forward test that correctly kept M0 blocked. Link the Skill revision and validation commands, then list the hardware items that were deliberately left unverified.
