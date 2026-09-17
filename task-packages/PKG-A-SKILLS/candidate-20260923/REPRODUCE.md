# Reproduce the 2026-09-23 candidates

The recorded run used Windows, Python 3.12.14 for behavioral tests, Python
3.14.6 with PyYAML for structure validation, and Vivado/XSim 2025.2. Copy
`exports/` into a new English-only path with no spaces; do not run inside or
overwrite the approved activity directories.

## SKL-001

From `fpga-module-verification/`:

```text
python -B -m unittest discover -s tests -v
python -B scripts/run_examples.py --vivado-bin F:/AMD/2025.2/Vivado/bin --output ../evidence/skl001-xsim
```

The second command exits 0 only if PCM4 and elastic pass, all three disposable
mutants fail at the simulation stage, and the restored source passes. Every
case creates a source snapshot, command/return-code record and full stage log.

## SKL-002

From `pynq-overlay-dma-validation/`:

```text
python -B scripts/run_offline_tests.py --output ../evidence/skl002-offline.json
python -B scripts/validate_receive_profile.py --profile references/example-receive/receive-profile.json --output ../evidence/skl002-receive-pass.json
python -B scripts/replay_receive_cases.py --profile references/example-receive/receive-profile.json --output ../evidence/skl002-receive-cases
python -B scripts/simulate_dma.py --contract references/example-session.json --output ../evidence/skl002-mock-receive.json
```

Expected lifecycle failures use fresh output names and must exit nonzero:

```text
python -B scripts/simulate_dma.py --contract references/example-session.json --fault rx-invalidate-noop --output ../evidence/skl002-stale-cache.json
python -B scripts/simulate_dma.py --contract references/example-session.json --fault short-output --output ../evidence/skl002-short-output.json
python -B scripts/simulate_dma.py --contract references/example-session.json --fault timeout --fault abort-timeout --output ../evidence/skl002-timeout-retained.json
python -B scripts/pynq_probe.py --profile references/example-receive/receive-profile.json --download --output ../evidence/forbidden-board-output.json
```

The last command must not create its requested output. No command in this
document authorizes board access.

## Install-name structure check

On the temporary install copy only, rename lowercase `skill.md` to `SKILL.md`,
then run the system Skill validator on each directory. The candidate export
itself remains lowercase for the contest path rule. See the recorded command
and outputs rather than treating this structure check as behavioral evidence.

All scripts refuse or should be given new outputs. Preserve a failed run as a
separate directory; never delete it and rerun under the same evidence name.
