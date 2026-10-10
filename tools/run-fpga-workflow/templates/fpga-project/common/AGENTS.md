# FPGA project instructions

## Stable project identity

- Project: `__PROJECT_NAME__`
- Product top: `__TOP_MODULE__`
- Simulation top: `__SIMULATION_TOP__`
- Vendor: `__VENDOR__`
- Tool/version: `__TOOL__ __TOOL_VERSION__`
- Device/package: `__DEVICE__ __PACKAGE__`
- Canonical launcher: `__CANONICAL_PROJECT_ENTRY__`
- Formal entry points: `project/script/run.bat`, `simulation/script/run.bat`, `linter/script/run.bat`
- Long-term protected boundaries: none recorded; add only project-stable restrictions here.

This identity block reduces discovery cost. It is not an all-purpose task or
authorization card. Each new request supplies a live task delta; ordinary
follow-ups update the snapshot and impact cone without rewriting identity.

- Treat project specifications, target files, constraints, register sources, and current reports as authoritative.
- Use one product-source writer per checkout and keep review roles read-only.
- For synchronous changes, reason from pre-edge state through RHS evaluation, NBA commit, combinational settling, and the next sampling edge.
- Preserve latency, throughput, backpressure, data/sideband alignment, reset, flush, abort, and error behavior unless the approved contract changes them.
- Put formal vendor build state under `project/par`, formal ModelSim/Questa state under `simulation/work`, and Codex-created diagnostic variants under `codex_out`; never commit vendor databases or fabricated vendor models.
- Keep generated standard directories canonical: `project/`, `project/par/`, `project/script/`, `simulation/`, `linter/`, `release/`, and `codex_out/`. Do not create numbered variants such as `project2`, `par2`, or `script2`.
- Keep visible script roots clean. `project/script` contains `run.bat`, `setting.bat`, `src_list.txt`, and one confirmed vendor Tcl/CLI flow. `simulation/script` contains exactly `run.bat`, `setting.txt`, `src_list.txt`, and `vsim.do`. Generated exports, `modelsim.ini`, `.Xil`, libraries, logs, and waves stay under `simulation/work`.
- Run only project-confirmed commands. Unexecuted checks are `NOT RUN`; missing or unread evidence is `UNVERIFIED`.
- Keep smoke compile/elaborate/run evidence lightweight and label it `DIAGNOSTIC_ONLY`; activate full simulation, formal, CDC/STA, or release gates only for claims that depend on them.
- When this scaffold becomes a formal target, create one real depth-0 launcher at `project/par/__PROJECT_NAME__.xpr`, `.pds`, or `.al`. Do not place it below `par/vivado_project`, `par/build`, or a random job directory, and do not fabricate a marker before target facts are confirmed.
- Configure a tool root or vendor environment and invoke canonical commands through the BAT process PATH. Do not hard-code absolute executable files or persist PATH changes.
- Reuse matching managed IP, incrementally regenerate missing products, or stage/import copied configuration after source-view ownership checks. New IP uses the installed same-version official Tcl/CLI; official GUI automation is a one-time fallback followed by an exported recipe. Never copy online IP configuration into the product or use an approximate stub in a formal list.
- Power is NOT APPLICABLE unless an explicit request or real power, thermal, safety, or release budget activates it.
