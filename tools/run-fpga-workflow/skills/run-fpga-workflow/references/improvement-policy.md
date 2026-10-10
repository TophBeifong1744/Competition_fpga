# Improvement policy

The workflow improves by curating evidence, not by retraining model weights.

## Eligible evidence

Only user corrections, reproduced failures with verified fixes, actually executed validation, independent review conclusions, and versioned primary documentation are eligible. Record source, date, scope, counterexamples, confidence, rerun method, and reviewer.

## Routing

- `PROJECT`: device, pin, voltage, clock/reset, regmap, exact command, project workaround, or local acceptance fact; keep in project SSOT.
- `SKILL`: reusable execution practice supported by at least two independent tasks.
- `AGENTS`: cross-project hard gate, normally supported by at least two independent projects/targets and independent read-only review.
- `MEMORY`: user preference only where the host system supports it and the user explicitly authorizes persistence.
- `DISCARD`: guess, self-rating, stale result, unsupported inference, or unsafe/private data.

An explicit user cross-project rule may be promoted directly, but still needs minimal, reversible editing and structural validation. Weakening safety, evidence, single-writer, reviewer independence, interface, clock/reset, CDC/RDC, electrical, or licensing controls requires explicit current authorization.

## Never persist

Secrets, customer information, private paths, proprietary source, device/pin/voltage/address/register specifics, project clocks/resets, historical pass status, one-off workarounds, or unverified tool/license claims.

## Promotion procedure

1. Add a candidate to the ledger; label insufficient evidence `UNVERIFIED`.
2. Obtain the required independent evidence and review.
3. Update one destination in a sequential single-writer batch.
4. Validate load/structure and record rollback.
5. Report what changed, why, evidence, validation, and residual risk.

No eligible candidate means no persistent edit and must not block delivery.
