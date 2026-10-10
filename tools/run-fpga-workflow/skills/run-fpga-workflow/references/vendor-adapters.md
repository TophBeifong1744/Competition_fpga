# Three-vendor adapter contract

Automatic selection is intentionally narrow.

| Evidence | Vendor |
|---|---|
| `project/par/*.xpr` | AMD/Xilinx Vivado |
| `project/par/*.pds` | Pango PDS |
| `project/par/*.al` | Anlogic TD |
| fallback `*.xci` | AMD/Xilinx |
| fallback `*.idf` | Pango |
| fallback `*.ipc` containing Anlogic, TD, or EG-family text | Anlogic |

Ignore `codex_out`, `release`, backups, old copies, and generated tool databases. Two detected vendors are `VENDOR_CONFLICT`; an Intel/Quartus or Lattice project marker is `UNSUPPORTED_VENDOR`; no evidence is `UNKNOWN_VENDOR`. All three fail closed and ask the user rather than choosing by file count or timestamp.

A formal generated project contains only one selected vendor flow. `project/script/src_list.txt` carries product HDL, include entries, and selected official IP configuration paths relative to the actual build run directory. `simulation/script/src_list.txt` carries project RTL, explicit simulation models, and TB order relative to the actual simulator run directory; managed vendor IP models may come from the official export. Dependency-sensitive source sets require authoritative optional order files under `document/`; the helper does not infer arbitrary vendor order. Formal build state goes under `project/par`; formal ModelSim/Questa state goes under `simulation/work`; Codex diagnostics go under `codex_out`. Commands preserve exact exits and never modify global PATH, registry, simulator mappings, or source files. A zero tool exit is command completion, not FPGA acceptance.

An official simulation-library recipe may run only for an exact, tested vendor/tool/family/simulator tuple. Codex-built cache libraries use a source-hashed key below `codex_out/_cache/simlibs`; a confirmed user-maintained compiled library may remain at its established location and be referenced only through a local simulator mapping. Without a recipe or official source, return `MISSING_VENDOR_LIBRARY` with a preparation checklist. Never fabricate a behavioral primitive or substitute a nearby version.

Generated-project desktop runtime uses `%~dp0`-anchored BAT plus confirmed vendor-native Tcl/DO/CLI. It must not require a `pwsh.exe` visible only inside Codex. Build defaults to a bounded compile checkpoint. Simulation defaults to the configured GUI and the same BAT supports `batch`. For Xilinx plus ModelSim/Questa, generate IP output products, export IP user/static files, inspect the actual Windows export artifact, and use a job-local `modelsim.ini`. Vivado can emit `.sh + compile.do` rather than `compile.bat`; the Windows wrapper must create required parent libraries, invoke the emitted compile DO, propagate compile failure, and never continue to load/run after that failure.
