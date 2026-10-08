# FF-1.0 private forward segment contract

Implements the frozen `ARCHITECTURE-FF-1.0.md` input (SHA256
`63a37d5c31816a02a411ddd3047f0ea356275b59f5795feb8193612c1177b11c`).
One clk/posedge domain. `cold_rst_n=0` is shared cold initialization and gates
offers/readies; its legality requires external invalidation of all old physical
obligations. Cold mid-frame reset is **not** an approved runtime recovery.
No CDC/RDC, XDC, IRQ, register, DMA, firmware, board or service-clock interface
is introduced. Actual timing/resources/CDC/RDC remain UNVERIFIED.

## Admission and ownership

The public NP/fixed4 boundaries remain unchanged. New entry admission is exactly
`desc_valid && desc_ready` and the same NP descriptor ACK edge. The source tuple
is token64/generation64/context165/frame_first432, immutable through terminal and
abort consumption. All 16 required units exist from admission onward. The input
snapshot consumes 8192 **actual** NP FFT_INPUT handshakes in Gate ch0..3 then DOA
ch0..3 order, each index0..1023. Complete tuple, last, numeric_valid/overflow are
checked. No first-beat admission, Python spectrum or copied instance success.

The original 2002-bit NP normal report is checked for exact tuple/close_done,
8192 generated/qualified, zero cancellation/unqualified work, eight1024 output
counts, twelve OK units, 1024 requests/responses/terminals/qualified rows, research
qualification and no errors. The persistent 2080-bit NP abort is separately
accepted, stored raw and cancels numerical work. NP source errors preserve the
raw original records; cancellation is not a substitute for NP drain/close.
Configuration cannot start before a validated normal NP report was accepted.
NP's own close/binding release cannot cancel the subsequently detached snapshot.

## State machine, physical work and capacity

States `debug_state`: IDLE0, COLLECT1, WAIT_NP2, CONFIG3, FEED4, DRAIN5,
FFT_FINAL6, LEAF_BEGIN7, LEAF_RUN8, LEAF_SAVE9, LEAF_RETIRE10, NEXT11,
FINISH12, REPORT13. Predicates use pre-edge state and counters; no same-edge
replacement admission or saved-terminal/retire lookthrough.

Per frame, CONFIG accepts real `24'h0aaaab`; FEED supplies all1024 staged S29
complex samples through the official core handshake. RAM holds an offered sample
while core ready is low, including after logical cancellation. FFT data padding
is zero, real[28:0], imag[60:32]. Only output tuser[9:0] is used as index; upper
tuser fields are not interpreted. Full1024 natural-order output/index/last are
checked and physically consumed. Half0..512 is staged; later bins are checked
and discarded. Status8 is independently consumed; bit0 and event overflow are
numeric errors. Its timing may precede the last output. Only both accepted
full1024 outputs and accepted status discharge `ip_obligation` on a later edge.
The explicit output/status permits affect real core ready independently.

`CONFIG` itself is an outstanding config **offer**. Once entered, valid and the
fixed configuration remain offered through ready stalls and runtime cancellation.
Only actual config ACK advances to FEED. Cancellation cannot skip to FINISH
from CONFIG or retire this outstanding offer. `hardware_started`/`ip_obligation`
still describe an actual accepted config, not an offered one; prior to ACK the
CONFIG state and busy admission block retain ownership. After a cancelled offer
ACKs, the same actual staged1024 inputs, full1024 outputs and status drain.
No finite bound is claimed for an offer whose ready never arrives.

After full valid FFT closure, fixed4 begins with a nonzero locally allocated
monotonic64 context mapped back to the original full source tuple/instance.
Maximum context is fail-closed; no runtime wrap or alias is allowed. Inputs0..512
are the **actual** staged spectrum. The unchanged fixed4 leaf supplies RNE(/16)
S25F23 with component overflow flags and invalid `(0,0)` complex placeholders.
It has normal pipeline/stall behavior and physical cancel-edge history.

Fixed4 normal retirement requires actual `data_done`, no old output/input offer,
local quiescence, NP closed and real FFT obligation absent. Cancellation instead
requires the leaf's actual terminal snapshot, its saved ACK on a separate edge,
then true retire acceptance on a later edge. Historical sticky transaction
cancellation alone stops driving leaf cancel after the persistent leaf terminal
exists. A current reliable kill still drives leaf cancel even if cancelled/saved,
and prevents a retire request/acceptance on that edge. A held/repeated kill blocks
retirement until it releases; a new distinct cause additionally extends the
cause audit. Neither case creates another terminal or resamples its N/P/T.
`fixed4_retire_accepted` is derived from these real leaf predicates. No constant
retire_safe, runtime reset or synthetic done is used. The full raw cancel
snapshot is copied before retiring the leaf clears its own registers.

Logical additional data RAM is8192×58=475136bits plus513×58=29754bits, total504890.
This design uses combinational reads with handshake-held addresses; physical
RAM inference, mux depth, BRAM count, Fmax, expanded timing and engineering
integration are NOT_RUN. Identity/status/diagnostic registers add capacity.

## Cancellation, error and final states

`cancel_now` or actual backend clear handshake, NP abort, source/protocol faults
kill the transaction. Cancel E wins over a new qualified result or OK terminal.
Already final units remain historical. If configuration or leaf begin physically
ACK on E, their real obligation still exists and must drain/save/retire. In
particular all outstanding real FFT inputs continue unchanged after cancellation;
all1024 outputs and status are drained before reconfiguration. A lost status or
infinite downstream stall has no finite deadline and cannot be marked retired.

FFT numerical overflow: own FFT ERROR_NUMERIC, dependent fixed4 NOT_RUN_NUMERIC;
other independent instances may proceed. Fixed4 overflow: all513 physical beats
may finish, affected complex invalid zero, good neighbors unchanged, own fixed4
ERROR_NUMERIC. Original numeric and protocol flags/first fault survive cancel.
`m_qualified` is raw leaf numeric_valid plus current same-edge transaction
eligibility; a physical m_valid&&m_ready on E is not a qualified result.

`unit_state` has16 four-bit lanes, lane0 low: FFT Gate0..3, FFT DOA0..3,
fixed4 Gate0..3, fixed4 DOA0..3. Codes:0 PENDING,1 OK,2 CANCELLED,
3 ERROR_PROTOCOL,4 ERROR_NUMERIC,5 NOT_RUN_NUMERIC. Codes6..15 reserved.
Every unit has a final code at terminal. `hardware_started` uses the same16
indices and actual config/begin handshakes. `physically_retired` means there is
no physical obligation for that instance; a never-started canceled unit can have
retired1 while hardware_started0. It never means unrun hardware completed.

Local first error codes:0 NONE,1 SOURCE_ORDER,2 SOURCE_ID,3 SOURCE_NUMERIC,
4 NP_REPORT,5 NP_ABORT_ID,6 FFT_INDEX,7 FFT_LAST,8 FFT_STATUS,
9 FFT_EVENT,10 FFT_OVERFLOW,11 FIXED4_OVERFLOW,12 FIXED4_PROTOCOL,
13 CONTEXT_EXHAUSTED,14 FSM. First is sticky. Raw original NP codes are retained
in its original record rather than relabeled as these local codes. Fault code
priority for simultaneous local faults is source, NP report/abort, FFT, leaf.

Accumulated cancel reason bits:0 explicit cancel;1 reserved0;2 backend clear;
3 NP abort present;4 local protocol/qualification fault;5..7 reserved0, ORed
with the caller-supplied eight-bit `cancel_causes` when explicit cancel fires.
An FFT/fixed4 overflow alone is a numeric failure, not transaction cancellation.
The unchanged fixed4 leaf receives the manager's union of prior and **current-E**
causes, so its first cancellation snapshot includes the actual cause at E rather
than only the previous edge's accumulated register.
The first management ABORT cause field uses the **actual qualified E cause set**:
explicit supplied bits contribute only while cancel_now is true; clear, NP abort
and current local faults contribute their mapped bits. Idle external cause values
do not contribute. Later causes accumulate in separate frame/leaf audit fields;
they never rewrite this first immutable ABORT or its original counts/identity.

## Reporting and indexed fields

`terminal_valid` and all report fields are held until actual terminal_ready ACK.
`abort_valid/payload` has a separate held slot. Shared terminal_* identity is
stable until both slots are consumed and all physical obligations have closed.
There is no new descriptor on either ACK edge. Every declared field is a raw
integer/vector; no physical time, global success,53-instance result, fresh,
commit or take is claimed.

Eight-lane fields use instance0 low (Gate0..3, DOA0..3):

| Fields | Bits per lane | Meaning |
| --- | ---: | --- |
| fft_input_counts / fft_output_counts | 11 | Actual core data ACK counts |
| fixed4_input_counts / fixed4_output_counts | 10 | Physical leaf ACK counts, including E transfer |
| fixed4_qualified_counts | 10 | Numerically valid eligible outputs strictly before E |
| fft_status_raw / fft_status_seen | 8 / 1 | First actual status and accepted-status presence |
| fft_event_seen | 7 | OR of frame_started, unexpected_last, missing_last, status_halt, input_halt, output_halt, overflow |
| fixed4_contexts | 64 | Allocated unique nonzero context, zero if not begun |
| fixed4_cancel_causes_record | 35 | Initial saved leaf causes plus monotonic later cause audit; updated before actual retirement |
| fixed4_terminal_n_record / p_record | 10 | Original leaf strict-before-E generated/transferred counts |
| fixed4_cancelled_unsent_record | 10 | Original leaf cancellation conservation term |
| fixed4_terminal_t_bin_record | 10 | Original leaf E physical output bin |
| fixed4_terminal_t_record / s_record | 1 | Original E output/input physical transfer facts |
| fixed4_cancel_saved / retire_accepted | 1 | Actual manager terminal-save ACK / derived actual retire acceptance |

After initial leaf-save ACK, `fixed4_cancel_causes_record` continues ORing the
leaf's documented cause union and reliable current-E causes, including a kill
on a would-be retire edge. Its saved N/P/T/S/bin fields remain the immutable
first leaf snapshot. Before real retirement removes the leaf-local state, the
manager already holds any added causes. Saved=1 confirms the initial record
was copied; it does not freeze the separately accumulating cause audit or imply
retirement. Repeated same cause adds no bit; a held kill cannot retire; with no
current kill, historical cancellation alone permits the existing later retire.

`source_report_record/source_abort_record` retain the unmodified original NP
wire layouts; `source_*_seen` distinguishes presence from initialized zero.
`source_received` is physical NP stream count, not successful FFT work.
`fft_audit_valid` and `fft_audit_status` independently pulse one edge after real
output/status handshakes; both may pulse together. Data and status share instance,
with separate payload fields. `fft_audit_on_cancel` is the data transfer's
logical cancel qualification. Output payload remains original numerical bits.
Current source tuple is the shared full audit identity.

The180-bit abort payload is MSB-first:

| Field | Bits |
| --- | --- |
| Strict-before-E unit_state | 179:116 |
| hardware_started | 115:100 |
| physically_retired | 99:84 |
| source_received | 83:70 |
| current fft_in_n | 69:59 |
| current fft_out_n | 58:48 |
| current leaf_in_n | 47:38 |
| current leaf_out_n | 37:28 |
| current instance_id | 27:25 |
| first local error (or local fault at E if none earlier) | 24:17 |
| Actual reliable E cause set (qualified supplied bits plus mapped current causes) | 16:9 |
| E transfers: NP source, config, FFT input, FFT output, leaf input, leaf output | 8:3 |
| NP not yet closed / pre-E IP obligation / pre-E leaf active | 2:0 |

The abort snapshot deliberately does not pretend a config ACK at E existed
before E; actual E transfer flags resolve that ownership. Final terminal fields
contain the later drained counters, accumulated diagnostics and final states.

## Cycle budget and unverified evidence

NP's previously proved ideal interval is descriptorE0 through reportvisible
E18440/earliest reportACKE18441. This backend starts no configuration before that
ACK; its next pre-edge transition goes to CONFIG. No future source delay is
folded into FFT cost. For each logical FFT measure accepted config to
max(last full output ACK, accepted status, event closure), plus manager edges.
Feed and output/status overlap must not be double counted. Fixed4 ideal beginE0,
inputsE1..513, outputsE2..514, then separate data_done/retire observation edges.
Total is actual NP interval plus serial FFT/fixed4/manager intervals plus actual
finite stalls. Old7377-cycle FFT/reference intervals are not this segment's
measured cost or WCET. Watchdog is diagnostic stop only.

Writer did not create a reference/checker/TB or acceptance asset. Current native
simulation product generation initially failed in the restricted tool environment;
original first errors and automatic approval rejection are retained in the
author diagnostic root. Generated model readiness, compile/elaborate/simulate
results must be stated by the subsequent actual author run, never inferred here.
Official part/config discovery is confirmed; complete IP engineering admission,
OOC/STA/reopen, hardware reset minimum, physical clock and losslessness are
UNVERIFIED. Power NOT_APPLICABLE.
