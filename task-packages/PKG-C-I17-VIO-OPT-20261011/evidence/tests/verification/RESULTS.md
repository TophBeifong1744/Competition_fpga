# PWM focused check results — 2026-10-10

Status: **CHECKERS_COMPLETE_PENDING_INDEPENDENT_REVIEW**. The verification asset author does not sign these assets or claim full system acceptance.

Product snapshots are unchanged from the writer freeze:

- `motor_drive.v`: `5c1a62f19ed0f25c06f22e521df90161dcbe2f835e2bc2dfaaf1b37ff7b41aa9`
- `four_mic_live_loop.sv`: `21d4decb91e0850d2e7634f4dd1dcd212552e500151b1ec79d564d1bd9f101e4`

Main raw run: `runs/nominal-attempt5`. Native XSim 2025.2, SW Build 6299465. `run.json` records each exact argv/cwd/source hash and stage exit. xvlog → xelab → xsim all exited 0. `xsim-stdout.log` records six CASE_COMPLETE markers and `ALL_CHECKERS_COMPLETE seed=17010 pending=0`.

| Case | Checked cycles | Result |
|---|---:|---|
| 1 MHz, MAX360 | 165711 | Math scoreboard + frozen original miter complete |
| 50 MHz, MAX360 | 8280111 | Math scoreboard + frozen original miter complete |
| 100 MHz, MAX360 | 16560111 | Math scoreboard + frozen original miter complete |
| 61.44 MHz, MAX360 | 10174575 | Math scoreboard complete; 3 fractional-width periods |
| 1 MHz, MAX1/reset0 | 165711 | Bound check + miter complete |
| 1 MHz, MAX511/reset511 | 165711 | Bound check + miter complete |

At 61.44 MHz, raw edge records show rising edges separated by 1228800 clock edges; 500/1500/2500/506 us high intervals are respectively 30720/92160/153600/31089 edges. Same-boundary, pre-boundary and mid-pulse commands, continuous valid, active reset inputs, reset high/low and recovery were checked by the independent cycle model. See MODEL-CARD and TRACEABILITY for exact scope.

All three isolated observation-fault canaries triggered their named checker: PWM_CHECK, MITER_CHECK, ASYNC_RESET_CHECK. All five illegal parameter runs triggered their named fatal checks: clock below 1 MHz, MAX0, MAX512, reset below 0, reset above MAX. Expected-negative XSim process exit codes and exact fatal text are preserved; runner judges expected fatal markers rather than assuming any clean exit proves rejection.

Environment history is retained in `runs/nominal` and attempts2–4. They failed because direct native invocation needed vendor runtime variables/Tcl/JVM/Python paths. They are TOOL_ENV_FAIL, not product faults. Installed BAT wrappers returned 1 without output. The working runner changes only the child-process environment and uses official native executables. No global environment, D-drive project, GUI or hardware was changed. This does not validate the formal desktop BAT.

Full top/IP simulation, full board elaboration, synthesis, implementation, timing/CDC and hardware motion are **NOT RUN**. The top change only received static diff/guard inspection. No stub substituted for algorithm or vendor IP. No product defect was observed in this bounded PWM test.

Reproduction by the agent: `python run_checks.py nominal canary_model canary_miter canary_reset invalid_clock invalid_max0 invalid_max512 invalid_reset_neg invalid_reset_high` from this directory, with the recorded installed native tool root. New attempt directories are created; evidence is never overwritten. This is an internal verification entry, not a new step assigned to the user.
