# Requirement → test → evidence

| Requirement | Test/checker | Evidence |
|---|---|---|
| 61.44 MHz period 1228800 edges | direct interval model, ID 3, eight complete periods | `edges_3.csv`, CASE_COMPLETE |
| 500/1500/2500 us exact and 506 us rounded up | every-edge model, width coverage counters, ID 3 | edges/falling edges and coverage counters |
| Original integer-MHz output behavior | original-output miter at 1/50/100 MHz | IDs 0/1/2, no MITER_CHECK failure, case drains |
| Active command bus during reset does not replace reset target | reset-held active inputs and T0 scoreboard | startup/reset edge rows |
| Mid-period commands leave pulse unchanged | commands during high and low phases, every-edge model | accept rows plus expected pulse edges |
| Command at boundary applies next period | exact-boundary command and pre-boundary command | accepted-cycle rows, following two pulse widths |
| Latest of continuous valid commands wins | 100 consecutive valid edges, deterministic pattern | accept rows, subsequent expected/observed period |
| Reset immediately lowers output, high or low | between-edge reset checker, both phases | async_reset rows |
| Recovery after reset | restart then pulse fall against reset target | reset and subsequent edge rows |
| Legal MAX/RESET bounds | MAX 1/reset 0; MAX 511/reset 511 | IDs 4/5 |
| Invalid parameters fail | CLK 999999, MAX 0/512, RESET -1/361 | expected-fatal isolated jobs |
| Critical checkers are live | model, miter, async-reset isolated observation faults | three distinct canary fatal markers |
| No stale pending expected work | bounded complete cases, six done flags | ALL_CHECKERS_COMPLETE pending=0 |
| Top admits 61.44 MHz only when configured; other guards unchanged | exact top diff read only | parent `PWM-61M44.diff`; full top simulation NOT RUN |

No FIFO, AXI, DMA, IRQ, CDC or FFT behavior is in this modified PWM verification cone. Those requirements are not inferred as passed. Reset, boundary, arithmetic rounding, illegal parameter handling and recovery are the relevant checks here.

Product author and test author are different. This document and all test assets require a separate qualified reader to accept the resulting evidence; the test author reports checker outcomes only.
