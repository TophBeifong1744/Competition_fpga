# NP-1.0 private numerical and cycle contract

Frozen design input: `F:/NUEC/codex_out/i17-numeric-preprocess-product-20261007/ARCHITECTURE-NP-1.0.md`, SHA256 `974400be40c5f547cb0d056a45e31cc9ace37162121bc8f922c9568b12455764`. Baseline `758cfc47e4b26d24ac9e88da3f30587d220c54bd`. This implementation documents that approved internal contract; it is pending independent validation and is not a public ABI, acceptance or production profile.

## Interface and acceptance edges

One `clk`, all new sequential state on posedge. `cold_rst_n=0` gates every valid/ready; synchronous cold initialization needs an edge and externally invalidates ALL old reader, downstream and callback obligations. That external condition is UNVERIFIED. Ordinary runtime recovery uses the controlled cancellation/drain/close path, never slice reset or cold reset to hide pending reads. The new module must share the caller's cold reset, not `slice_rst_n`.

Descriptor/read/response/close ports have the exact caller names, widths and meanings. Connect the caller's `binding_valid`, `bound_token`, `bound_generation`, `current_context`, `new_work_allowed`, `local_cancel_now`, `pending_cancel`, `first_error_valid/code`. Keep the existing caller/consumer authoritative; do not add a second storage leaf. `research_profile_valid` is an explicit synchronous assertion by the integrator that this fixed research configuration/table identity is bound; no default production configuration is created.

All input tuples hold during stall. Descriptor ACK freezes token64/generation64/context165/first432 and creates a real lease. It may accept a canceled historical descriptor to discharge ownership, but creates an immediate abort and sends no numerical read. The first normal request is on a later edge. There is one actually accepted read pending; the next request cannot fire on its response ACK edge. Every response is physically ACKed/audited while a transaction is active. Only an exact pending token/generation/context/index echo ends that accepted request; wrong echo is drained physically but cannot prove its termination, so the lease remains until a real matching terminal response arrives. Matching non-OK/LOCAL_STALE responses do terminate the request, while rejecting numerical qualification. No invented terminal evidence, timeout or constant close is used.

Normal response qualification additionally requires origin B=0 and status READ_OK=0, raw index, sid/frame/interval/first/last/reset-before equal to descriptor, correct ID first+index using 65-bit nonwrapping arithmetic, last only at1023, and all four S32 lanes sign-extended from S24. Raw flags do not choose clipping policy and are not turned into numerical statuses. Only a qualified response writes one 96-bit PCM row and all four exact sums. Bad raw response and full echo are retained separately from cancellation and the first local/caller errors.

FFT_INPUT carries `fft_domain` (0 Gate, 1 DOA), `fft_channel[1:0]`, `fft_index[9:0]`, signed29 `fft_real/imag`, numeric_valid/overflow/last and original token/generation/context/frame_first. Order is Gate ch0..3, then DOA ch0..3, each index0..1023, total8192. Imaginary is0; last is index1023 for each instance. `fft_frame_first` has original raw descriptor bits, so sample ID reconstructs as frame_first[129:66]+index only after the actual read was checked. No FFT spectrum, 53-item success, time, fresh, commit or take is produced.

The single registered FFT_INPUT item and complete sidebands are stable under ordinary stall. No lookthrough: ACK removes the old item and synchronously prefetches the next PCM/coefficient; a later CALCULATE edge produces the next valid item. Legal exact inputs produce numeric_valid=1/overflow=0. Internal coefficient/range failure aborts the transaction before emitting that affected item, retaining original fault operands/value and numerical error. It never silently emits an overflowing value as normal.

## Arithmetic and table

Input x is signed24. Four sums are exact signed34; means are signed24 RNE(sum/1024). Gate center is signed25 x-mean; multiply by U18F17 h, then RNE(/2^17) checked signed25. DOA multiplies ORIGINAL signed24 x by h, then RNE(/2^17), saturates signed24 and detects overflow; a detected internal range error aborts numerical qualification. Gate is never clamped toS24. Both domains then shift left4 exactly to signed29, imaginary0.

Multiplication uses a signed44 result (wider than the conservative S43 bound). RNE uses an extra signed45/unsigned45 magnitude, quotient and remainder: increment for remainder>half or tie with odd quotient, then restore sign. No negative add-half arithmetic shift and no early truncation. Mean has k10; windows k17. All range tests precede narrowing; legal PCM and frozen h in0..131072 fit. Physical implementation/expanded depth/Fmax are unmeasured.

The actual ROM is `hann-u18f17.mem`, 1024 five-digit lowercase hexadecimal lines, LF and no BOM, sample index in ascending line order. Bytes6144, SHA256 `487c7f988ab00fc0428dc3fbe1705e933eac96ef4f54519727bf9fb0d11dc1bf`. It decodes exactly to original4096B U32LE SHA256 `51a05f855181f1774c3373c83085fd5a2792f5db932d66b1f3dc768e8ec6a2f2`. `HANN_FILE` selects a path to these SAME frozen bytes; verify byte identity before compile/run. No runtime cosine. ROM defaults to illegal18'h3ffff before readmemh; missing/short/unknown/out-of-range consumed words fail closed with COEFFICIENT. An in-range substituted table is an input identity violation detected by integration hash preflight, not a claimed hardware SHA engine. Vendor file-load failure may also stop compilation/simulation; preserve that real error.

## Local statuses and counts

Twelve 3-bit lanes in `unit_status`: lane0..3 mean_0..3; lane4..7 gate_window_0..3; lane8..11 doa_window_0..3. Low bits hold lane0. Codes0 PENDING,1 OK,2 ABORTED,3 ERROR; 4..7 reserved. A mean becomes OK only when actually locked. A window becomes OK only after1024 qualified output ACKs. Same-edge abort wins over a new OK; previously completed OKs remain history. The final report marks unfinished units ABORTED, or the offending numerical instance ERROR. `abort_units` is the complete12-bit unfinished-at-E set, bit per status lane; an independent transaction abort terminates this set instead of fabricating hardware done.

Four mean lanes in `mean_s24` are packed little lane order, each24 bits, lane0 low. Eight `output_counts` lanes are11 bits, lane0 low: Gate0..3 then DOA0..3. These counts include qualified strict-before-abort output ACKs only. They cannot exceed1024. `qualified_rows` counts real validated/stored responses, not requests. `read_requests/read_responses/read_terminals` count actual request ACK, physical response ACK, and exact pending response-echo termination respectively. Request count<=1024; response/terminal32-bit counters saturate rather than wrap and retain COUNTER error.

G=`generated`, P=`qualified`, T=`transferred_on_abort`; G includes registered generated FFT items, P counts qualified transfers strictly before E, T counts an old output's physical transfer on E (0 or1). Cancellation conservation: unsent_cancelled=G-P-T, not_generated=8192-G; all nonnegative. Normal terminal report has G=P=8192, T=0, unsent_cancelled=not_generated=0. Pending or ungenerated work is never success.

## Cancellation, controlled clear and lease

Reliable same-clock E observes local/pending caller cancellation, caller error, loss of new-work eligibility before own close, changed binding, missing research qualification, controlled clear or internal protocol/numeric error. `data_clear_req_ready` is asserted only for an active transaction that has not yet aborted. The actual clear handshake first freezes identity, original obligations and abort; cache validity is retired only through drain/close/report, and physical RAM is not cleared. In idle or already canceled state this request is backpressured; it is not a second cold-reset interface.

On E, old valid&&ready output may physically TRANSFER_ON_ABORT; T increases, P/status do not. Old stalled output is withdrawn afterE and the independent abort terminates it without waiting for fft_ready. Any accepted request onE still becomes pending and must really drain. Response ACK onE is DISCARDED_ON_ABORT, never added to sums/cache; exact echo may end the actual pending request. Later ready cannot revive the tuple/generation. Ordinary FFT receivers without this persistent same-clock cancellation contract are not approved integrations.

`abort_valid/payload` freezes once atE and holds through its independent ready stall; ACK does not permit new work or discard caller lease/pending reads. Normal lease lasts through all8192 output ACKs. Cancellation drains every actual pending request first. Both paths enter QUIET, then CLOSE; no request or FFT item exists there. `reader_no_future_access` is true only with real CLOSE valid and derived terminal conditions, never constant1. Matching actual close ACK is necessary before report. Close is reader closure, not completed caller storage retirement/audit/save. Own close-induced !new_work_allowed is ignored in CLOSE/after close, preventing feedback self-cancellation; independent local/pending/caller errors still apply until report freezes. No normal numerical work or request can resume after abort or close.

Protocol/numeric flags accumulate observed local categories; `error_code` preserves first LOCAL cause. `caller_error_valid/code` preserves the first original caller cause independently. Non-OK response audits describe failure of normal numerical qualification; they are not an independent DUT acceptance verdict. Newly observed late diagnostics/counters are locked before report creation. Once visible, report and abort payloads are immutable. Each has its own ACK and both slots must be empty before a new descriptor; no same-edge replacement. Cold global invalidation remains external/UNVERIFIED.

Cancel reason mask: bit0 local_cancel_now; bit1 pending_cancel; bit2 first_error_valid; bit3 !new_work_allowed before own close; bit4 actual data_clear handshake; bit5 missing research_profile_valid; bit6 local protocol fault; bit7 local numerical fault. Final report accumulates later reasons; abort retains the initial E reason set. Status/error preservation does not relabel a physical output history or ACK as qualification.

Local error codes (decimal): 0 NONE;1 PROFILE;2 DESC_TUPLE;3 DESC_RAW;4 UNREQUESTED_RSP;5 RSP_TUPLE;6 RSP_STATUS (origin/status fails normal qualification);7 ROW_IDENTITY;8 ROW_ID_RANGE;9 ROW_LAST;10 PCM_EXTENSION;11 COEFFICIENT;12 MEAN_RANGE;13 GATE_RANGE;14 DOA_RANGE;15 BINDING;16 FSM;17 COUNTER. Wrong/reserved FSM states fail closed to drain and retain error. No production timeout is invented for stalled close or missing terminal response.

`first_fault_value` is signed44 mean rounding result for MEAN_RANGE, exact multiply result for COEFFICIENT, window rounding result for window range errors. The sample/domain/channel/index and raw PCM/coefficient accompany it. For protocol errors these arithmetic metadata fields are incidental diagnostics, not claimed relevant offending arithmetic; bad response full tuple/payload and frame_first are the authoritative raw identity evidence. A descriptor error canonicalizes arithmetic metadata to0 except its mic0 PCM. Fields associated with incomplete statuses are not valid numerical results.

## Persistent report wire layout

`report_payload[2001:0]` is packed MSB-first in the following order. Numeric payload signs are explicit above; other IDs/counters remain unsigned raw integers.

| Field | Bits | Width |
| --- | --- | --- |
| `token` | 2001:1938 | 64 |
| `generation` | 1937:1874 | 64 |
| `context_tag` | 1873:1709 | 165 |
| `frame_first` | 1708:1277 | 432 |
| `unit_status` | 1276:1241 | 36 |
| `mean_s24` | 1240:1145 | 96 |
| `output_counts` | 1144:1057 | 88 |
| `read_requests` | 1056:1025 | 32 |
| `read_responses` | 1024:993 | 32 |
| `read_terminals` | 992:961 | 32 |
| `qualified_rows` | 960:950 | 11 |
| `generated` | 949:936 | 14 |
| `qualified` | 935:922 | 14 |
| `transferred_on_abort` | 921:908 | 14 |
| `unsent_cancelled` | 907:894 | 14 |
| `not_generated` | 893:880 | 14 |
| `aborted` | 879:879 | 1 |
| `close_done` | 878:878 | 1 |
| `protocol_error` | 877:877 | 1 |
| `numeric_error` | 876:876 | 1 |
| `profile_valid` | 875:875 | 1 |
| `cancel_reasons` | 874:867 | 8 |
| `error_code` | 866:859 | 8 |
| `caller_error_valid` | 858:858 | 1 |
| `caller_error_code` | 857:850 | 8 |
| `abort_units` | 849:838 | 12 |
| `first_fault_value` | 837:794 | 44 |
| `first_fault_domain` | 793:793 | 1 |
| `first_fault_channel` | 792:791 | 2 |
| `first_fault_index` | 790:781 | 10 |
| `first_fault_pcm` | 780:757 | 24 |
| `first_fault_coefficient` | 756:739 | 18 |
| `bad_rsp_valid` | 738:738 | 1 |
| `bad_rsp_token` | 737:674 | 64 |
| `bad_rsp_generation` | 673:610 | 64 |
| `bad_rsp_context` | 609:445 | 165 |
| `bad_rsp_index` | 444:435 | 10 |
| `bad_rsp_status` | 434:433 | 2 |
| `bad_rsp_origin` | 432:432 | 1 |
| `bad_rsp_payload` | 431:0 | 432 |

## Persistent abort wire layout

`abort_payload[2079:78]` is the2002-bit report layout above, shifted up78 bits. It snapshots strict-before-E statuses/means/counts, plus actual E read/response/terminal counters and T, first cause, complete abort set and original identity. This abort snapshot is independent of the later report's drained counters/final statuses. `close_done` is usually0 and never predicts a future close; a late abort after a real close can retain1. The low78-bit suffix is:

| Field | Bits | Width |
| --- | --- | --- |
| `held_valid` | 77:77 | 1 |
| `held_domain` | 76:76 | 1 |
| `held_channel` | 75:74 | 2 |
| `held_index` | 73:64 | 10 |
| `held_real` | 63:35 | 29 |
| `held_imag` | 34:6 | 29 |
| `held_numeric_valid` | 5:5 | 1 |
| `held_overflow` | 4:4 | 1 |
| `held_last` | 3:3 | 1 |
| `response_on_abort` | 2:2 | 1 |
| `read_on_abort` | 1:1 | 1 |
| `pending_after_edge` | 0:0 | 1 |

held_valid0 canonicalizes the held-output suffix tozero. Original output token/generation/context/frame_first are in at_edge. held_valid1 records the OLD registered item exactly, regardless of sameE physical transfer or stall. response_on_abort is an actual response ACK (whether matching or malformed); read_on_abort is an actual request ACK. pending_after_edge=request_fire || (old pending && !exact-terminal-fire); no cancel-only decrement.

## Actual FSM and static cycle budget

Codes: IDLE0, READ_REQ1, READ_WAIT2, MEAN3, LOAD4, CALCULATE5, SEND6, DRAIN7, QUIET8, CLOSE9, BUILD_REPORT10, WAIT_REPORT11. All predicates use pre-edge state; no request/response/output/descriptor replacement lookthrough.

Let descriptor ACK be E0; assume actual caller+B memory path, no cancellation/errors, all request/response/FFT/close/report sinks immediately ready and no vendor/file failure. Read i requests at E(2i+1), ACKs response at E(2i+2); last row ACK E2048. Means lock E2049..2052. Initial synchronous cache/ROM load E2053. FFT item k generates at E(2054+2k), ACKs at E(2055+2k), k0..8191. Final ACK E18437; QUIET E18438, actual matching close E18439, report locks after E18440, earliest report ACK E18441 and next descriptor ACK E18442.

Decomposition descriptor-to-report:2048 read edges +4 means +1 initial fetch +16384 output edges +1 quiet +1 close +1 report =18440 edges. FFT_INPUT ideal II2,8192 beats; cache read/ROM prefetch at prior ACK does not generate a replacement valid on that edge. This is static logic/caller-derived latency, NOT measured simulation, hardware WCET or realtime promise. Cancel at E with no pending, or exact pending response ACK at F>=E, takes drain-to-quiet F+1, quiet-to-close F+2, matching close at earliest F+3, report at earliest F+4. Caller/hardware stalls, malformed echoes, pending response loss or held report/abort can extend indefinitely; no finite deadline, full H3 or losslessness claim.

Storage: PCM1024×96=98304bits, ROM1024×18=18432bits, four34-bit sums, four24-bit means, one FFT output register plus identity/control, persistent report2002 and abort2080bits plus live diagnostic state. Actual primitive count/utilization and STA/CDC/RDC are NOT_RUN/UNVERIFIED. Power NOT_APPLICABLE. No vendor primitive/IP, XDC, regmap/IRQ/DMA or new clock domain.

## Evidence and next owner

New product only; old caller/consumer/A dependencies unchanged. This writer supplied no test asset and ran no compile/elaboration/simulation/synthesis/implementation/board command. Source freeze and exact dependency/ROM hashes are in this batch's writer report. Sequential author DIAGNOSTIC_SMOKE must include a real caller+B storage path and record measured cycles; original B-REVIEW owns independent frozen rule-to-test evidence afterwards. Original limits/STOPs persist. This private source/documentation is not acceptance.
