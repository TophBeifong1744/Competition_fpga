# C-VIO-EVID-003 gate checker canary — 2026-10-10

Status: **FIXED_PENDING_INDEPENDENT_REVIEW**. Test-only repair; no product changed.

The exact same `tb_gate_map.sv` now runs in two isolated jobs:

- `runs/gate_map-attempt2`: nominal gate/map check, all checks complete, pending0.
- `runs/canary_gate`: `CANARY_GATE` inverts the sampled physical-PWM observation while `permit_open=1` and internal PWM remains HIGH. The unmodified expectation requires output LOW and gate unopened. The independent `GATE_MAP_CHECK no opening mid high pulse` rejects the injected observation at57ns.

This is a fault in the checker observation path only. It does not modify RTL or replace gate behavior, and the nominal run does not enable it. The checker remains the existing physical no-mid-high-opening checker. Control/evidence/PWM regressions were not rerun or modified.

Original test and runner are retained as `tb_gate_map-before-canary.txt` and `run_board_checks-before-gate-canary.txt`. Earlier run directories and repair1 index are unchanged. The updated runner recognizes the specific GATE_MAP_CHECK fatal marker because native XSim returns exit0 even after `$fatal`. Compile/elaborate errors still stop the run; nominal requires its completion marker and no fatal.

Current board aggregate is `94ec3200c0a2e9c0ba3c4e701804a9e8decdd8ef9136edcedfa2d594cc55cefc`; the gate RTL remains `9efdfdecdcc8ce27e2881a5c3647173f2656bcbbbaba85f6422c15e2f56b8e25`. All source hashes/commands/exits and raw-log hashes are recorded in the two new run.json files and `GATE-CANARY-INDEX.json`.

This closes the authored evidence gap only subject to the non-author reviewer. Full-system/IP simulation, physical timing and board acceptance remain outside this bounded check.
