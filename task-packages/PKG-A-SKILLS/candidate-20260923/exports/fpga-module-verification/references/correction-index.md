# Correction evidence index

This page indexes existing approved evidence and the fresh 2026-09-23 candidate
run. It does not relabel historical runs as new execution.

| Case | First observation | Correction and result | Provenance |
|---|---|---|---|
| One-edge/one-slot false PASS | The old ordered-transaction TB allowed a two-stage elastic mutant to pass with 1149 checks | The repaired TB checks occupancy, valid, ready and payload before/after each edge; the same mutant fails at cycle 2, while the restored one-slot DUT passes 13800 checks | Approved baseline `a7e1ea976da91ba735af5c0a79fffdc7d10c121f`; historical package `task-packages/PKG-A-SKILLS/REPAIR-S1.md` |
| Disposable mutants | Data-bit, empty-stage-ready and two-stage changes compile and elaborate | Each fails during simulation with a recorded first mismatch; the unchanged DUT then passes the same TB | Fresh output is indexed by the parent `candidate-20260923/README.md` |
| B unfamiliar signed8 saturating adder | A held-out `-128 + -1` fault was found in an isolated forward use | The corrected implementation was retested with 65536 input pairs, 66343 transactions and 337372 checks with zero golden differences | Historical B input/result commit `0ef0355642ea8719d5e4cdde0a38c531550218d4`, under `results/skill-review/b-20260914/`; reused, not rerun in this candidate |

Expected negative simulations must reach the simulate stage after successful tool
version, compile and elaborate steps. Tool startup or compilation failure is not
accepted as mutation detection.
