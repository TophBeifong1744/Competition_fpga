# #16 two-environment development diagnostic adapter

This is a diagnostic/test asset. Reference behavior is commit
`21e93570cb054f81c629675bd4f1b99a6249edc6`; the direct algorithm and
configuration files plus their local import closure are pinned by SHA-256 in
`diagnose.py`. It does
not change production defaults or implement chirp alignment, formal angle
scoring, audio gain, or SNR scoring. A successful run is
`CONDITIONAL_DEVELOPMENT_DIAGNOSTIC_NOT_ACCEPTANCE` (`DIAGNOSTIC_SMOKE`).

## Inputs and gates

`--mapping` is Luna's mapping of both environments, not a directory scan.
Exactly eight BIN/LOG pairs per environment are required. Each pair must
bind its canonical `c_{indoor|outdoor}_{scene}_20260922_{run}` identity to one
ZIP and exact original member paths/hashes. The adapter verifies the whole
mapping, then the chosen ZIP and every selected BIN/LOG member. The original
ZIP is read only. It never consumes Luna's normalized copies or renames data.

The fixed input metadata reviewed for this batch is:

| File | SHA-256 |
| --- | --- |
| `luna-receipt/mapping.json` | `22873b4a64020edb29fac7b083c429b1eea2a310f2d3242df085ba8ad06ca757` |
| `luna-receipt/summary.json` | `e046966df4d1ab07a15a5170c08b1f55e4b122d98c7e710cb506c351e88557ef` |
| `luna-receipt/runs/index.json` | `61ef3998c4a01f9dd457e089de5ab8a750fe33386981a16f4ec32cfb115a51b7` |

The Luna summary is a **mechanical receipt** with `complete_s1_status =
BLOCKED_I16_ENTRY_01`; it cannot be passed as `--receipt`. Before a real run,
A's I16-ENTRY-01 repair must pass independent review and a complete S1
verification must produce a per-environment receipt. The bridge that creates
that receipt remains an explicit integration dependency. A receipt must be a
JSON object with:

- `kind: FULL_S1_CAPTURE_VERIFICATION`, `status: PASS_FULL_S1`,
  `environment`, `mapping_sha256`, and `source_zip_sha256`;
- `entry_commit` (40 hex), `entry_path` (repo-relative),
  `entry_source_sha256`, `evidence_path` (repo-relative),
  `evidence_sha256`, and the real `command` array;
- eight `captures` with unique `canonical_stem`, `status: PASS_FULL_S1`,
  `raw_sha256`, and `log_sha256` matching the mapping exactly.

The adapter verifies referenced files and hashes. These checks bind records;
they do not confer human approval or prove that an arbitrary receipt was
produced by an approved entry. The entry reviewer and #16 reviewer must check
that provenance separately. The existing `finish_scene.py` import failure is
not bypassed by the adapter.

## Proposed real invocation — NOT_RUN

After the full S1 gate is met, invoke separately for `indoor` and `outdoor`
with the corresponding original ZIP and a new output path:

```powershell
& 'D:/Python/python.exe' -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/two-environment-diagnostic-20260924/diagnose.py `
  --repo F:/NUEC/develop --zip '<matching-original.zip>' `
  --mapping '<luna-receipt/mapping.json>' --environment indoor `
  --receipt '<complete-S1-indoor-receipt.json>' --out '<new-diagnostic-output>'
```

`--out` must not exist. It receives `result.json` and full `frames.json`, with
the actual command, working directory, Python/NumPy versions, source and
dependency hashes, ZIP/member/receipt identities, and candidate assumptions.
For each environment only its `bg_pre` supplies the 95th percentile background
power; no `old_background` mode is run. Every complete 1024-sample window is
processed at 512-sample hops from the start of each separate Run. Each Run
creates fresh gate and trackers; nonactivity resets the tracker as in the old
diagnostic. Fresh, HOLD, rejected frames and timestamps are retained. The
40 mm square, 48 kHz and 343 m/s values are candidate assumptions, not
measurements of this capture.

The user's playback statement is `USER_REPORTED`; WAV byte identity, actual
position uncertainty and loaded artifacts are not independently established.
Marker/guard windows are not used here. Formal evaluation remains governed by
`checkpoint-20260923/FORMAL-EVALUATION.md`: independently supported activity,
complete windows, all-denominator reporting, HOLD excluded from fresh,
`V=0` percentile `null`, and explicit uncertain/excluded intervals. Without
credible array-position component references no objective SNR is reported.

## Bounded synthetic check

```powershell
& 'D:/Python/python.exe' -B -m unittest discover `
  -s task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/two-environment-diagnostic-20260924 `
  -p 'test_*.py' -v
```

The test makes tiny ZIPs and PCM in a temporary directory. It does not open
either received recording. This check is a diagnostic smoke of mapping,
reference isolation, frame/state handling and failure gates; it is not an FPGA
functional or acoustic acceptance test.
