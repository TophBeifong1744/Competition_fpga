# Real PYNQ receive adapter: API and state-machine design

Status: design only; no board adapter implementation is included or qualified.
`pynq_probe.py` remains fail-closed.

## Proposed boundary

The future adapter consumes a statically validated receive profile and exposes
only these operations:

1. `inspect_overlay()` parses the same-build HWH without downloading it and
   returns the exact IP/interrupt inventory.
2. `admit_runtime()` records the installed PYNQ/driver/allocator versions and
   proves the required cache operations are available.
3. `load_overlay()` downloads only the already-bound bit/HWH pair after explicit
   operator authorization.
4. `allocate_rx(length, alignment)` returns a buffer plus physical address and
   records whether coherence is genuinely guaranteed.
5. `prepare_rx()` establishes clean ownership; non-coherent memory is prepared
   according to the validated policy before arming.
6. `start_receive()` marks ownership as possibly DMA-held before invoking the
   driver, so an exception cannot be treated as “never started.”
7. `poll_fresh_status()` returns transaction-bound status, actual length and
   error bits; stale/default status is invalid.
8. `request_stop()` uses only the declared source stop/drain sequence. It does
   not infer a whole-PL reset.
9. `invalidate_and_read()` is legal only after completion and fresh quiescence.
10. `release()` is legal only after CPU ownership is restored; otherwise the
    buffer remains retained for diagnosis.

Exact PYNQ method names are deliberately not frozen until the board image and
installed `pynq` package are measured. The intended mapping may use
`Overlay(..., download=False)`, HWH/IP dictionaries, `allocate`, and an AXI DMA
receive channel, but a documentation guess is not executable evidence.

## State machine

```text
PREFLIGHT
  -> OVERLAY_INSPECTED
  -> RUNTIME_ADMITTED
  -> OVERLAY_LOADED
  -> CPU_OWNS_BUFFER
  -> PREPARED
  -> DMA_MAY_OWN
  -> COMPLETED_AND_QUIESCENT
  -> CPU_OWNS_FRESH_DATA
  -> VERIFIED
  -> RELEASED
```

Any arm, timeout, DMA error, short output, cache failure or unreadable status
moves to `FAILED_RETAINED`. A reviewed abort may move it to
`ABORTED_AND_QUIESCENT`; only then may ownership return to the CPU. Clearing an
error bit, deleting a Python object, or waiting an arbitrary delay is not a
quiescence proof.

## Evidence required before implementation

- exact supported PYNQ image and installed package/driver versions;
- one same-build bit/HWH/manifest set parsed successfully on that image;
- measured allocator alignment/coherence and cache-operation behavior;
- exact driver status/error/timeout/abort semantics; and
- a disposable safe source plus raw normal/short/timeout/stale-cache traces.

Until those exist, the mock state machine is reusable design evidence and the
real adapter remains blocked.
