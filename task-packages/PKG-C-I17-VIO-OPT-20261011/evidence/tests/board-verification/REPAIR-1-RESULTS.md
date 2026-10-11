# Repair1 focused results — 2026-10-10

Status: **CHECKERS_COMPLETE_PENDING_INDEPENDENT_REVIEW** for the listed bounded cases.
Product aggregate: `41f3696c10b4f2c88bd914dc4addea6f7c16fc2cf4c60971eae4d118d52d9d0e`.
Controller hash: `9f7bc21add0fc4166c678882d5584ef318e97ba4c5238cb05fa71b29b9574802`.

| Requirement / finding | Evidence | Outcome |
|---|---|---|
| C-VIO-STATIC-001, frontend5 while DOA busy retains authorization until report | `runs/early_finish-attempt2` | Original reproducer completes |
| C-VIO-STATIC-002, registered warm cannot use old IDLE | `runs/warm_race-attempt2` | Original failing cycle15 now correct; later test-model enum error found |
| Native recovery6→7→8→9→0 and drain before completion | `runs/warm_race-attempt3` | Corrected native stimulus completes; original cycle15 check unchanged |
| Atomic config, readiness, binding, ARM/permit, STOP, observe, one-shot, read actions | `runs/control-attempt3` | 76 checks complete, pending0 |
| Control checker negative observation fault | `runs/canary_control` | CONTROL_CHECK catches corruption |
| Full terminal-word data checker negative fault | `runs/canary_data` | DATA_CHECK catches corrupted terminal word17 |
| Simultaneous report+abort slots; full backpressure; delayed servo accept; full208/23/6-word dumps and repeat; diagnostic1/2/7/63 and malformed records | `runs/evidence` | Prior checker completion reused only after same DUT/TB hashes verified |
| Default-low/low-phase opening/STOP hold/cold reset; actual signed map vectors and rounding | `runs/gate_map` | Prior checker completion reused only after same DUT/TB hashes verified |

The first two original DUT failures remain under `runs/early_finish` and `runs/warm_race`; do not delete or reinterpret them as passes. `FINDINGS.md` is the historical failure-stage record. These new outcomes are input to independent review, not author-closed finding statuses.

The warm-tail reference correction is fully described in MODEL-CARD. This did not change the requirement or adjust a latency to match observed repair behavior. It corrected stimulus against the frozen original manager enumerations and added native return plus AXIS drain checks.

Native XSim2025.2 only. Every job has a separate work database and raw logs. No product, original PWM verification, D-drive project, global environment or hardware was modified by this verification batch. Full-system simulation, IP build, synthesis, timing, CDC and board acceptance are NOT RUN.
