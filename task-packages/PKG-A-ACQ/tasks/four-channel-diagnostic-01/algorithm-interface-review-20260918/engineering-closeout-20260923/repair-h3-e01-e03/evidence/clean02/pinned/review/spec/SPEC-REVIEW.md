# B independent Spec axis

Reviewed 2026-09-21. Original packages untouched. Commands used local Python 3.12 with `-B`; scripts and exact outputs are adjacent. No ARM/AMD build, hardware, old capture/FFT/endurance replay. Parent reviewer runs author entry commands separately.

## Task 1 — f879a54cf40359209895af955bcef92accdf79ea

Spec read: README, A-CONFIRMATION, BUDGET, exact archived B-RESPONSE; implementation: source/logic_adapter.py and pinned functional Framer. No blocking mismatch found for the stated accepted-row/software-math scope. Independent `framing_oracle.py` constructs 30 deterministic random runs (180,000 accepted rows, 87 complete frames) with clip/drop, adjacent errors, long intervals and IDs above 2^53. A separate clean-run segmentation oracle matches event rows, all frame PCM, original IDs, row extents and logical intervals. Output: framing-oracle-results.json, all PASS.

No scope creep found: incomplete identity ABI, finite counter guards, real ready/valid, CDC and timing are expressly excluded, not covertly claimed implemented. `commit_decision(last_id=1023, ttl=512, available=100)` accepts the contradictory time; recorded as an input-precondition observation rather than a blocker because this predicate assumes trusted availability and does not claim a complete timestamp validator. Engineering Results explicitly adds a lower-bound guard. No production/hardware approval follows.

## Task 2 — 0abdc91c57787b7c868a797b88f35129de169faf

Spec read: README, ROUTE, NUMERIC, BUDGET and cited B response. Two implementation mismatches block treating the new Results lifecycle model as contract-conformant. Both reproduce using normal immutable-string arguments, without malformed values:

1. **Post-commit error after revocation escapes fail-stop.** `engineering_model.py:69-72` overwrites COMMITTED with REVOKED; `:99-104` recognizes a historical commit only from current state. Sequence commit → CLIP barrier → new clean interval → error(old frame) records FRAME_ERROR, keeps failed=False/active=True, then allows another COMMITTED result. Violates ROUTE.md:25 and B response line54 requiring retrospective fault/fail-stop after an already published result, irrespective of subsequent HOLD revocation. Keep immutable `ever_committed`/commit audit separate from usability and regress clip/STOP/RESET interleavings. Direct post-commit error without barrier correctly fail-stops (control case).

2. **Session configuration is not frozen.** `engineering_model.py:52-67` binds only per frame; `:108` compares against that per-frame value. Frame0 configA and frame1 configB both commit under the same epoch/interval, contrary to ROUTE.md:23 (changes require new session). A mutable mapping also changes the already-submitted snapshot because line66 stores it by reference, violating ROUTE.md:15. Establish immutable session binding and immutable submitted snapshots, or strictly restrict/enforce an immutable binding representation, and reject in-session changes.

Commands: `python -B .../adversarial.py`, `python -B .../framing_oracle.py`. Both exit0 means evidence scripts executed; adversarial-results.json explicitly records the observed **failures**, not approval. Original source hashes included there. No scope creep found; conditional budgets remain REALTIME_BLOCKED, missing real timing evidence is a stated scope limit, not one of these blockers. Historical R1/R2 pending text is not a demand to repeat accepted repairs.
