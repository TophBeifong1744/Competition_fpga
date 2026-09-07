# Board runbook and failure map

## Admission gate

Before `--download`, confirm all of the following from actual evidence:

- exact board revision and full device part, including speed grade;
- a reproducible PYNQ image or board support package compatible with the board DDR/MIO/boot design;
- working DDR and a supported contiguous-buffer allocator;
- `.bit`, `.hwh`, and manifest hashes from one build and a compatible Vivado/PYNQ flow;
- a safe AXI4-Lite identity block and a bounded MM2S-to-S2MM test route;
- no test path can backpressure or disturb a live physical acquisition stream.

If one item is unknown, remain in offline mode. If PYNQ admission fails within the project schedule, keep the same register/DMA/interrupt contract and use a Vitis or PetaLinux runner.

## Safe execution order

1. Archive the current PL/application state and disconnect unsafe physical outputs.
2. Run offline validation and record the report hash.
3. Parse the Overlay without download and inspect `ip_dict`.
4. Download only after board/device/build/interface identity is consistent.
5. Read identity registers before any write.
6. Allocate bounded TX/RX buffers; fill TX and clear RX.
7. Flush TX, arm S2MM, then start MM2S.
8. Poll both channels with a deadline. On timeout, capture DMA status and stop the test.
9. Invalidate RX before CPU comparison.
10. Compare exact bytes or the declared golden result; record mismatch count and first mismatch.
11. Record byte count, elapsed time, throughput, latency, cache operations, statuses, environment, and hashes.
12. Release buffers. Recovery/reset is a separate, contract-authorized action.

For sustained paths, repeat across minimum, typical, maximum-safe, and non-power-of-two lengths allowed by the contract. Then perform long-run testing with sequence IDs and overflow counters. A loopback alone does not prove continuous sensor capture.

## Competition requirement and typical-failure map

| Requirement or observation | Likely failure | Evidence to capture | Stop/fix direction |
|---|---|---|---|
| Overlay loads but IP names are absent | mismatched or stale HWH | bit/hwh hashes, `ip_dict`, build ID | stop; regenerate a matched artifact set |
| Identity read differs | wrong Overlay, address map, or interface version | HWH address, raw register read, manifest | stop before writes |
| MM2S completes, S2MM hangs | missing TLAST or stream path not connected | both DMA statuses, ILA TVALID/TREADY/TLAST | stop on deadline; inspect producer TLAST |
| S2MM completes with stale/zero data | RX cache not invalidated or wrong ownership | executed cache ops, buffer addresses, before/after bytes | fix ownership and invalidate timing |
| Hardware sees stale TX data | TX cache not flushed | TX fill/hash, flush record, ILA payload | flush after fill and before transfer |
| DMA reports internal/slave/decode error | bad address, interconnect, reset, or descriptor | raw DMASR, addresses/ranges, reset state | capture first; recover only per contract |
| Transfer rejected or truncated | length exceeds IP limit or violates beat/alignment | requested/actual lengths, width/alignment | correct profile or design; never silently round |
| Small tests pass, long tests fail | ring/descriptor/cache/overflow issue | sequence IDs, counters, per-block timing | add stress matrix and explicit loss policy |
| Golden compare fails without DMA error | payload format, byte order, transformation, or stale cache | first mismatch, input/output hashes, schema version | locate first semantic disagreement |
| Throughput varies or misses deadline | Linux scheduling, copies, DDR contention, or PL stalls | distribution across repeated runs, ILA stalls | separate control-plane jitter from PL timing |
| Notebook display looks correct | insufficient acceptance evidence | raw evidence JSON, reports, logs | do not claim hardware acceptance |

## Evidence claims

Use exact wording:

- **Offline validated:** profile, artifacts, contracts, and supplied reports passed static checks.
- **Mock validated:** host-side logic passed deterministic synthetic tests.
- **Board loopback passed:** named board, image, Overlay build, transfer sizes, and repetition count passed recorded loopback.
- **System path passed:** only after the real source/sink, long-run continuity, errors, performance, and recovery behavior are measured.

Never turn the first three into “the whole system passed.” Report RTL simulation, timing/CDC, board loopback, and application measurements independently.
