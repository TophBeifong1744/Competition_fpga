## 0.5.0 — 2026-10-13

System-first S1–S6; outcome-based staffing independent of headcount; shared budgets and integrated results; context-independent major reviews; direct board cadence; minimal-purpose retention; governed file/branch cleanup.

## 0.4.7 — 2026-10-11

Plan interface joins, ILA and first/subsequent board checkpoints at dispatch; batch small fixes and retain direct board validation for board-discovered fault repairs.

## 0.4.6 — 2026-10-11

Board-discovered faults: skip simulation after repair and prioritize affected on-board validation; retain build, timing and safety checks.

## 0.4.5 — 2026-10-10

Integration-first delivery and capability-aware half/full-host CPU utilization; active runs remain unchanged.

# Local adaptation 0.4.4 — 2026-10-10

Simplified active workflow and profiles: direct delivery/integration/testing and merge-or-repair; major-module independent judgment; complete engineering ZIP. Historical entries below are not additional active gates. CLI/schema/13 roles unchanged.

<!-- Current local adaptation 0.4.3 / SS-PROJECT-ZIP-20261010-3: Vivado/Vitis milestone ZIP and major-module review. Earlier version notes below are historical. -->

<!-- Local adaptation 0.4.2; patch SS-STAGE-20261010-2. Whole-stage execution supersedes intermediate review cadence below; upstream remains 0.4.0. -->

# Changelog

## 0.4.1 - 2026-10-10 (local adaptation candidate)

- Based on upstream 0.4.0 at e40fd8000b526b72ba80373127bf5fd6e5f8dc28; not an official upstream release.
- Ordinary QUICK uses bounded sequential implementation/self-test and one qualified non-author acceptance; preserve FULL/high-risk obligations.
- Human checkpoints, ILA raw evidence and incremental integration; additive BOARD_FUNCTIONAL stage.
- Keep 13 roles, three evidence profiles, independent sign-off, safety and bounded repairs.


All notable changes follow Keep a Changelog. Versions follow Semantic Versioning.

## [0.4.0] - 2026-08-28

### Added

- Added stable project identity plus live task deltas so follow-up requests can supplement, supersede, expand, or narrow the current task without repeating machine-wide discovery.
- Added structured task authorization, protected work, requested claim, claim stages, role modes, and board boundaries while preserving backward-compatible task-contract authorization strings.
- Added five conditional `fpga_engineer` modes: RTL implementation, official IP integration, build flow, physical implementation, and release packaging.
- Added the official-IP decision flow and IP proof packet schema covering managed reuse, incremental regeneration, source-view-safe staging/import, installed official Tcl/CLI, and GUI-once fallback.
- Added evidence-triggered physical implementation guidance with baseline freezing, path classification, one-primary-variable experiments, and keep/revert comparisons.
- Added `README.zh-CN.md` and complete `docs/zh-CN/` navigation for architecture, roles, installation, usage, and safety/evidence.

### Changed

- Scoped verification, CDC/STA, physical QoR, formal, release, and final review through `claim_stage` without creating a competing evidence-profile system.
- Made power `NOT APPLICABLE` by default unless a real power, thermal, safety, or release claim activates it.
- Narrowed final review to integrated contract/snapshot/specialist evidence, conflict resolution, blocking findings, and highest-risk sampling instead of repeating every specialist's full traversal.
- Standardized generated `simulation/script` to exactly `run.bat`, `setting.txt`, `src_list.txt`, and `vsim.do`. Generated exports, libraries, logs, waves, and `.Xil` remain in `simulation/work`.
- Simplified generated `project/script` to the build BAT, project setting, canonical source list, and one confirmed vendor Tcl/CLI flow.
- Updated English landing pages and guides with live identity/task behavior, official IP responsibility, writer modes, claim stages, and physical implementation boundaries.

### Validation

- Parsed all 13 role TOMLs, 11 workflow JSON schemas, and package PowerShell scripts.
- Exercised task-contract valid/invalid claim-stage cases and a valid official-IP proof packet.
- Exercised the project scaffold with stable identity, a direct canonical launcher path, three visible build-script files, and four visible simulation-script files.
- Kept real Xilinx/ModelSim execution evidence from 0.3.2/0.3.3 as diagnostic toolflow evidence; this release does not claim new DUT, Pango, Anlogic, timing-closure, bitstream, or board validation.

## [0.3.3] - 2026-08-27

### Changed

- Required normalized vendor launchers to be depth-0 files at `project/par/<project-name>.xpr`, `.pds`, or `.al`, with same-name vendor databases as direct siblings.
- Rejected newly generated `par/vivado_project`, `par/build`, and random project containers as canonical output while preserving foreign nested projects as import sources until normalization is requested.
- Removed machine-specific absolute executable files from the formal runtime contract. Generated BAT adapters now configure a tool root or vendor environment, modify only their process PATH, verify canonical commands, and invoke them by name.
- Updated architecture, implementation, vendor-platform, and final-review gates plus scaffold metadata and public documentation.

### Validation

- Confirmed a Vivado 2020.2 canary creates `project/par/direct_par_canary.xpr` at depth 0 with direct sibling native databases.
- Confirmed scaffold metadata reports the exact canonical launcher path without fabricating an empty project marker.

## [0.3.2] - 2026-08-27

### Changed

- Replaced generated-project PowerShell runtime wrappers with pure `%~dp0`-anchored BAT entry points and deliberately fail-closed native adapter placeholders.
- Separated formal vendor build state in `project/par` and formal ModelSim/Questa state in `simulation/work` from Codex-only diagnostics under `codex_out`.
- Added GUI-by-default and batch simulation semantics, plus explicit real-simulator compile/load/run evidence requirements.
- Documented the Windows Vivado/ModelSim export edge case where `export_simulation` emits `.sh + compile.do`, including parent-library creation, local `modelsim.ini` correction, nonzero compile exits, and no load after compile failure.
- Updated the architect, implementation, verification, vendor-platform, and final-review roles to enforce the native desktop entrypoint contract without applying Xilinx-specific commands to unverified Pango or Anlogic tools.

### Validation

- Exercised a BAT-driven Vivado 2020.2 synthesis checkpoint and a BAT-driven ModelSim SE-64 2020.4 compile/load/2 us diagnostic run on an isolated non-shipped fixture.
- Kept remaining DUT/IP/constraint/timing warnings outside the script repair scope and made no product-RTL acceptance claim.

## [0.3.1] - 2026-08-26

### Changed

- Made governance proportionate with separate diagnostic/smoke and claim-specific acceptance profiles while preserving one-writer, no-self-sign, evidence-integrity, failure-ownership, CDC, and electrical-safety gates.
- Added brief pre-edit reasoning for user-requested minimal source changes without introducing redundant approval pauses.
- Assigned formal-evidence acceptance to the existing independent FPGA reviewer only when formal proof is part of the requested acceptance claim.
- Standardized generated projects on `project/`, `project/par/`, and `project/script/` with no numbered variants, and moved optional PowerShell helpers under clean `script/ai_run/` directories.
- Improved the English landing page and guides with a clearer value proposition, one-click project experience, evidence profiles, honest limitations, and adoption guidance.

## [0.3.0] - 2026-08-26

### Added

- Added the shadow-only, strictly read-only `fpga_temporal_evidence_reviewer` for bounded cycle and simulation-evidence review.
- Added stable workflow artifacts, Model Cards, findings-ledger convergence, simulation-failure classification, and hard repair-loop stops.
- Added deterministic Xilinx/Pango/Anlogic detection, RTL/IP/TB file-list generation, preflight, official-library recipe hooks, and a clean formal-project scaffold.
- Added a private after-sales fault-library schema and empty/config/query hook without shipping private data.

### Changed

- Standardized generated Codex process output beneath project-root `codex_out`.
- Expanded English documentation with formal directory structure, one-click `run.bat`, temporal evidence, model independence, and local-first shadow rollout.
- Updated package/install validation for 13 roles: 10 strict read-only roles and 3 potential sequential writers.

## [0.2.0] - 2026-08-24

### Changed

- Made `README.md` the sole canonical English landing page.
- Added a GitHub-focused hero, status badges, quick start, architecture overview, complete role table, use cases, limitations, and adoption calls to action.
- Expanded the English architecture, roles, installation, usage, and safety/evidence guides.
- Normalized the FPGA architect's output headings and improved public terminology.
- Updated package validation to derive the plugin version from `VERSION`, require the English documentation set, and reject CJK text or stale localized-document references.

### Removed

- Removed the duplicate English README and localized documentation copies in favor of one maintainable English documentation path.

## [0.1.0] - 2026-08-24

### Added

- Twelve FPGA/SoC FPGA roles with explicit read/write boundaries.
- ANALYZE, QUICK, and FULL workflow modes.
- Stable-diff checkpoint supervision, isolated EDA evidence, and independent sign-off.
- User/project installation, verification, validation, and safe uninstallation scripts.
- Initial bilingual documentation, prompts, research ledger, and contribution templates.
