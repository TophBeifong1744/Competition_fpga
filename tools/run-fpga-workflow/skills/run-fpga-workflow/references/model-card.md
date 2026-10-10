# Model Card

Create a Model Card for every non-trivial protocol, device, memory, FIFO, DSP, or vendor model used to support a behavioral claim.

Required fields:

- model name, version, and SHA-256;
- exact device/protocol identity;
- authoritative document title, revision/date, section/table/page;
- port and signal mapping;
- timing, reset, latency, error, and unknown-state semantics;
- abstractions, simplifications, unsupported behavior, and applicability limits;
- conformance tests and independent reviewer;
- whether any algorithm/table/helper is shared with the DUT.

Reject a model that copies DUT RTL, reads internal DUT state to modify expected behavior, changes expected latency after observing the DUT, or fabricates a missing vendor primitive. Diagnostic force/bypass is permitted only when clearly labeled and cannot prove the bypassed function.

Validate the machine-readable card with `references/schemas/model-card.schema.json`.

