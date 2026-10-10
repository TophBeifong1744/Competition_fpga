# Compatibility

> Local adaptation candidate 0.4.1, based on upstream 0.4.0 at e40fd8000b526b72ba80373127bf5fd6e5f8dc28. Not an official upstream release. See ADAPTATION.json and the paired team package. No installation, FPGA execution or ILA capture was performed.


Local candidate package version: **0.4.1** (upstream baseline **0.4.0**)

## Package format

This release uses Codex plugin discovery through `.codex-plugin/plugin.json`, custom agents under `.codex/agents/`, and the canonical plugin skill under `skills/run-fpga-workflow/`. The installer deploys that skill to `.agents/skills/run-fpga-workflow/` for user or project use.

## Environment exercised on 2026-08-24

- Codex CLI: 0.147.0
- PowerShell: 7.6.4
- Git: 2.54.0.windows.1
- Operating system: Windows

Static package validation is included. The helpers support vendor detection for AMD/Xilinx Vivado, Pango PDS, and Anlogic TD; exact EDA commands and official libraries remain local project/tool-version facts. The native-runtime contract was exercised on Windows with Vivado 2020.2 and ModelSim SE-64 2020.4 using an isolated, non-shipped FPGA fixture. A separate Vivado canary confirmed a depth-0 `project/par/<name>.xpr` with same-name direct sibling databases. Version 0.4.0 statically validates live project/task contracts, writer modes, claim stages, official-IP packet shape, bilingual documentation, clean script roots, and process-local command-name runtime. Fresh-session behavior, Pango/Anlogic generation, every licensed vendor flow, DUT function, physical QoR, timing closure, bitstream, and board results remain target-specific and UNVERIFIED until exercised.
