# Forward FFT29 and fixed4 private composition

FF-1.0, fixed parent `c9273ebc70d8ddeb283e0903e5aee46102dc7638`.
Primary writer mode IP_INTEGRATION. Research numerical segment only: real NP
inputs to one official AMD forward FFT, eight logical frames, then unchanged
fixed4. This is not a production profile, hardware admission, full H3 result,
real clock service bound, fresh/commit/take implementation or acceptance.

## Unique entry and dependencies

`pcm4_forward_fft_entry` is the composition entry. Connect its descriptor,
reader and caller-side ports to the existing real caller/consumer. It instantiates
the authoritative unchanged NP and couples its real descriptor ACK to backend
source admission. `desc_ready` gates both; the next descriptor cannot enter
until the prior backend, report and abort slots are retired. NP's error-code
input is named `caller_first_error_code` on this new entry to distinguish the
backend's `first_error_code` output. Old NP/fixed4 ports and semantics do not change.

`HANN_FILE` must identify the original frozen NP Hann bytes; see the original
table manifest. `research_profile_valid` is mandatory evidence qualification,
not a default parameter. No new window, input shift or numerical model is added.
The private manager can also connect to a separately instantiated **real** NP,
provided `source_begin_valid/ready` is exactly coupled to its descriptor ACK.

Use `SOURCES.txt` with the original caller dependencies and the official FFT
generated sources/libraries. No stub or Python-computed spectrum is acceptable.
`official-ip.json` retains every original component/model parameter, exact XCI
source identity, part, version/revision and runtime packing. Its source XCI is
an immutable reference; do not import its historical relative generation path.

From an initialized Vivado **2025.2** vendor environment:

```
vivado -mode batch -source project/rtl/algorithm/fft_forward/generate_simulation.tcl -tclargs <NEW_ABSOLUTE_DIAGNOSTIC_OUTPUT>
```

The recipe rejects existing outputs, any other version/revision, creates an
in-memory simulation configuration for confirmed `xc7z020clg400-2`, generates
only simulation targets and exports XSim compile scripts. No OOC, implementation,
STA, constraints, formal project import or upgrade is invoked. The fixed part
belongs to the historical numerical simulation configuration, not board identity.
Compare generated component/model parameters with `official-ip.json` before
simulation. Bind generated native sources/libraries and current tool model bytes.
Old portable Q30 golden and old AMD model DLL are not current RTL equivalence.

## Cancellation and output consumption

`cancel_now/cancel_causes` is an explicit backend-scoped same-clock cancellation.
The entry forwards `cancel_now` to NP's local cancellation as well. Caller
close-induced `!new_work_allowed` or binding release does **not** cancel a
detached backend snapshot. External integration must convey an independent
cancel to `cancel_now` during this phase. `controlled_clear_valid/ready` is the
backend's private clear handshake; old NP `data_clear_req_*` remains separate.
Neither is a RAM/cold reset shortcut.

`fft_output_permit` and `fft_status_permit` reserve the integrator's capacity
for a real FFT output/status transfer. They drive the actual official ready
ports independently. With permit low the official output/status must stall.
The half-spectrum RAM inherently reserves all 513 entries before feeding FFT;
back-half outputs are checked and discarded, not held waiting for fixed4. Full
FFT audit pulses are registered physical handshake observations one edge later,
so an external audit collector must account for this pipeline reservation.
These permits are explicit inputs; the module creates no default sink capacity.
`m_ready` independently stalls the unchanged fixed4 output register.

`m_valid` and raw payload/flags are physical leaf offers, including a possible
same-edge cancel transfer. `m_qualified` distinguishes numerical eligibility;
on cancel E it is false even if the old valid/ready physically transfer.
An overflowing complex is `(0,0)`, numeric_valid false, with separate real/imag
flags. Legal neighboring bins retain their numerical payload. An instance with
any overflow is ERROR_NUMERIC; its physical transfers are not an all-OK result.

All report fields hold while `terminal_valid` is stalled. `abort_payload` is a
separate immutable first-E snapshot, held while `abort_valid` is stalled. Both
must be ACKed before new admission. Original NP report and abort records remain
unaltered. Runtime cancellation cannot reset the FFT away: after an accepted
configuration, the real remaining staged inputs are sent and all 1024 outputs
and one independently accepted status must drain before reuse. Missing status
or infinite backpressure is unbounded isolation, not a fabricated retirement.

## Evidence boundary

See `FORWARD-CONTRACT.md` for lane order, terminal states, packing, error codes,
cycle/storage budget and actual physical retirement prerequisites. Native author
evidence is held only in the dispatched diagnostic root. Generation, compile,
elaboration, simulation, physical timing and hardware acceptance are distinct
facts; source existence or a recipe does not prove execution. Writer/author
checks are DIAGNOSTIC_SMOKE and require subsequent independent verification.
