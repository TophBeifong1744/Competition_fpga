# #16 two-environment development diagnostic adapter

This diagnostic/test asset follows algorithm behavior at
`21e93570cb054f81c629675bd4f1b99a6249edc6`. Its ten local algorithm and
configuration dependencies are pinned by SHA-256. Repair parent:
`ddd44f8d190a76352bb79630e3fd761270d0828e`. It changes no production
default, threshold or interface. A later real output, if authorized, is
`CONDITIONAL_DEVELOPMENT_DIAGNOSTIC_NOT_ACCEPTANCE`.

## Three distinct read-only roots

- `--repo F:/NUEC/develop`: B algorithm/configuration and Luna mapping.
- `--s1-snapshot-root F:/NUEC/codex_out/i16-entry-b-review-a91000c`: A's
  snapshot at `a91000c5e99ceb279a7178885f8fdbd7ffe0da08`, with
  `snapshot-manifest.json` and source tree under `snapshot/`.
- `--s1-evidence-root F:/NUEC/codex_out/i16-two-environment-s1-20260924`:
  native S1 result, command and identity records.

`accepted-inputs.json` freezes these paths and published hashes for this
host and batch. Children are resolved within their separate owner roots.
Historical command paths are checked, retained and never executed. The S1
command used byte-identical Luna `originals/` copies while the mapping names
the `F:/资料/录音/` originals. Their accepted byte hashes bind the records;
historical paths are not rewritten. Machine relocation is outside this batch.

Every invocation requires `--expected-commit` with the complete B commit SHA
chosen outside the adapter. Before reading `accepted-inputs.json`, the adapter
checks that `--repo` is the Git root, HEAD equals that SHA, the executing
`diagnose.py` is the authoritative file under that root, and its raw bytes and
the manifest's raw bytes equal their Git blobs at that commit. It repeats the
HEAD and byte checks before publishing a successful result. The result records
both observed identities. This runtime drift gate does not establish that the
chosen commit is reviewed; the main process must independently check its
commit and source/input identity before a later real run.

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

The two existing native S1 results each report 8/8 `PASS_RAW_UART_ONLY`
captures, 288250 groups and zero flagged rows. Their top statuses remain
`PARTIAL_RECEIPT_PENDING_POSITION_AND_PROVENANCE`; original `missing` and
`not_tested` lists are carried into preflight and later diagnostic outputs.
This supports raw UART integrity only. Position, configuration, playback byte
identity and acoustic performance remain unverified. The A entry snapshot is
consumed read-only, with no copy in the B checkout.

## Metadata preflight — run in this repair

From the B checkout, use a **new** `--out` directory:

```powershell
& 'D:/Python/python.exe' -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/two-environment-diagnostic-20260924/diagnose.py `
  --repo F:/NUEC/develop `
  --expected-commit '<reviewed-40-char-B-SHA>' `
  --s1-snapshot-root F:/NUEC/codex_out/i16-entry-b-review-a91000c `
  --s1-evidence-root F:/NUEC/codex_out/i16-two-environment-s1-20260924 `
  --mapping F:/NUEC/develop/codex_out/c-two-environments-receipt-20260924/luna-receipt/mapping.json `
  --out '<new-preflight-output-directory>' `
  --preflight-only
```

This reads JSON, source text and pinned algorithm files. It verifies the
snapshot manifest but deliberately skips its old recording ZIP. It does not
open received ZIP/BIN/LOG, extract PCM, call the acoustic algorithm, or rerun
S1. The result is `METADATA_PREFLIGHT_ONLY`, not ZIP re-verification. Native
command/log evidence is under
`codex_out/i16-two-environment-adapter-20260924/repair01/`.

## Later real development run — NOT_RUN

The following is an interface example for `indoor`; use the corresponding
original ZIP, native result and fresh output directory for `outdoor`.
`--receipt` must be the **existing native**
`indoor-run/verifier-output/result.json`. An invented `PASS_FULL_S1` object
or Luna mechanical summary is rejected.

```powershell
& 'D:/Python/python.exe' -B task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/two-environment-diagnostic-20260924/diagnose.py `
  --repo F:/NUEC/develop `
  --expected-commit '<reviewed-40-char-B-SHA>' `
  --s1-snapshot-root F:/NUEC/codex_out/i16-entry-b-review-a91000c `
  --s1-evidence-root F:/NUEC/codex_out/i16-two-environment-s1-20260924 `
  --mapping F:/NUEC/develop/codex_out/c-two-environments-receipt-20260924/luna-receipt/mapping.json `
  --environment indoor --zip 'F:/资料/录音/sound_09_22(1).zip' `
  --receipt F:/NUEC/codex_out/i16-two-environment-s1-20260924/indoor-run/verifier-output/result.json `
  --out '<new-development-output>'
```

`--out` must not exist. It receives `result.json` and full `frames.json`, with
the actual command, three roots, Python/NumPy versions, source and dependency
hashes, original ZIP/member/native result identities, and candidate assumptions.
After metadata binding a later run verifies the original ZIP and each selected
member by hash.
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

The tests make tiny ZIPs and PCM in a temporary directory. Synthetic
native-format negative cases run after a separate synthetic identity gate;
the fixed real-evidence hash gate is tested independently. A bounded trace
uses the locked real Tracker with controlled synthetic directions to check
HOLD counting. No received PCM is opened. This is a diagnostic smoke, not an
FPGA functional or acoustic acceptance test. The adapter has been tested on
Python 3.13.0 / NumPy 2.2.0. Native S1's Python 3.7.0 / NumPy 1.21.6
record does not prove adapter compatibility.

The earlier author description of a first test failure has no retained
original failure log and is `AUTHOR_REPORTED / UNVERIFIED`. Preserved `run01`
command/log shows 8/8 success; it is not rewritten as failure proof.
