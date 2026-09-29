# Independent offline evaluator assets

These synthetic evidence bundles and expectations implement the frozen r1 case
plan plus MAIN-DECISIONS-r2. They test the evaluator only. `make_cases.py`
creates bundles from independent source-frame schedules; `checker.py` checks
event identities, classifications, conservation, gates, and claim boundaries.
`runner.py` calls the product CLI and checker in separate processes and retains
raw logs under a new `codex_out` directory. It never runs hardware or audio.

The author of these assets cannot independently sign their final acceptance.
