# Human checkpoints, ILA evidence, and incremental integration

## Readiness and choices

Codex handles authorized engineering implementation and focused self-tests. Add short Chinese purpose comments to new or materially changed project-owned blocks; do not annotate every line or edit generated vendor outputs. State feasible options, meaningful pros/cons, and a recommendation for consequential architecture, interface, precision, clock, IP/device/version or resource decisions, then wait for the human's choice only on the dependent path. Previously chosen unchanged decisions and routine equivalent fixes do not need renewed approval.

Match pre-handoff checks to the next operation, reusing exact-candidate evidence:

- Simulation: actual compile/elaboration and focused known-input or boundary self-test when the tool is available. State what remains untested.
- Synthesis/implementation: confirm source/top, part, tool/IP, constraints and the requested run. Read existing relevant reports. An early function inspection does not require full P&R.
- Programming/board: bind bit plus HWH/XSA/ELF where applicable, and LTX when ILA is used, to the exact implemented candidate; preserve applicable electrical, clock/reset/CDC/STA, memory and stop/recovery prerequisites.

If only static inspection was possible, report compile/simulation/build NOT RUN and give the shortest human command or GUI steps; never claim the code is verified usable. Handoff is distinct from functional acceptance. The human may open a trusted existing matching run instead of rebuilding for participation.

At each useful checkpoint give: candidate/project/run; actual checks and limitations; short operation steps; useful screenshot targets; raw log/wave/report/sample export paths; expected behavior and next action. Codex analyzes the originals and reports expected -> observed -> evidence -> next step. Screenshots illustrate rather than prove an unobserved property.

## Use ILA when it answers a concrete board question

Use ILA for an actual observed internal/interface property such as channel mapping, accepted samples, valid/ready behavior, frame boundaries, reset recovery, or peripheral command sequencing. Do not add ILA by default to every task. First decide the property, known stimulus, expected relation and necessary observation window; choose the existing correct capture clock, minimal probes, trigger and depth. Do not invent probe names, frequencies or depth values. Unsafe/cross-domain sampling does not prove CDC correctness.

Explain correct and incorrect traces briefly before the human runs:

- AXI-Stream example, only where the contract specifies it: transfer occurs at the active sampling edge with valid && ready. During a stall, the unaccepted beat and sidebands remain stable under the protocol. Count accepted beats, not valid cycles; last belongs to the specified final accepted beat. A changing stalled beat, missing/extra accepted beat, or misplaced last is a concrete failure.
- Frame/sample example, only after confirming the project contract: channel/order, sample-enable and accepted sequence agree with a known input; frame markers occur at the required accepted sample boundary. Required latency comes from the approved contract, not from adapting expectations to the trace.
- Reset example: outputs/state follow the approved reset and restart contract. A short clean capture does not prove every reset phase or long-run condition.

These are examples, not universal signal requirements. Give actual signal names and numerical expectations from the current design/contract, or label them unknown. A trace of data toggling alone does not prove arithmetic accuracy or acoustic performance. For numeric behavior compare raw samples with independent known results and defined tolerance.

Bind raw CSV/WDB or tool-native exports, sampling clock, probes/trigger/depth, input identity and capture duration to bit/LTX plus other relevant artifacts. If only a screenshot is available, explain the limited observation; request the minimal useful export rather than signing unobserved properties. Wrong/missing bit-LTX binding, an inaccessible raw capture, unexercised trigger or missing known stimulus cannot establish board functional acceptance.

ILA changes implementation resources/timing and creates a new candidate. Use that candidate's reports; an old uninstrumented timing result is not automatically applicable. Removed probes also create a changed implemented candidate, requiring affected evidence and bindings to be refreshed.

## Scoped acceptance and immediate integration

The three evidence profiles remain unchanged. Use SPECIALIST_ACCEPTANCE with local BOARD_FUNCTIONAL for an actual bounded board-behavior claim; BOARD_PREP means preparation only. The task-contract schema accepts the added stage. Board evidence can directly establish an observed contract property within its stimulus/window; it does not bypass required simulation evidence when simulation acceptance is itself requested.

Codex may report the exact observed scope after comparing the capture with independent expectations. A qualified non-author member or valid designated AI accepts the same exact candidate; the author of changed test/checker assets cannot independently sign their own contribution. One review can cover technical final review and member acceptance when its identity and responsibilities are explicit. Preserve remaining NOT RUN/UNVERIFIED and original system requirements.

After the agreed local criterion is met and necessary acceptance and engineering authority are in place, connect the accepted module to the overall project without another generic coordination gate. Add the authoritative source/IP/XDC and intended connections only once, record the combined version, and check actual interface, clock/reset, address/driver and resource/timing effects. Reuse unchanged valid evidence and run only affected combination checks. Human download/board operations still remain human actions. A module or diagnostic integration is not complete system acceptance, and unrelated presentation/documentation does not delay a justified integration.
