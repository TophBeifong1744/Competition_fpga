# Receive-only negative-test matrix

All cases below are generated from the same valid synthetic fixture by
`scripts/replay_receive_cases.py`. A negative case succeeds only when the
validator returns `FAIL` and includes the named issue code. These are parser
and contract failures, not physical board faults.

| Case | Single change | Expected result / first relevant issue |
| --- | --- | --- |
| `valid` | none | `PASS` |
| `missing-s2mm` | remove the declared DMA module from HWH | `FAIL / HWH_S2MM_INSTANCE` |
| `mode-mismatch` | declare scatter-gather | `FAIL / CONTRACT_MODE` |
| `dre-mismatch` | claim S2MM DRE | `FAIL / CONTRACT_S2MM_DRE` |
| `axis-width-mismatch` | profile says 64-bit AXIS while HWH says 32 | `FAIL / HWH_C_S_AXIS_S2MM_TDATA_WIDTH` |
| `length-mismatch` | profile says 13-bit length while HWH/max say 14-bit | `FAIL / HWH_C_SG_LENGTH_WIDTH` and `MAX_TRANSFER_LENGTH` |
| `payload-hash-mismatch` | replace external schema hash | `FAIL / PAYLOAD_SCHEMA_HASH` |
| `build-mismatch` | change manifest build ID only | `FAIL / MANIFEST_BUILD_ID` |

The unit suite adds disabled S2MM, memory-width mismatch, maximum-length,
TLAST, cache policy, control stop semantics, transfer granularity, bit hash and
HWH hash cases. Existing lifecycle tests retain stale-cache, short-output,
timeout and completed-but-not-quiescent release failures.
