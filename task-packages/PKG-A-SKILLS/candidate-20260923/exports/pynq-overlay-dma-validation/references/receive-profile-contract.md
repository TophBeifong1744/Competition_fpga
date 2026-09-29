# Receive-only S2MM profile contract

This is a separate profile from the approved full-loopback profile. It adds a
fail-closed static gate for a receive-only AXI DMA build without weakening or
rewriting `validate_profile.py`.

## Purpose and evidence boundary

`validate_receive_profile.py` binds one profile to one adjacent `.bit`/`.hwh`
pair and one build manifest. It checks the selected AXI DMA instance and its
HWH parameters, the external payload-schema hash, the control/stop semantics,
and declared receive lengths. A PASS is **static evidence only**. It does not
prove that PYNQ can parse or download the overlay, that buffers are coherent,
that TLAST occurs on a physical stream, or that the board is safe to run.

The current candidate supports polling and explicit RX invalidation only. The
fields describe the declared control contract; a static HWH parse cannot prove
the runtime stop/drain behavior or bitstream provenance. The profile must provide:

- `profile_kind: receive-only-s2mm` and schema version 1;
- exact board/image/device declarations;
- adjacent bit, HWH and manifest paths plus one build/interface identity;
- simple DMA, S2MM enabled, MM2S/SG/DRE disabled;
- AXIS width, memory width, length-register width, maximum length, transfer
  granularity, buffer alignment, TLAST, completion and RX cache policy;
- a separately named run-control/status module and complete-packet stop/drain
  semantics;
- an external payload-schema path and SHA-256; and
- at least one bounded receive test length and timeout.

The HWH must expose these AXI DMA parameters at the exact configured instance:

| Contract field | HWH parameter |
| --- | --- |
| S2MM enabled | `C_INCLUDE_S2MM` |
| MM2S disabled | `C_INCLUDE_MM2S` |
| simple mode | `C_INCLUDE_SG=0` |
| no DRE | `C_INCLUDE_S2MM_DRE=0` |
| stream width | `C_S_AXIS_S2MM_TDATA_WIDTH` |
| memory width | `C_M_AXI_S2MM_DATA_WIDTH` |
| length width | `C_SG_LENGTH_WIDTH` |

The declared maximum is `(1 << length_width_bits) - 1`; each concrete transfer
must still satisfy the configured granularity and contain full AXIS beats.

Without S2MM DRE, `buffer_alignment_bytes` must be a positive integer multiple
of `memory_data_width_bits / 8`, with a positive byte-addressable memory width.
This makes every address admitted by the declared alignment legal for the
selected DMA memory-mapped interface. For a 64-bit memory interface, 8, 16 and
64 bytes qualify; 12 bytes does not. This is an address constraint, separate
from `length_granularity_bytes` and the receive length checks. This candidate
still rejects DRE-enabled profiles under its existing receive-only contract.

## Command

Run from the Skill directory and always select a new output file:

```text
python -B scripts/validate_receive_profile.py \
  --profile references/example-receive/receive-profile.json \
  --output results/receive-static.json
```

The bundled example artifacts are synthetic parser fixtures, not a deployable
overlay. Project payload fields remain outside the generic DMA core. See
`soundsight-record-v1.json` only as one external schema example.
