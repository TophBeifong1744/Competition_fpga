# sat_add isolated simulation package

Read REPORT.md for actual outcomes and evidence. contract.md specifies behavior; sat_add.sv is the corrected module; tb_sat_add.sv is the independent self-check; case.json is the runner manifest. Original first failure is immutable evidence at runs/01_original; passing replay at runs/02_fixed; sensitivity failures at runs/03_mutant_x and runs/03_mutant_z. Source snapshots and logs are kept in every run.

To reproduce, use the commands in commands.txt but supply a NEW output directory for each invocation. Existing output directories are intentionally rejected by the runner. Main case expects PASS_SIMULATION; mutants expect FAIL_SIMULATION. No synthesis or hardware claim follows from these results.
