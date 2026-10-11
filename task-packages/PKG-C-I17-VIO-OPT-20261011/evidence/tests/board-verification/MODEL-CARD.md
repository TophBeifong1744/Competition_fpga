# Board controller, evidence and gate model — 2026-10-10

Purpose: bounded functional checks of the new controller/storage/PWM isolation. No full-core, FFT, IFFT, audio, vendor IP, synthesis or board claim.

Independent requirements source: `../../delivery/board-task-contract.json`, frozen before test writing. Bit-field packing is the published `../BOARD-INTERFACE.md`; this supplies drive/decode mappings, not observed DUT behavior used to adjust expected results. C-VIO-STATIC-001/002 expectations were supplied by the independent reviewer/architect through the parent before dynamic reproduction.

The test environment drives public inputs for actual core events (ready, identity, busy, terminal and stored-report notifications). Those event schedules are test stimuli, not a replacement core implementation. No stub emits fake FFT/DOA success. `signed_angle_map.sv` is the actual frozen original module. Its numerical vectors do not claim correctness of source-direction estimation.

The native recovery sequence comes from frozen original `inputs/inputs/parent/rtl/forward_window_manager.sv`: lines41–43 define IDLE0, START_OFFER1, PREPARE_OFFER6, WAIT_RESET7, RESET_WAIT8, CLEAR_OFFER9; lines190–200 define the handshake progression and actual return to IDLE. Registered WARM becomes visible for the next core sampling edge. The old-IDLE check remains at that edge, followed by real states6/7/8/9 and return0; AXIS data still blocks completion even after the return.

Model repair disclosure: the original warm_race tail erroneously drove state1 as a prepare state. The repaired product correctly rejected old IDLE at cycle15 but stayed in recovery after that invalid simulated sequence. This is REFERENCE_MODEL_FAIL for the tail, not a second product failure. `tb_control-before-native-recovery-fix.txt` and `runs/warm_race-attempt2` preserve it. The original cycle15 expectation was unchanged. Control regression also received the actual 6→7→8→9→0 stimulus.

Scoreboards use explicit edge-indexed stimuli and check after NBA updates (`#2`). Control checks assert atomic COMMIT snapshots, true-ready wait, source-before-diag ordering, exact 725-bit identity, arm-before-permit, observe no authorization, STOP priority, no replay, recovery and explicit restart. They do not read DUT internal registers; exposed state is an interface observation.

Evidence checks construct expected records from pre-edge inputs and published layouts. The following edge's servo accept/angle is independently added to that saved record. Distinct deterministic bit patterns populate all725 identity bits,6626 terminal bits and180 abort payload bits. Every emitted DUMP word is compared, including tail padding and metadata sequence/type/index/count/last. The diagnostic producer holds words through ACK acceptance, inserts deterministic 0–3 edge stalls (seed17010), and checks exact ACK tuple with a low cycle between ACKs.

Cold reset and physical PWM checks operate between/at clock edges: reset forces low, explicit permit cannot open during high PWM, low-phase opening passes subsequent high, and withdrawing permit/STOP retains an already-open gate. These are digital gate semantics, not motor position or analogue pulse quality.

Canaries: corrupt the sampled context bit before the control snapshot comparison; corrupt terminal word17 before its data comparison. Separate run directories must catch CONTROL_CHECK and DATA_CHECK respectively. The nominal design and expected values remain unchanged. Native XSim may exit0 after `$fatal`; the runner checks fatal and completion markers as well as compile/elaborate exit codes.

Limits: finite directed schedules, not exhaustive formal proof. Diagnostic lengths1,2,7,63 are covered, not every possible length; sequence exhaustion and every abort/ACK overlap are not covered. Full official-IP integration and real core timing remain NOT RUN. The test author cannot sign these assets independently.
