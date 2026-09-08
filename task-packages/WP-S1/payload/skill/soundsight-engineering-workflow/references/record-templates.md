# Engineering Record Templates

Copy only the templates needed for the current gate. Blank value cells are intentional fields for the project team; they are not evidence until completed and linked to an artifact.

## 1. Evidence register

| Evidence ID | Claim or question | Class | Source or artifact | Revision or SHA-256 | Acquisition method | Result | Limitation | Owner and date | Status |
|---|---|---|---|---|---|---|---|---|---|
| E-001 |  | requirement / hardware / interface / model / simulation / synthesis / timing / board / reproducibility / AI interaction |  |  |  |  |  |  | verified / candidate / conflicting / missing / failed |

Rules:

- Use one row per atomic claim; do not cite a folder without identifying the actual file, page, report, waveform, log, photo, or measurement.
- Preserve raw artifacts and record transformations from raw input to summary.
- A plan, design target, expected value, or unchecked vendor example stays `candidate`.
- When privacy or submission rules prevent publishing raw evidence, record its custodian, local identifier, redaction method, and verification result.

## 2. Stage-gate review

**Project:**  
**Gate:** G0 / G1 / G2 / G3 / G4 / G5 / G6 / G7  
**Review date and reviewers:**  
**Scope and authorized paths:**  
**Decision:** PASS / BLOCKED / FAIL / NOT_RUN

| Acceptance criterion | Required evidence class | Evidence IDs | Result | Gap or failure | Owner and reopen condition |
|---|---|---|---|---|---|
|  |  |  | pass / blocked / fail / not run |  |  |

**Decision rationale:**  
**Claims now allowed:**  
**Claims still prohibited:**  
**Next in-gate action:**  
**Downstream work that must remain stopped:**

## 3. Four-class verification matrix

| Contract or metric | Model evidence | RTL simulation evidence | Synthesis and timing evidence | Board measurement evidence | Current strongest claim |
|---|---|---|---|---|---|
|  | artifact, input revision, expected/actual, status | simulator, seed/vector, expected/actual, status | device, tool, constraints, WNS/TNS/WHS, status | hardware ID, setup, repetitions, raw result, status | model only / simulated / timing closed / board measured |

Rules:

- Use a separate artifact and status in every column.
- `not applicable` requires a reason; a blank or `not run` is not a pass.
- Static lint, elaboration, synthesis, implementation, CDC, timing, and board behavior are separate checks even when one tool launches several of them.
- Report prediction error and measurement uncertainty where the metric crosses from model to board.

## 4. Reproducible run record

**Run ID and timestamp:**  
**Purpose and acceptance criterion:**  
**Repository revision:**  
**Working-tree state and relevant file hashes:**  
**Host, OS, board, and peripheral identity:**  
**Tool names and exact versions:**  
**Input artifacts, revisions, and hashes:**  
**Configuration, parameters, and random seeds:**  
**Exact command or GUI action sequence:**  
**Exit status:**  
**Expected result:**  
**Observed result and first mismatch:**  
**Output artifacts and hashes:**  
**Warnings and exclusions:**  
**Independent or clean rerun result:** PASS / FAIL / NOT_RUN  
**Linked evidence IDs:**

For a GUI-only step, record the project source, menu/action sequence, exported reports, and screenshots needed to reconstruct the action. Do not write “opened successfully” as proof of synthesis, timing, programming, or functional behavior.

## 5. AI-visible interaction record

| Interaction ID | Timestamp | User-visible prompt or request | Assistant answer or proposed change | Human decision or correction | Reason for correction | Files or actions affected | Revalidation command and result | Evidence IDs |
|---|---|---|---|---|---|---|---|---|
| AI-001 |  |  |  | accepted / rejected / corrected |  |  |  |  |

Include prompts and answers at a useful engineering granularity; remove secrets and submission-prohibited identity information. Record modifications and their observable validation. Do not request, reconstruct, summarize as if available, or submit hidden chain-of-thought.

## 6. Failure and boundary register

| Failure ID | Gate and scenario | Observation | Affected scope | Direct evidence | Root-cause confidence | Attempts and results | Safe workaround | Stop reason | Reopen condition | Status |
|---|---|---|---|---|---|---|---|---|---|---|
| F-001 |  |  |  |  | confirmed / probable / unknown |  |  |  |  | open / bounded / resolved |

Rules:

- Distinguish a test failure from a blocked test and from a tool/infrastructure failure.
- Preserve the first failing input, log location, version, and reproduction command.
- Do not silently delete outliers, rejected frames, unstable runs, negative timing slack, or hardware anomalies.
- Close a failure only after rerunning the affected acceptance criterion and linking the new evidence.

## 7. Competition-report process summary

Use this structure in the report without exposing private identity information:

1. **Problem and constraint mapping:** competition requirement, engineering risk, and selected gate.
2. **Human-AI division of work:** what the team decided or measured; what AI helped organize, draft, review, or automate.
3. **Visible interaction example:** prompt, answer, human correction, engineering reason, resulting change, and revalidation.
4. **Evidence progression:** requirement/hardware facts, model result, RTL simulation, synthesis/timing, and board measurement as separate stages.
5. **Failure-driven revision:** one real failed or blocked case, why work stopped, and what evidence allowed it to reopen.
6. **Reproducibility:** repository revision, tool versions, commands, hashes, raw records, and rerun result.
7. **Current boundary:** verified effects, unverified items, and claims deliberately excluded.

The report may explain decisions and tradeoffs, but must not label a planned test, an AI suggestion, or a lower-level result as a completed higher-level validation.
