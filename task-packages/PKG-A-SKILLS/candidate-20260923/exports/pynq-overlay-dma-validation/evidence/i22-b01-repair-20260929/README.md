# I22-B-01 bounded offline verification

The synthetic static receive-profile gate matched all 19 independent CLI
expectations. Four focused unittests passed, including an isolated negative
canary that rejects an obsolete PASS expectation for 1-byte alignment. This
is verification-asset author evidence, pending separate read-only review.

## Requirement to test traceability

| Requirement basis | Expected result | Cases |
| --- | --- | --- |
| PG021 Table 2-24, no-DRE S2MM destination address follows memory-mapped data width | At 64 bits, alignment 8/16/64 passes; 1/4/12 fails `S2MM_ADDRESS_ALIGNMENT` | `new-alignment-*`, unittest `test_no_dre_address_granularity_from_memory_width` |
| Same width rule at 128 bits | 8 fails, 16 passes, with matching profile/HWH and refreshed manifest hash | `new-width-128-*` |
| Frozen receive contract requires positive exact integers and byte-addressable widths | Boolean, zero and absent fields fail `CONTRACT_INTEGER`; width 12 fails `BYTE_WIDTH` | `new-alignment-bool/zero/missing`, `new-width-bool/zero/missing/12` |
| Existing candidate rejects DRE | DRE=true with 1-byte alignment fails `CONTRACT_S2MM_DRE` and does not trigger new no-DRE gate | `new-dre-alignment-1` |
| PG021 Table 2-25 and frozen receive length contract keep length separate from address alignment | A 96-byte transfer passes 4-byte stream beat and length granularity while the declared address alignment is 64 bytes | `new-length-96-alignment-64` |
| Original I22-B-01 counterexample | Fixed old CLI still returns static PASS for alignment 1; frozen new CLI rejects the same declarative defect | `old-original-64`, `old-alignment-1`, `new-original-64`, `new-alignment-1` |

`summary.json` indexes every run and native report SHA-256. The seven key
case folders here retain native JSON reports and command records. Every CLI
run, including full synthetic inputs, stdout, stderr, report, input hashes,
command, cwd, Python version, and exit code, is under the shared repair
workspace `codex_out/pr32-i22-b01-repair-20260929/verification/cases/`.
`REVIEW-PACKET.zip` carries the frozen validator, contract, focused test,
the small synthetic fixture needed to rerun it, this index, and selected
synthetic native evidence for B's offline review;
`PACKET-MANIFEST.json` records each archived member's SHA-256.
The focused unittest record is `unit-verified-command-result.json`; its
stderr is `unit-verified-stderr.txt`. The earlier counterexample and its
first-failure evidence remain untouched in
`codex_out/pr32-i22-b01-receipt-20260929/received/review/`.

Baseline product checkout: `6a1efb1fa945ec17a38baa128ca93fb829503085`.
Frozen validator SHA-256:
`5c693d637e7a0c109634fbe11ce3026a376ba77793c4bad777c2cc1968b0101e`.
Frozen contract SHA-256:
`79dd356f81e304107041a0932a6f9b6421e9e435e7903599e304c746c8d7f08b`.

Scope: synthetic parser inputs and static CLI only. Real PYNQ allocator,
driver, overlay load, physical DMA, board behavior, timing, and CDC/RDC are
NOT RUN; this evidence cannot establish those claims or member approval.
