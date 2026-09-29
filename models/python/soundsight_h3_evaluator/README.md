# SoundSight H3 offline evaluator candidate

This package consumes evidence. It does not run portable H3, select a target, infer
a hardware clock from `SYNTHETIC_TIME`, or measure audio SNR. It is an author
product candidate pending separate verification.

From the repository root on Windows:

```powershell
Set-Location models/python
D:/Python/python.exe -B -m soundsight_h3_evaluator --bundle F:/evidence/bundle.json --out F:/evidence/new-report
```

`--out` must be new. Exit 0 means a report was generated; it does **not** mean
PASS. Exit 2 means bad CLI or evidence structure, 3 means a reference/source
identity conflict, and 4 means an internal error or source drift. Failures retain
`failure.json` in the reserved output directory. The CLI never deletes an old
output. On success it writes `report.json`, `evidence-index.json`, `README.md`.

## Bundle V1

The input is a JSON object with `schema_version=EVIDENCE_BUNDLE_V1`,
`claim_scope` (`SYNTHETIC_TEST`, `DIRECTION_RUN`, `DIRECTION_CELL`, or
`P1_P4_BATCH`), `evidence_level`, `seal`, `policy_ref`, `preregistration`,
`runs`, and `references`. Each relative reference has `id`, `path`, `bytes`,
`sha256`, `role`, and `producer`. The CLI checks raw bytes before and after
evaluation. Formal scopes require source references and a preregistration seal
proof reference when it claims `SEALED`. `PROVISIONAL` is accepted with an
explicit missing reason and cannot give formal PASS. The referenced source itself must be reviewed separately;
hashing a fabricated source does not make it trusted.

Every preregistered Run must appear once. Each Run declares `capture`,
`window_grid`, `truth`, `algorithm`, `time_proof`, `watermarks`,
`target_identity`, and `audio`. `capture` includes immutable boot/session/
interval, epoch, generation, algorithm/config/calibration identities; original
sample ID range; drop/clip half-open ranges and `flags_sealed`. Missing facts
are `{ "value": null, "missing_reason": "NOT_OBSERVED" }` with an appropriate
reason, not zero or an omitted key. Valid reasons are `NOT_OBSERVED`,
`NOT_FROZEN`, `NOT_APPLICABLE`, `LOG_TRUNCATED`, `SOURCE_CONFLICT`,
`SYNTHETIC_ONLY`, and `POLICY_UNRESOLVED`.

`algorithm.portable_ref={run_index_ref,result_ref}` may link existing portable
research bytes. Both references are hashed; the old index must bind the old
result hash, and its planned frame count must match this Run's fixed grid.
The link is reported as `RAW_BYTES_LINKED_RESEARCH_ONLY`: it never supplies
native status, real clock anchors, or designated-consumer take evidence.

`truth.windows` is independently frozen before the algorithm events and has
rows `{start_original_id, label, flags, truth_angle_deg, delta_theta_deg}`.
Labels are `TARGET`, `BACKGROUND_PRE`, `BACKGROUND_POST`, `NON_TARGET`,
`CHALLENGE`, `UNKNOWN`, or `EXCLUDED`. The grid is fixed at 1024 samples with
a 512-sample hop. Drop preserves the original grid and causes INPUT_FAIL;
clip is a separate flag and remains provisional in this first batch because
its present-case policy is not implemented. Supplying a policy label alone
cannot clear this blocker. An independently sealed no-clip flag does not need
the present-case policy.

Formal bundles use the fixed 53-unit portable `required_units` set in
`events.py`; synthetic operator cases may declare a smaller explicit set.
Each algorithm event has `event_id`, full immutable `key`, `kind`, `at` with
native `{domain,epoch,tick}` and optional reliable `seq`/`edge_id`, and a
kind-specific result. `STATUS` also has `unit` and optional `branch_reason` for
valid `SKIPPED`; `NUMERIC` is `VALID` or `INVALID`; `COMMIT`/`TAKE` result
`SUCCESS` is an observed success, with `TAKE.delivery=FRESH`, an exact
`consumer_id`, and `TAKE.original_id_interval=[lower,upper]` when so proved.
`AVAILABLE` also has an original-ID interval whose lower bound must not
precede the source frame's last sample. `time_proof` lists
causal `order_edges`, explicit `T_result={value,unit:"original_samples"}`,
and, for real time, anchored `REAL_OBSERVED` facts plus `consumer_id`.
Formal time proof also needs a frozen TTL policy reference, designated
consumer source reference, and an anchored original-ID coverage interval with
native domain/epoch/tick and error bounds. A `SYNTHETIC_TIME` schedule in a
formal claim remains unresolved even if it lists take events.
Cross-domain equal coarse timestamps with no reliable edge stay unresolved.
Cancellation wins at the same proved edge. A later invalidating error retains
the historical take but moves the final outcome to nonfresh.

Each stream watermark row names `frame`, `status`, `commit`, `take`, `cancel`,
or `late_error`; it supplies `sealed`, `continuous`, `lost_count=0`,
`flush_ack`, `source_epoch`, `first_seq`, `last_seq`, `through_original_id`, and
`terminal_keys` containing the
SHA256 of each canonical full K whose terminal coverage is proved. The
evaluator requires all six streams for a definitive absence or valid fresh.
An expiry timestamp alone is not a late-error seal. `audio` has an independent
qualification axis and is `NOT_MEASURABLE` in this first batch.

Report metrics preserve M and its five classes, N=V+D+U, both independent
background partitions B=F+D+U, rate gates, nearest-rank P50/P95 intervals,
W (report only), and integer unavoidable-failure certificates. Unknown
outcomes leave final P50/P95 null. The claim scope controls the final title;
the input, protocol/numeric, target identity, and audio axes remain visible.
`SYNTHETIC_TEST` may exercise these calculations but can never produce a
formal performance PASS. Evidence-level and member approval are separate.

The frozen contract SHA256 identities are in `report.py`. This package is
standard-library-only. Its data schema is a software evidence envelope, not a
PS/RTL ABI or a production activity/Tracker/TTL profile.
