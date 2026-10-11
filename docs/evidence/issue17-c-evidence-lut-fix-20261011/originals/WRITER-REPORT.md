# C-EVID-LUT-001 — bounded writer handoff

Candidate: `project/rtl/c_board/i17_vio_evidence.sv` SHA256 `135271131d893eba2b8e22a7b596c78292de4050a69855f131b5fe5a582fdfd6`. Reviewed parent: `d6b7096d55bdcc44ff275bdad2b208c25092ad6e9668aff4edcd83dcac76fc6a`. Author checks complete; independent acceptance pending.

| Evidence | Before | After | Delta |
|---|---:|---:|---:|
| Isolated synthesized logic LUT | 20546 | 6546 | -14000 |
| Isolated total LUT | 20634 | 6634 | -14000 |
| LUT memory | 88 | 88 | 0 |
| Flip flops | 10489 | 10509 | 20 |
| F7 / F8 mux | 1943 / 694 | 2271 / 750 | 328 / 56 |

Scope/assumptions: only `word_for` and its purpose comments changed. It now selects a padded 32-bit word within each record before selecting record kind. For each definite kind/index, original record padding gives zero beyond its length; explicit guards preserve those zeros. Record5 retains all64 raw memory words regardless of captured length. Unknown kind uses default0; X/Z index makes guarded `if` nontrue, preserving0. Payload X/Z bits remain selected exactly. All non-function source bytes are identical.

Behavior/latency/throughput: no cycle contract delta; registers, handshake, release, STOP/error behavior, LSW-first fields and ILA layout unchanged. Clock/reset/CDC/RDC: no change. Register/IRQ/DMA: no interface change. Vendor/target: same xc7z020clg400-1 and Vivado2025.2; no IP or constraint changes to product.

Evidence: native XSim completed 409600 independent bit-addressed oracle plus old-function differential checks across16 kinds,256 indices, four data patterns and X/Z guards/payloads. Public READ exercised6656 transactions; extended original transaction TB completed29178 checks and7772 cycles of all19 output differential comparison. This includes raw reads after release, diagnostic stale data after a long then short capture, uninitialized word63, all padding/invalid indices, live READ and frozen live DUMP. CANARY_DATA deliberately corrupted terminal word17 and triggered DATA_CHECK at787ns. XSim returns0 even on that fatal. The runner actually accepts any log containing `Fatal: DATA_CHECK`; this run's independent review verified the exact first failure at kind3/word17 and no success completion. LOW C-EVID-LUT-SH-001 records the runner-hardening follow-up; no RTL/TB changes or test rerun were made. Positive cases require completion and no fatal.

Resource evidence: two identical-option single-module OOC syntheses completed with process exit0; logic LUT reduction 68.14%. Reports are `synth_before/utilization.rpt` and `synth_after/utilization.rpt`. Full-design old optimized u_evidence=20044 logic LUT is a different context and must not be mixed with these isolated counts. Warnings retained: unused dump_seq removed, constant error bits, diagnostic period rounded to1ps. Restricted launches initially failed at mkdir before synthesis; retained attempt logs identify that environment failure. No product repair was made for it.

Unverified/risks: these results do not prove whole-design fit, routed timing, board function, or repair C-AB-CTRL-001 STARTUP_BLOCKED. No full synth, implementation, download, IP generation, or native D project/source writes occurred. D source still `d6b7096d55bdcc44ff275bdad2b208c25092ad6e9668aff4edcd83dcac76fc6a`. Existing task packages and untracked sound_servo_clock.sv were protected.

Handoff to review: review `product.diff`, `product-freeze.json`, this exact candidate and `run-manifest.json`/native logs. After acceptance, a separate authorized single-file integration may copy these exact bytes into the existing D import path. Human full synthesis and implementation must save the fresh utilization/timing/DRC/logs; old DCPs are not candidate evidence. No bitstream/board step is approved by this handoff.
