# NP-1.0 numerical preprocess to FFT_INPUT

Task `I17-NUMERIC-PREPROCESS-20261007`, FULL / RTL_IMPLEMENTATION. Frozen architecture SHA256 `974400be40c5f547cb0d056a45e31cc9ace37162121bc8f922c9568b12455764`; parent `758cfc47e4b26d24ac9e88da3f30587d220c54bd`. New source is pending independent validation. No product or test acceptance follows from this document.

`pcm4_numeric_preprocess.sv` is a real single-window reader of the existing `pcm4_window_caller` descriptor/read/close interface. It stores 1024×4 signed24 codes, computes four exact means, then emits independently windowed Gate and DOA FFT input streams. It does not implement FFT, activity, PHAT, localization, Tracker, DAS or complete H3.

## Source and integration

`SOURCES.txt` lists the single new SystemVerilog module, relative to this directory. Keep original caller/entry/consumer and six A source dependencies at their authoritative paths; this module does not instantiate copies of them. Connect its descriptor/read/response/close and eligibility/error ports directly to the one original caller. Connect `cold_rst_n` to the same caller cold initialization; never connect ordinary slice reset as datapath recovery. Existing source/interface files are unchanged.

Set `research_profile_valid` explicitly only after binding this fixed research numeric profile and table identity. Route persistent `abort_valid/abort_payload` to a downstream consumer that implements same-clock cancellation priority. An ordinary FFT receiver that ignores cancellation is not an approved integration. Keep `fft_ready`, `report_ready` and `abort_ready` real capacity/consumption signals. Report ACK and abort ACK are independent; neither alone frees a live lease or pending read. Connect caller save/audit/control sinks according to their original contracts.

`HANN_FILE` defaults to `hann-u18f17.mem`, resolved by the elaborated design's tool working directory. An integrator may specify another path to the exact SAME manifest-bound bytes; verify SHA256 before compile/run. ROM is an actual readmemh runtime dependency, not a comment-only constant. Do not regenerate cosine or select a same-name mutable file. Missing/short/out-of-range coefficients fail closed when consumed; in-range substitutions require byte-identity preflight. This batch creates no vendor project, build BAT, IP or external engineering entry.

## Exact two-domain computation

Gate: four signed34 exact sums → RNE(/1024) signed24 means → signed25 x-mean → exact multiply by U18F17 Hann → RNE(/2^17) signed25 → exact <<4 signed29, imag0.

DOA: original signed24 x → independent Hann multiply → RNE(/2^17), signed24 saturation with overflow detection → exact <<4 signed29, imag0. Gate is not clamped to signed24 and DOA does not subtract means. Internal range/coefficient failure retains error and aborts before normal emission of the affected item.

The original frozen Hann is 4096B U32LE SHA256 `51a05f855181f1774c3373c83085fd5a2792f5db932d66b1f3dc768e8ec6a2f2`. Its exact `.mem` conversion is 6144B SHA256 `487c7f988ab00fc0428dc3fbe1705e933eac96ef4f54519727bf9fb0d11dc1bf`, 1024 LF lines of five lowercase hex digits, index0..1023 in line order. [table-manifest.json](table-manifest.json) binds source commit/path/blob/raw bytes, conversion and actual encoded bytes. Local `.gitattributes` preserves LF in this new directory only.

## Capacity, ordering and lifetime

One PCM cache (98304bits), one ROM (18432bits), four sums/means, one accepted read pending, one registered FFT_INPUT item, one 2002-bit report and one independent 2080-bit abort record. New descriptors cannot overwrite a report/abort slot. RAM is not reset; validity/identity and qualified row count control all use.

Output order is Gate ch0..3, then DOA ch0..3, each index0..1023; 8192 complex FFT_INPUT beats. Full token/generation/context/raw frame identity and index remain aligned under stall. Only actual checked read responses can enter sums/cache. A wrong response echo is audited/ACKed physically but cannot terminate an accepted request; absent a matching terminal response, pending and lease remain and the affected path stalls closed.

Lease remains through both domains' final qualified transfers, or through cancellation and real pending-response drain. Matching close/no-future-access is generated only in the derived terminal state. Closing is not completed caller retirement/save. Controlled `data_clear_req_valid/ready` while active records cancellation first and then drains/closes; it cannot silently clear outstanding work.

Cancellation preserves strict-before-edge OK and physical history. A same-edge old output may TRANSFER_ON_ABORT and is counted separately from qualification. A stalled old output withdraws after that edge; abort closes its logical obligation without waiting for output ready. Persistent report/abort retain original identity and explicit incomplete/error statuses. Later ready never revives an old generation.

See [NUMERIC-CONTRACT.md](NUMERIC-CONTRACT.md) for all ports, status/error/reason codes, report/abort bit layouts, conservation, lifecycle and cycle edge contracts.

## Budget and evidence limits

Static no-stall actual caller/B-memory schedule from descriptor E0: 2048 read edges +4 mean edges +1 first fetch +16384 FFT input edges +quiet/close/report3 =18440 edges to visible report. FFT_INPUT ideal II2. Actual matching close E18439, report after E18440, earliest next descriptor E18442 with immediate report ACK. Measured simulation cycles are NOT_RUN in this source-writing batch. Unbounded external stalls, missing terminal responses or held report/abort mean no finite deadline; no production losslessness/realtime promise.

The arithmetic path is synchronous cache/ROM output → 25-bit subtraction where needed → signed25×positive19 multiply → full-width magnitude/RNE/range check → registered signed29 output. Actual mapping, mux/depth/fanout/critical path, utilization, Fmax, STA/CDC/RDC, cold invalidation, external frontend feedback and board remain UNVERIFIED. Single clk; no new CDC/XDC/IP/CSR/IRQ/DMA. Power NOT_APPLICABLE.

Mathematics is bound to portable source commit `ba32fa3ae9b123ae8b843cd7d5485c18a4463d1d`, chain SHA256 `7a0846bfdd5ac03105806544a4dd0533410616737df347ad199282198e325714`, source manifest `80880da38c143cd720833e5a4ce1fd66493e7b75a2842f6cc60572d567fd3b83`, fixed_golden leaf `f6bb2bc41dee3f1e2e6d93176972d92db12d687978fd3a95a47e85b28f88a74a`, B-r2 `30a9a550d4303d464dc2e56d8b2ce38774b49c1d8e313bc70efbc0c4b06c5924`. Old full-chain/FFT evidence is not new RTL acceptance.

This product writer ran no compilation, simulation, synthesis, implementation or hardware and wrote no test/checker assets. After source freeze, the coordinator routes read-only shadow inspection and a separate sequential DIAGNOSTIC_SMOKE using at least one real caller/B path; original B-REVIEW independently validates the frozen product. Exact writer snapshot/evidence is under `codex_out/i17-numeric-preprocess-product-20261007/`. Original limits and repair STOPs persist.
