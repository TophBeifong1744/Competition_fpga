# T1 independent expectations — frozen before DUT execution

Task: I17-PRODUCER-PARTIAL-VERIFY-B-01. Product 89ffaf6d7a54bf1c4d0b4b3ca49a376e1e390795.
Author: B-REVIEW, not the product author. New assets require subsequent nonauthor review.
This document and fixtures use contracts/saved source bytes, not DUT outputs or imported DUT functions.

Authorities: SPEC 6931206c…f5ed §§2–4,6,8; INTERFACE-PREP 49e1591c…6d18 §§2–7;
RAW-R1 902fb37e…cbc2; PRODUCT-BATCH d3cd702b…6ac (software resource limits);
TEST-BATCH 2a91cc7d84954fc58f5497e3275d5c4beb17b588976ee05e581b6819454d2807.
The full original bytes are in the independent output inputs/. The older design/24-case
mathematical judgments are reused, not rerun. This partial producer cannot perform mathematical V.

## Independent fixed values and representation

Source result SHA 514028b4…c7c89, frame2: boot DAS_EOF_B_BOOT, session DAS_EOF_B_SESSION,
interval DAS_EOF_B_INTERVAL, frame2/generation23/last_id2047. Pair0 and pair1 remain two views:
peak6/delta13/tau24589; pair0 L1/T22928/false/TAU_BOUND/lag_01/unit34;
pair1 L2/T32425/true/VALID/lag_02/unit37. These are saved facts, not a numerical recomputation.
Report integers are decimal strings; original copied bytes must keep the original hash.

Complete NPY: SHA 6fa87070…de1e5, 49280 bytes, v1.0, `<i8`, C, (6,1024), offset128.
Independent row spans: pair0 [128,8320), pair1 [8320,16512). No code decode.
Whole source and parent/member identities remain separate; same tau cannot merge selectors.

## Case map, checks and coverage

|Group|Independent contract expectation|Executable cases/check category|
|---|---|---|
|Saved source|Two requested and processed views, all selected facts/partial identity/units retained; missing context/array/run/config, exit0 INCOMPLETE|saved_file / FACTS, IDENTITY, DENOMINATOR|
|NPY/container|Parent ZIP and complete member read once; correct row spans; FILE and member separately charged; full byte copies|saved_zip / LAYOUT, SOURCE, RESOURCE_ACCOUNTING|
|Six role dispatch|Exact profile/version/schema hash/RAW_BYTES/role/scope/whitelist; unsupported source never consumed|six_roles, role/scope/schema/version/encoding/whitelist challenges / DISPATCH|
|Structural controls|Decoded duplicate/unknown/number/empty/reference/path traversal are exit2 FAILURE_ONLY; known control binding mismatch exit3; no report|control_* / EXIT, FAILURE_ONLY|
|Original errors|All reasons/history retained; no false numeric validity; typed refs unknown; 64/65 and1024/1025 UTF8-byte limits and8/9 entries are not truncation rules|errors_* / ERRORS, ORIGINALS, NO_ESCALATION|
|Source conflict|Actual bad source hash exit3 FAILED + missing, no consumption; length conflict retained|source_hash/source_length / SOURCE, EXIT|
|Budget|Actual different-source acquisition counts even when hash fails; failed bytes must exhaust budget before next source|failed_read_budget / RESOURCE_BUDGET|
|ZIP/NPY|Actual CRC/stream/end/size matter; duplicate member rejects; unsupported dtype/endian/shape cannot yield accepted layout; member traversal exit2|zip_crc/zip_duplicate/zip_size/npy_* / SOURCE, LAYOUT|
|JSON limits|Source tree depth64 supported vs65 RESOURCE_UNSUPPORTED; no clipping or fabricated conflict|json_depth_* / DISPATCH|
|Output protection|Existing directory contents unchanged, exit2 and no output publication|existing_out / OUTPUT_PROTECTION|
|Internal failure|Internal post-check injected after real source conflict returns4, retains earlier conflict, no valid report/index|injected_post_failure / FAILURE_ONLY; INTERNAL_INJECTION not standalone CLI|
|Checker activity|Separate checker processes reject independent mutations of denominator/facts/identity/errors/budget/raw status and claim scope|canaries / specified semantic category, nonzero|
|Runner propagation|Controlled child17 makes runner nonzero and records17; does not pretend DUT failed|--fail-step / RUNNER_FAILURE|

## Resource derivation (before DUT)

Budget B, two different FILEs of lengths L1,L2, max(L1,L2)≤B<L1+L2.
FILE1 is fully read and has a declared digest mismatch. The hash mismatch is a real conflict,
but cannot undo the already spent acquisition. FILE2 must not be read/processed; RESOURCE_UNSUPPORTED
coexists with SOURCE_BYTE_IDENTITY and FAILED/exit3. Only stability rereads are outside acquisition charging.
Counting only verified cache bytes is not counting actual different sources. ZIP failed inflate bytes
have the same consumption principle, but that sibling path is initially a static finding, not an executed case.

## Failure handling and scope

Exit precedence4→2→3→0 applies only to facts actually reached. Do not infer a source conflict from
bad controls that block reading. Normal missing/unsupported exit0 is report generation, never PASS.
Every successful report: V NOT_RUN/wire_ready0/time UNBOUND; RAW audit NOT_RUN, no native events,
no checked-source coverage; no claims of mathematical V/real time/receiver/hardware.
The checker is a finite projection oracle, not a general RAW/V verifier. It reads saved input
with the standard library and tests declared assertions independently; it never imports DUT.
On confirmed blocking product failure, freeze bounded evidence rather than expanding into full acceptance.
Full stress/RSS/WCET/OS races and other omitted branches stay explicitly NOT_RUN.
