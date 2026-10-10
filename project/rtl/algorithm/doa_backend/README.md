# Native continuous DOA backend candidate

This is new synthesizable B RTL, based on fixed B r2 mathematical sources in
`math-manifest.json`. It is not an accepted complete H3, a physical timing
measurement, production Tracker, TTL, or target identity selector. Author
diagnostics have at most DIAGNOSTIC_SMOKE status. Synthesis, resource use,
STA and hardware service bounds remain NOT_RUN/UNVERIFIED.

## Connection and ownership

`pcm4_doa_official_entry` is the authoritative public native consumer with
managed `ss_ifft25` actually instantiated through `ifft25_official`.
Its internal `pcm4_doa_native_entry` adapter reserves one buffer
and report lease from the first held fixed4 data offer, full terminal offer,
or source ABORT offer, in that priority order. This reservation is **not** an
A acquisition descriptor acceptance or successful delivery. No source ready
is asserted until the internal `pcm4_doa_backend` reservation has occurred.
Zero-output cancelled source frames can therefore still be accepted. No two
consumers may drive FF ready. A owns any diagnostic fanout/cache and the
common frontend/backend cancellation wiring; this module does not edit A.

Both domains are checked in fixed order Gate0..3 then DOA0..3, each bin0..512.
All accepted payloads include token64/generation64/context165/frame_first432,
domain/channel/bin, S25 complex payload, numeric validity, component overflow,
and same-edge qualification. Only DOA domain1 values feed the six pairs.
The gate-domain values are not used as a substitute DOA FFT/window.
`active_identity` is `{token,generation,context,frame_first}`, first item MSB.
It remains stable until all report/abort slots have been consumed and the IP
has physically retired. There is no new-frame acceptance on a release edge.

The external `gate_identity` and `gate_policy_id64` bind an explicit gate
observation to the reserved tuple. `gate_evidence_valid` is accepted only if
this identity equals the reserved tuple. There is no default gate true.
Missing/mismatched gate evidence still permits numerical diagnostics; it
prohibits eligible angle delivery. This is an input interface for the actual
gate owner, not a production activity policy implementation.

### Complete frontend record

Pack `s_terminal_data[6625:0]` by concatenating **all** these FF outputs in
this order (first MSB), exactly the `frontend_t` declaration in the core:

```
token, generation, context, frame_first,
unit_state, hardware_started, physically_retired,
fft_input_counts, fft_output_counts,
fixed4_input_counts, fixed4_output_counts, fixed4_qualified_counts,
fft_status_raw, fft_status_seen, fft_event_seen, fixed4_contexts,
fixed4_cancel_causes_record, fixed4_terminal_n_record,
fixed4_terminal_p_record, fixed4_cancelled_unsent_record,
fixed4_terminal_t_bin_record, fixed4_terminal_t_record,
fixed4_terminal_s_record, fixed4_cancel_saved, fixed4_retire_accepted,
source_received, transaction_cancelled, protocol_error, numeric_error,
first_error_code, accumulated_cancel_causes,
source_report_record, source_abort_record, source_report_seen, source_abort_seen
```

The upper725 bits are the original identity; the remaining5901 bits are raw
audit, not reconstructed summaries. ACK means the entire record has actually
been retained in `frontend_terminal_record`. Numerical work starts only after
this barrier checks4104 accepted valid ordered values, the full tuple,
all16 unit states OK, all16 hardware starts/physical closures,
all8 statuses seen/zero, all8 input/output counts1024, all8 fixed4
input/output/qualified counts513, source8192 and original source report
present/non-aborted, plus no protocol/numeric/first error or source ABORT.
The raw NP report/abort and all per-bin/cause/history fields remain exposed
without reinterpretation; their original upstream qualification is not
replaced by a new downstream decoder.

`s_abort_identity` is the same725-bit tuple and `s_abort_data` is the actual
180-bit immutable frontend ABORT payload. It has its own physical held-slot
ACK and retained `frontend_abort_*` fields. A reliable offered ABORT for the
active tuple suppresses qualification immediately, before its slot ACK.
Cancelled frontend short output is not relabeled as SOURCE_ORDER.

M's current PR47 connection decision (SHADOW-TEMP-001) also requires an
actual foreign ABORT ACK (`s_abort_valid && s_abort_ready` with a mismatched
full identity) to suppress `angle_delivery_eligible` on that same E edge.
A physical diagnostic report ACK may still occur with eligibility0. The actual
foreign identity and180-bit payload are retained; an empty first-error slot
records ERR_ID, while an existing first error remains unchanged. This foreign
ACK alone creates no reliable cancellation or cancellation cause. An unaccepted
foreign offer or idle offer creates no such ACK; the native adapter's idle
reservation behavior is unchanged. Earlier accepted history remains intact,
and any started official IP obligation continues to drain physically.

## Mathematical chain

Serial pairs:01,02,03,12,13,23. Square-array baseline deltas respectively
(1,0),(1,1),(0,1),(0,1),(-1,1),(-1,0); edge40mm, sample48kHz,
sound speed343m/s. Cross is `Xi*conj(Xj)`, S51 F46, no saturation.
Band7..85, nonzero and `2500*square>=max(square_band)`, at least12 bins.
The original epsilon cannot exclude a nonzero integral cross code.
Magnitude is exact RNE sqrt of `square<<48`; reciprocal uses the frozen
256-entry F30 ROM and two exact RNE Newton refinements. Normalization emits
S25 F23 or rejects the pair on overflow; no saturating repair. All arithmetic
intermediates use explicitly wide integral math. There is no real arithmetic,
transcendental runtime table generator or `$sqrt`.

DC/Nyquist PHAT imaginary components are zero by the fixed band. Negative
frequencies are protected conjugate copies; interior most-negative imaginary
codes reject before conjugation. Official IFFT input/output real/imag25 codes
occupy bits24:0/56:32 in a64-bit beat; padding is zero. Configuration24'h0AAAAA
means inverse1024, natural order, ten /2 stages. No extra /1024 is applied.
Status8 and natural index/TLAST are independently checked. The numerical core
exposes an official IP interface; the authoritative entry actually connects
it to the managed core. No approximate/custom FFT model is included.
`official_events` is a live raw7-bit observation in the same order as forward
events (frame_started bit0, unexpected_last1, missing_last2, status_halt3,
input_halt4, output_halt5, overflow6); it is not a done ACK.

Lag scan: increasing[-6,6] for edges and[-8,8] for diagonals, most-negative
tie winner. Parabolic delta is symmetric RNE, clamped ±2048 Q12. Physical
limits22928/32425 Q12 are inclusive. Separated peak margin is reported in
signed64 Q15, and is not an extra acceptance threshold. Six signed32 Q12
taus, signed25 peaks and margins use lane0 low.

LS uses at least3 valid pairs, positive determinant, exact integer RNE Q20
vector solution and predicted Q12 residual. Residual square must be at most
`n*2048^2`; norm square lies inclusively in104858²..1363149². Independent
normalized CORDIC accepts S23 Q20 vectors, normalizes both with
`shift=24-bit_length(maxabs)`, runs24 iterations with frozen Q16-degree atan
steps, and produces canonical signed S18 F8 degrees[-180,180). Zero vector
and S23 vector overflow reject. +x is0°, +y +90°; positive angle is toward+y.
Mic coordinates(0,0),(1,0),(1,1),(0,1); physical orientation remains A/C's fact.

## Reports and invalid reasons

`report_valid && report_ready` accepts retained diagnostics, not an automatic
servo command. A successful angle use additionally requires
`angle_delivery_eligible`, which includes explicit gate qualification, no
numeric/protocol error and no current or historical cancellation. It does not
claim fresh/commit/take, true-time expiry, physical source identity or confidence
threshold certification. Already computed numerical facts are not overwritten
by a later cancel; live delivery qualification is revoked separately.

`backend_stage_state` has21 four-bit lanes (lane0 low): PHAT0..5,
IFFT0..5, lag0..5, LS, normalized CORDIC, external qualification.
Codes0 pending,1 OK,2 algorithm rejected,3 numeric invalid,4 protocol error,
5 cancelled,6 skipped. Every required instance closes in the retained report;
unexecuted hardware never appears as completed. `pair_state` is six aggregate
four-bit lanes, with the same reasons. `pair_valid` means legal lag, not that
the frame has a deliverable direction. Previously final states remain final
when cancellation closes remaining instances. `direction_reason`:0 valid,
1 insufficient pairs,2 rank deficient,3 residual rejected,4 norm rejected,
5 frontend not usable,6 cancelled,7 numerical/protocol failure. Exact first
error8-bit codes:1 identity,2 source order/count,3 source numeric/qualification,
4 frontend qualification,5 PHAT overflow/conjugate,6 IFFT index,7 IFFT TLAST,
8 IFFT status,9 IFFT event,10 CORDIC input. First error is sticky and raw
upstream errors remain in the original record.

`pair_hardware_started` records actual IFFT configuration ACK, not a planned
call. `pair_physically_retired` means no IP obligation, including never-started
rejected/cancelled pairs; it does not mean six cores ran. Input/output counts
are actual handshakes (six11-bit lanes), status is six8-bit lanes and seen bits.
Numeric precomputation is not a hardware completion or visible true-time fact.

## Cancellation, STOP and physical closure

One common `clk` and synchronous active-low `cold_rst_n` initialize the whole
composition. Cold reset is not runtime cancellation. No CDC/CSR/IRQ/DMA is
introduced. A must share the cold invalidation domain with the official core.

Reliable cancel/STOP is qualified by the full active tuple; unrelated causes
at idle cannot enter audit. Current E cancellation wins normal result eligibility,
result ACK and semantic finalization. `frontend_cancel_request` forwards only
the scoped external cancel/STOP request, not a loopback of source ABORT.
During collection, cancelled transactions still receive real pending frontend
data and full records; no physical-closure deadlock is caused by revoking ready.

Kill before an offered configuration runs no IP. Once configuration is offered,
valid remains stable until actual ACK even if cancellation arrives. Any actual
ACK (including E) creates a drain obligation: accept all1024 staged input beats,
all1024 actual outputs and the actual status before retirement. No runtime
reset, forced done, fabricated status, future-reader shortcut or fake hardware
closure is used. Missing status/ready preserves the obligation; no unmeasured
watchdog/service budget is invented. New/held kill suppresses successful
publication, but historical cancellation permits later physical draining.

`abort_valid` is an independent held first-cancel slot. `first_cancel_causes`
bits0 scoped cancel,1 STOP,2 frontend ABORT, OR actual supplied cause bits only
for qualified external requests. The first immutable record includes prior
stage/pair finals, hardware start/retire, counts and statuses; `abort_ip_transfers`
bits0 config/1 input/2 output/3 status record actual E handshakes separately.
`accumulated_cancel_causes` is monotonic late audit and cannot rewrite this
first snapshot. Both report/abort slots must be consumed before reuse.

## Cost and bounds

Single buffered frame; serial six pairs, one official core. PHAT/CORDIC/LS are
real RTL. Wide combinational integral sqrt/divider is an initial synthesizable
implementation choice; arithmetic depth/area/timing are UNVERIFIED. This is
not a claim of48kHz continuous service, WCET or resource fit. Numerical work
uses bounded state loops; official handshakes can stall indefinitely. A owns
admission buffering and any measured throughput policy. Synthesis and timing
closure need their separately authorized evidence before a hardware claim.

## Official simulation product entry

`official-ip.json` binds the exact historical S25 XCI SHA256
`0cc3549721df23822ab01071e1dbf4b8fc89b1bb43bae13cd6fe283db828d6d6`.
`generate_simulation.tcl` recreates its component settings under unique
`ss_ifft25`; no legacy XCI output path is imported. The known simulation
target is `xc7z020clg400-2`, metadata100MHz, Vivado2025.2, xfft9.1 revision15.
This target/metadata is not evidence of a current board clock or hardware fit.

From an initialized vendor command environment:

```
vivado -mode batch -source project/rtl/algorithm/doa_backend/generate_simulation.tcl -tclargs <new-exclusive-simulation-output-directory>
```

The recipe refuses existing output, checks exact tool/core revision, creates
the required child `ip` directory, generates simulation only, and exports
XSim compile products. It does not synthesize, launch OOC runs, implement,
download hardware or change global library mappings. Compile the generated
`ip/ss_ifft25/sim/ss_ifft25.vhd` with its official libraries from exported
`export/ss_ifft25/xsim/` before `SOURCES.txt`. Actual generated products and
native compile/elaborate/simulate evidence remain separately recorded;
the existence of this recipe is not execution or acceptance evidence.
