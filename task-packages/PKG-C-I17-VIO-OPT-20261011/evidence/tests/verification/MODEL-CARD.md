# PWM edge-count model — 2026-10-10

Scope: `motor_drive` overlay only. Claim stage FUNCTIONAL_SIM, acceptance pending a non-author reviewer. No claims for full top, FFT, timing, CDC, electrical behavior or mechanical motion.

Independent basis: architect-approved `../pwm-task-contract.json` plus the parent-assigned frozen cycle contract. The model was written by the verification owner after the product writer released the checkout. It computes output intervals directly from mathematical time boundaries, not from the DUT divider/accumulator/state. It does not observe DUT internal registers or tune expectations to observed behavior.

- T0 is the first active clock edge after reset. It starts a PWM period using the previously retained/reset command.
- `P=20000*CLK_HZ/1000000` cycles. This is integral for all tested clocks.
- For bounded command `a`, `W=500+floor((2000*a+MAX/2)/MAX)` microseconds.
- Pulse length is `ceil(W*CLK_HZ/1000000)` clock intervals. The model compares output on every edge, after a 1 ns NBA settle delay.
- At period boundaries the prior command is used. A same-edge valid command only changes the following period. Valid commands elsewhere cannot alter the active pulse.
- Reset asserts between edges, in both high and low phases, with active angle/valid inputs. Output is checked before the next clock edge. Release occurs on a falling test clock edge; this test does not verify a hardware reset synchronizer.

All instances use a 10 ns test clock to reduce testbench complexity. `CLK_FREQ_HZ` controls required **edge counts**, and the CSV records cycle indices. Thus this proves configured ratios/counts, not physical 61.44 MHz clock generation or a 20 ms simulator-time pulse period. Converting 1228800 edges at the actual 61.44 MHz gives 20 ms. Physical clock correctness remains a separate board/STA concern.

An additional integer-frequency miter compares outputs on every edge against a copy of the exact frozen original, with only the module name changed. It is compatibility evidence, not the independent timing model. The runner records the source and copy hashes.

Stimulus: deterministic seed 17010; reset with active inputs, a startup-edge command, commands immediately before and exactly at a period boundary, within high/low pulse phases, and 100 consecutive valid commands with varied 9-bit values. Cases cover 1/50/100 MHz and 61.44 MHz; MAX 1/360/511; reset lower/mid/upper endpoints. The 360-degree case tests 500, 1500, 2500 and 506 us. At 61.44 MHz these are 30720, 92160, 153600 and 31089 edges.

Canaries run in separate output directories: invert one scoreboard observation, invert one legacy-miter observation, or invert the async-reset observation. They must trigger their specific fatal marker. No product source mutation or waived checker is used in the normal run. Illegal parameter jobs must report the expected parameter assertion and never `INVALID_NOT_REJECTED`.

Limits: the finite stimulus is not exhaustive all-angle/formal proof; no reset-metastability, clock jitter or analogue PWM model; no full-top stubs. Native XSim only, not ModelSim/Questa or a desktop BAT entry-point claim. The installed BAT wrappers returned 1 without output; the local runner supplies observed vendor-library/Tcl paths to the official native tools only for the child process. Initial tool-environment failures remain in separate run folders.
