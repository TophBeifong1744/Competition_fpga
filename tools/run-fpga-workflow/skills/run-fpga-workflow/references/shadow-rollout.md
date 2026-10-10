# Shadow reviewer rollout

The temporal-evidence reviewer starts as a shadow specialist, not a permanent blocking gate.

Compare:

- Baseline: existing 12-role behavior;
- Variant A: 12 roles plus stable artifacts/checklists;
- Variant B: Variant A plus the temporal-evidence reviewer.

Use the same snapshot, defect corpus, model/reasoning tier, and budget. QUICK tasks do not invoke the shadow by default. Candidate findings enter a comparison ledger; a real BLOCKER/HIGH still requires ordinary evidence resolution, but one discovery does not prove permanent role value.

Suggested promotion evidence includes complete detection of known blocking canaries, no regression versus Variant A, useful non-duplicate findings across at least two independent projects/targets, controlled false-positive/duplicate rates, bounded elapsed-time cost, and no increase in repair loops. Record actual measurements. Until promotion is evidence-backed, label the role `SHADOW` and keep final sign-off with `fpga_reviewer`.

