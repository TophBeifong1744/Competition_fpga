---
name: pynq-overlay-dma-validation
description: Validate a PYNQ Overlay and its versioned AXI4-Lite/AXI DMA contract, from portable offline artifact checks through real-board loopback, golden-reference, performance, and resource evidence. Use for PYNQ/Zynq project acceptance or DMA failure diagnosis; do not use mock or static results as proof of board operation.
---

# PYNQ Overlay DMA Validation

Use a project-supplied JSON profile as the single source of board identity, Overlay artifacts, register semantics, DMA geometry, self-tests, golden-reference rules, and acceptance limits. Never infer these values from a project name or hard-code a particular board, address, transfer length, or payload format.

## Select the mode

- **Offline mode:** validate the profile, `.bit`/`.hwh`/manifest relationship, HWH-visible IP, register layout, DMA length/alignment/cache/TLAST contract, supplied evidence, golden results, and resource/performance limits. Static or mock evidence can establish only offline readiness.
- **Board mode:** first pass offline mode, then load the matching Overlay on the declared PYNQ board, read identity registers, run bounded DMA loopback/self-tests, execute required cache operations, capture timeouts/status, compare golden output, and validate the resulting hardware evidence.

Read [references/profile-contract.md](references/profile-contract.md) before creating or changing a profile. Read [references/hardware-runbook.md](references/hardware-runbook.md) before board mode or when diagnosing a failed transfer.

## Required inputs

1. A version-controlled profile conforming to `references/profile-contract.md`.
2. A `.bit`, `.hwh`, and build manifest produced by the same build; the manifest records hashes, device/board identity, Vivado version, build ID, and interface version.
3. The authoritative AXI4-Lite register contract and DMA stream contract.
4. For board mode, a supported PYNQ image, reachable board, valid DDR path, and a deliberately bounded loopback/self-test design.
5. Golden vectors or an exact loopback rule, acceptance thresholds, and Vivado timing/resource reports when those claims are requested.

Do not guess absent contract values. Mark them unresolved and stop before downloading or writing hardware.

## Workflow

1. Copy `references/example-profile.json` and replace every example value with project evidence.
2. Run `python scripts/validate_profile.py --profile <profile.json> --mode offline --output <offline-report.json>`. Resolve every `ERROR`; retain warnings and report hashes.
3. Confirm the board profile against physical/device-tree evidence and confirm that `.bit`, `.hwh`, manifest, PYNQ image, and Vivado/PYNQ compatibility belong together.
4. On the board, run `python scripts/pynq_probe.py --profile <profile.json> --download --output <hardware-evidence.json>`. This performs read-only identity checks and only the self-tests explicitly declared in the profile.
5. For a transformed data path, run `python scripts/compare_golden.py --expected <golden> --actual <capture> --format bytes --output <golden-report.json>`; use `json-numbers` plus explicit `--atol/--rtol` only when the payload contract permits tolerance.
6. Validate board evidence with `python scripts/validate_profile.py --profile <profile.json> --evidence <hardware-evidence.json> --mode hardware --output <hardware-report.json>`.
7. Archive the profile, manifest, reports, evidence JSON, raw/golden hashes, commands, and environment versions together. State the strongest evidence level actually reached.

## Evidence levels

- `static`: schemas, hashes, HWH metadata, contracts, and reports inspected without executing transfers.
- `mock`: deterministic synthetic data exercised host-side logic without a PYNQ board.
- `hardware`: the declared physical board loaded the declared Overlay and produced recorded register/DMA observations.

Higher levels do not erase lower-level failures. PYNQ display output does not prove RTL simulation, timing closure, CDC correctness, or sustained physical-input continuity.

## Outputs

- Machine-readable validation report with `PASS`/`FAIL`, evidence level, artifact hashes, checks, warnings, and stop reasons.
- Board evidence JSON containing observed board identity, Overlay load state, register reads, cache operations, DMA completion/TLAST/error/timeout data, mismatch counts, and measured transfer timing.
- A concise acceptance summary separating offline checks, real-board results, golden comparison, performance, timing/resources, and unresolved boundaries.

## Stop conditions

Stop without Overlay download or register writes when any of these holds:

- `.bit`, `.hwh`, or manifest is missing, mismatched, unhashed, or names a different device/build/interface.
- Board identity, full device part, PYNQ image/support, DDR/DMA path, register semantics, or safe self-test route is unresolved.
- Register offsets overlap, violate alignment/range, or identity expectations are absent.
- DMA length violates beat/alignment/max-transfer limits, cache ownership is undefined, or required TLAST has no producer.
- The planned test could drive an unverified physical output, overwrite live buffers, or disturb a real-time acquisition path.

During board mode, stop the current test on timeout, DMA error, missing TLAST, identity mismatch, cache-operation failure, or golden mismatch. Capture status before any reset. Do not escalate to a whole-PL reset automatically; recovery must be authorized by the project contract.

## Backend boundary

PYNQ is a control and validation backend, not part of the real-time PL algorithm. Keep AXI4-Lite, AXI DMA, interrupts, vectors, and evidence formats backend-neutral so the same contract can be driven by Vitis or PetaLinux when PYNQ does not pass the board admission gate.
