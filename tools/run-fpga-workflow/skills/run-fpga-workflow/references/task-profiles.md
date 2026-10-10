# FPGA task profiles

Load only the relevant profile.

## Datapath or FSM

Define ports, throughput, latency, backpressure, buffers, precision, overflow/saturation, illegal-state recovery, and unchanged boundaries. Freeze an impact cone and cycle contract. For pipeline/FSM/FIFO/RAM changes, run the temporal reviewer in shadow mode against one bounded clock-domain cone. Acceptance includes directed boundaries, reset, random backpressure, a cycle-indexed checker, and synthesis/STA when structure or target timing may change.

## Registers, commands, IRQ, or DMA

Find the single register source. Review address units, alignment, width, endianness, byte enables, reset values, RO/RW/W1C/RC/self-clear, reserved bits, side effects, versioning, and atomic snapshots. Explicitly define W1C concurrent-event priority, IRQ raw/status/mask/clear/reassert, and DMA alignment/boundaries/ownership/cache/backpressure/abort/recovery. Do not hand-edit duplicated generated views.

## CDC, reset, or timing

Use CDC/timing and verification pre-review; add vendor/board review for clock primitives or external clocks. Match crossing type to synchronizer, handshake/toggle, stable multi-bit protocol, Gray counter, or async FIFO. Check reconvergence, reset release, pulse visibility, data stability, attributes, MTBF assumptions, generated clocks, I/O delays, and narrow exceptions. Structural and constraint correctness require separate evidence.

Select only the required mode: `CDC_STRUCTURE`, `STA_COVERAGE`,
`PHYSICAL_QOR`, or `TIMING_CLOSURE`. An async FIFO with missing clock or
constraint evidence may have a valid structure while timing coverage remains
UNVERIFIED; do not call that a DUT failure. Compile/smoke does not trigger full
P&R. Power is NOT APPLICABLE by default.

## Official IP integration

The writer uses `IP_INTEGRATION` and the vendor reviewer audits the result.
Start with `IP_DISCOVERY`: reuse a matching managed IP, regenerate missing
products, stage/import copied or legacy configuration, use confirmed official
Tcl/CLI, or plan GUI-once. Only `IP_INTEGRATION_ACCEPTANCE` requires the full
IP proof packet, OOC, constraints, simulation model, and canonical-project
reopen. Internet sources provide official documentation and examples, not
product IP configuration files to copy.

## Physical implementation

Use only for `IMPLEMENTATION_QOR`, `TIMING_CLOSURE`, or real routed evidence.
Freeze a baseline, classify logic/route/fanout/congestion/clocking/
RAM-DSP-GT-IO/constraint root cause, change one primary variable, rerun, and
keep or revert from comparative evidence. Do not default to seed/strategy,
whole-design Pblocks, repeated phys-opt, replication, or pipeline insertion.
Power remains NOT APPLICABLE unless a real budget or claim activates it.

## Multi-vendor platform

Keep product behavior in common RTL. Wrap PLL/clock/I/O/SERDES/delay/RAM/FIFO/DDR/transceiver/boot/debug and target constraints. Select portable or vendor-optimized implementations by target, not scattered conditionals. Each target needs exact device/tool/IP data, an independent build/report row, and equivalence tests.

Automatic scripts support only Xilinx (`.xpr`/`.xci`), Pango (`.pds`/`.idf`), and Anlogic (`.al`/marked `.ipc`). Conflicts and other vendors fail closed. A generated standard project contains exactly one adapter and one `codex_out` output root.

## Board or high-energy output

Require exact manuals/schematics and safe defaults before physical steps. Separate simulation, static implementation evidence, instrument capture, unloaded tests, and controlled load tests. Wiring, power-up, movement, heat, laser, relay, high voltage, and energy enable are USER ACTIONS with prerequisites, stop conditions, and recovery.

## File ownership

- Product RTL/constraints/wrappers/build/regmap implementation, official IP configuration/recipes, physical changes, and explicitly authorized release packaging: `fpga_engineer` only, one primary mode per batch.
- Firmware/drivers: `embedded_engineer` in a later sequential batch.
- Testbench/assertions/reference models: ordinary bounded QUICK permits `fpga_engineer` in a later self-test phase of the same execution context; otherwise `verification_engineer` in a later sequential batch. Their author never independently signs the changed acceptance assets.
- Reviews: read-only; reviewers never fix findings.
- EDA output: formal vendor build state uses `project/par`; formal ModelSim/Questa state uses `simulation/work`; Codex-created diagnostic variants use unique ignored `codex_out/<run-id>/...` directories. Never commit vendor databases or generated IP.

## Human checkpoints and scoped board integration

Read [human checkpoints and ILA](human-checkpoints-and-ila.md) for useful human simulation/synthesis/implementation/board nodes. Human operations capture critical screenshots plus native reports and raw samples. Before handoff, complete the checks relevant to the next operation or disclose unavailable checks; static inspection alone is not a usability guarantee.

A bounded board-behavior claim uses SPECIALIST_ACCEPTANCE and local BOARD_FUNCTIONAL, with independent acceptance expectations, matched bit/LTX and relevant software artifacts, known stimulus, observation-window limits, and accessible raw captures. Preserve necessary electrical/clock/CDC/STA prerequisites. After scoped pass and required non-author acceptance, integrate into the overall project within existing authority and recheck affected combined interfaces and implementation evidence. Do not wait for unrelated documentation or claim whole-system acceptance.

## Minimum sign-off evidence

Requirements and unknowns are explicit; user changes are protected; integrated diff is reviewable; affected tests have real results; CDC/RDC, synthesis, implementation, and STA are present when affected or clearly UNVERIFIED; interfaces agree across domains; high-energy actions retain a human safety gate.
