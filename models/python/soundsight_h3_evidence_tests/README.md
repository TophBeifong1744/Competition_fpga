# Independent saved-evidence producer tests

Read EXPECTED.md first. Product is read-only; no product helper generates expectations.
Standard library only. From this checkout's models/python:

```text
python -B -m soundsight_h3_evidence_tests.make_cases --inputs <frozen-inputs> --out <new-cases>
python -B -m soundsight_h3_evidence_tests.runner --cases <cases> --out <new-runs>
```

Each case has a frozen expected.json before any DUT run. Runner uses the authoritative
producer CLI and a separate independent checker process, preserving commands, cwd,
stdout/stderr, exit codes and first failing case. It continues only through this bounded
case list to record neighboring boundaries; its overall exit is nonzero on any failed check.
Run saved_file first, then the rest. --case selects one or more IDs. --fail-step records
a controlled child exit17 and returns nonzero; that is a runner canary, not a DUT failure.

The injected_post_failure case calls real main after a controlled post-check exception;
it is labeled INTERNAL_INJECTION. Other cases are subprocess module CLI executions.
Generated synthetic bytes are explicit test fixtures, not old native execution.
Artifact hashes are checked after semantic assertions so output mutations can prove
the intended checker assertion, rather than merely tripping an unrelated hash guard.

New oracle/checker assets need review by a person/agent who did not participate in their
creation. No FUNCTIONAL_ACCEPTANCE, production, mathematical-V or real-member acceptance
is conferred by this batch. See the output DELIVERY and index for actual coverage/omissions.
