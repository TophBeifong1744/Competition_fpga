# Saved-research partial evidence producer

Python standard library, research only. This package reads fixed saved evidence;
it does **not** import portable algorithms, replay FFT/PHAT/IFFT/Tracker/DAS,
decode correlation values, run mathematical V, or emit receiver/hardware status.

From the exact checkout's `models/python` directory:

```text
python -B -m soundsight_h3_evidence producer --access-map <absolute map.json> --selection <absolute selection.json> --registry <absolute registry.json> --out <absolute new directory>
```

No installation or global PYTHONPATH is needed. The output directory is created
exclusively. Existing output is never modified. Inputs are read-only; use `-B`
to prevent bytecode artifacts. The package's executing files and input/control
bytes are recorded; final delivery binds them to the exact Git candidate.

## Adopted bounded scope

This implementation follows `INTERFACE-PREP.md` SHA256
`49e1591cae8a06168fd6aeabdf358db11d2ec2f77d8f2b1cee161c70eeba6d18`
and the explicit I17-PRODUCER-PARTIAL-PRODUCT-B-01 dispatch. The control
`PROPOSED_NOT_ACTIVE` label remains research metadata, never an authorization
token. No production schema has been activated.

Decoder source specification: `6931206cc7dc89f992913e8231a5c95604bcafb5e1a7faec1facf4a08329f5ed`.
RAW R1: `902fb37e4b7533c22c8b59d1c3b011f7820df3e5063ccff994b940496464cbc2`.
All six source schema/version/hash/encoding and role/scope combinations are
fixed in `contracts.py`. Registry content whitelists restrict access further;
they cannot add executable modules, source-context/native codecs or arbitrary
global rules. Global rules also require the exact SPEC source whitelist.

The three control formats have closed fields, strict UTF8/no BOM, no decoded
duplicate keys or unknown fields, and no JSON numeric tokens. Integers use
decimal strings; null does not stand for UNKNOWN. Their file byte bindings are
verified before source consumption. Legacy JSON has its own admission rules;
its original integers and 1117570-byte result are not rejected using the RAW
1MiB/numeric-token rule. Source bytes are never normalized or rewritten.

FILE capabilities are explicit absolute ordinary local paths. URL/UNC/device,
ADS, traversal, wildcard, environment expansion, symlink and Windows reparse
ancestors are rejected. Paths are checked before/after open/read; inode, size,
mtime and raw hash are checked before publication. These checks are not a claim
of an OS sandbox or immunity to hostile concurrent filesystem race attacks.
ZIP_MEMBER only refers to a mapped FILE container; no nested extraction, pickle,
filesystem extraction or payload-driven URI lookup. Classic central-directory
limits are checked before constructing ZIP metadata. ZIP64/encryption are
explicitly unsupported. The selected member has separate bytes/hash/CRC.

Stored/DEFLATE streams are consumed to their real end under the live expansion
limit, including true length and CRC checks. Claimed file_size cannot hide
trailing expansion. NPY headers also reject duplicate keys before literal
evaluation. These operations do not decode any correlation value.

## Outputs and process codes

`report.json` separates producer_result, V, missing, unsupported, original_errors
and known conflicts. `run.json` records execution and source identity;
`output-index.json` binds the emitted bytes. Complete verified saved sources are
copied as `originals/<actual-sha256>.bin`. These are exact saved bytes, not native
execution records newly created by this exporter. Eligible per-view RAW files
are in `raw/`; all have audit.NOT_RUN, unknown full K/ordered roots/lifetime,
no native events, and no CHECKED_SOURCE coverage.

| Code | Meaning |
| --- | --- |
| 0 | A report was generated; it may be INCOMPLETE or UNSUPPORTED. Never PASS. |
| 2 | CLI/control structure or output-directory error. No successful report. |
| 3 | Known byte/source identity/type/locator conflict. Can have a sealed FAILED report, or failure-only when controls cannot be trusted. |
| 4 | Internal failure or runtime drift. Failure-only; partial outputs are INVALID diagnostics. |

Known conflicts survive unrelated missing/unsupported evidence. Their occurrence
does not pretend V ran: **V always NOT_RUN**. SEALED_REPORT means stable output
bytes, not provenance/identity closure or member acceptance. A successful process
is separate from a successful evaluation, which this package does not perform.

The complete selection denominator is retained: requested = processed +
not_processed. Equal tau at different frame/pair selectors never merges views.
Original TAU_BOUND qualification rejection is separate from numeric invalidity;
saved units, raw reasons, per-component audit locations and full history bytes
remain available. No missing flags are replaced with zero. The full source is
preserved even if a report text/RAW field cannot carry a long reason. A reason
over 64 UTF8 bytes is not a valid Error381.reason; over 1024 bytes cannot be a
KNOWN RAW Text. More than eight raw diagnostic entries are not truncated or
claimed to be a valid typed eight-slot wire Error list. No namespace/code/native
or PROTOCOL=7 is guessed from strings. Any capacity-blocked RAW is explicitly
listed; the report and original bytes remain, without a wire success claim.

Partial original identities are saved independently. Root/Object expectation is
not an input here: complete K12/ordered-roots three-way comparison belongs to a
future separately authorized V. Source-context/native/lease codecs, original
timestamps, EOF/STOP contracts and production parameters remain unsupported or
missing. Saved available/commit/take and arrays are not native_done/readable.
Cancel/termination history is not reinterpreted or rewritten. wire_ready=0,
time UNBOUND, #18/Case167/previous STOP and accumulated findings are unchanged.

## Explicit software resource limits

Per control: 1MiB/16 layers; map/views 256, registry 32, whitelist 256, supports32.
Actual new-content acquisition, including rejected/partial FILE reads and emitted
ZIP bytes, is charged immediately against read_budget_bytes and a 64MiB hard
software cap. Successful cache admission is separate from acquisition; an identity,
CRC, size, stream or later read failure does not refund acquired bytes.
FILE/container16MiB; expanded member8MiB; total expanded32MiB;
ZIP entries4096 and central directory1MiB. Source reads/decompression use at
most 1MiB chunks. Containers and members count separately; repeat use of the
same admitted source does not re-read/decompress it. The NPY parser only checks
its bounded header, 6x1024 `<i8` layout and row byte span; no numeric code decode.

Legacy JSON: 64 layers, 250000 lexical nodes, decoded string1MiB/total16MiB.
Lexical limits are enforced before a complete decoded tree is constructed;
only one complete legacy tree is held at a time. Sources are hashed/checked
before parsing. Unknown extensions are retained in original bytes, not granted
evidence merely for being present. Resource rejection is RESOURCE_UNSUPPORTED,
not truncated input or a fabricated source conflict. Earlier real conflicts
remain. Read budgets are software resource parameters, never acoustic defaults,
hardware cycles, service budgets or production time bounds.

Unconsumed legal numeric extensions preserve their lexical tokens without
becoming integer evidence. Consumed integer fields require actual integral
lexical tokens in their range; float/exponent/-0 cannot pass via coercion. Native
JSON non-finite tokens are rejected. Nested config/source-manifest groups are
retained through exact source pointers rather than keeping multiple decoded
trees alive. Optional Git observation records HEAD/dirty state; raw executing
file hashes remain authoritative if Git is unavailable.

The byte-cache/JSON limits are **not** an interpreter/OS/RSS hard bound. Temporary
chunks, UTF8 decoding and Python tree overhead exist. Windows PeakWorkingSetSize
is recorded where callable; otherwise UNKNOWN. A measured peak is not a proof
of a process upper bound or WCET. Post-verification does not recharge distinct
source budget; its streaming read is separately a stability check.

### I17-PRODUCER-T1-01 resource audit

`source_audit.distinct_source_bytes` is acquisition spent, not verified-cache size.
Each previously unverified source ID/locator consumes its actual FILE/expanded
bytes, including when its declared hash names already cached content. It must fit
the remaining budget before reading and is charged while reading, without refunds.
Only an already verified ID's immutable buffer is reused without another acquisition.
`expanded_member_bytes` includes actual emitted member bytes even when the member
is rejected. `verified_cache_bytes` counts only complete verified content retained
for reuse/`originals/`. Equal content at a new location may share that buffer only
after the location's own budgeted acquisition and identity checks succeed; verified
cache bytes may thus be smaller than acquisition spent. `identity_check_bytes` is
retained for output compatibility and is zero: new-location authentication is not
an exempt hash-only check. Post/stability rereads remain `post_check_bytes` and do
not recharge primary acquisition. No counter is a hardware time bound.

Each actual read record adds `acquisition`: `mode` (NEW_CONTENT),
`state` (VERIFIED or REJECTED), `charged_bytes`,
`complete`, and rejected `reason`. For a partial rejection, `observed` hashes/counts
only the returned prefix, never an asserted complete object; `complete=false` and
`post=NOT_VERIFIED` make that distinction explicit. A complete identity-rejected
FILE may have `post=UNCHANGED`: stability does not grant identity validity. Sources
rejected before acquiring any bytes are listed on the affected missing/unsupported/
conflict axis, not fabricated as read sources. A retry of a failed ID preserves the
error without another acquisition; failure metadata is not a verified byte cache.
Failure-only output adds `source_accounting` alongside the retained read records.

The FILE reader uses the pre-open length and final stamps without a +1 byte probe.
The inflater caps each returned output chunk at the exact remaining budget and
stops when that limit is reached without a proven stream end; it does not generate
an extra byte beyond the ceiling to test for overflow. Resource refusal retains
already emitted prefix accounting, never publishes a truncated member as valid.
Frozen tests remain read-only; author repair diagnostics are not independent
acceptance or closure of this finding.

Round2 removes the old free new-location cached-hash behavior: at a fully consumed
budget, another unverified locator is RESOURCE_UNSUPPORTED before it is read,
even if it would contain equal bytes. No identity conflict is invented from unread
payloads; earlier actually observed errors remain. The old author full-budget alias
expectation is retained in old evidence as a superseded behavior, not edited to
hide the difference. Already verified same-ID FILE/ZIP buffer reuse is unchanged.

## Module responsibilities / review handoff

`contracts.py`: fixed interfaces and bounded admission.
`sources.py`: capability reads, resource accounting, ZIP/NPY byte views.
`producer.py`: original selected fields, internal links, complete error/source
audit; explicit incompleteness rather than root backfilling.
`raw_export.py`: limited lossless RAW diagnostics, no verification.
`__main__.py`: authoritative CLI, post checks, error exits and output identities.

Author tests are DIAGNOSTIC_SMOKE only. Product freeze precedes nonauthor test
assets and subsequent independent review. This package grants neither its
author nor an author-owned agent acceptance authority.
