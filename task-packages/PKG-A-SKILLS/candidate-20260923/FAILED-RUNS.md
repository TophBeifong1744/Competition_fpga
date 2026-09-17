# Preserved author-run setup failures

## run01 install-copy step

The first isolated run completed SKL-001 XSim and SKL-002 offline/static/mock
tests, but the final temporary install-copy command used `Copy-Item
-LiteralPath` with a wildcard. PowerShell correctly treated `*` literally and
stopped because that path did not exist. A second attempt exposed the separate
Windows case-insensitive rule that `skill.md` cannot be copied over itself as
`SKILL.md`.

This was a test-orchestration mistake, not a Skill behavior failure. No source
or evidence was overwritten. The correction was to enumerate directory items
explicitly and perform the case-only rename through an intermediate filename.
Both structure checks then returned `Skill is valid!`. Because the candidate
source was tightened afterwards, the final evidence comes from a completely
new `run02` directory rather than reusing run01 results.

## run02 board-guard expectation record

All run02 behavior completed, but the orchestration initially expected board
guard exit code 2 by copying a historical review statement. The approved
`pynq_probe.py` actually raises `SystemExit` with a string, for which CPython
returns 1. The raw stderr contained `BOARD_RUNNER_NOT_QUALIFIED`, the requested
output did not exist, and the existing unit test requires only a nonzero exit.
The execution record was corrected to the observed/contractual exit code 1;
the probe source was not changed and no behavior test was rerun or relabeled.
