# DAS EOF finite verification assets

Product: `dcaf9ef13d1a2ce4fc766b50f08f8a00836ccb37`, PR39. These assets are
authored by B-REVIEW after the product writer released write ownership. They
do not modify the product, prior fixtures, or frozen reports. New reference,
checker, and runner still require review by original A/R, who did not author
them. Neither these assets nor their successful execution issue member approval.

## Entry

Use Python 3.13.0 and NumPy 2.2.0 (the recorded environment). From any cwd:

```text
python -X utf8 -B data/fixtures/h3_portable/das_eof/runner.py --repo <PR39-repo> --out <new-evidence-directory>
```

The runner refuses existing output directories and outputs inside the asset
directory. Every actual DUT interval uses the public `python -m
soundsight_h3_portable` CLI. The six-angle observation calls the real bound
`audio.render_three_lanes` manual entry and ROM, in a separate process; it does
not invent a second chain entry. Source-binding Git access is configured with
an exact process-scoped `safe.directory`; no global configuration is changed.

## Requirement → input → independent checker → coverage

| Contract | Inputs | Independent assertion | Covered boundary |
|---|---|---|---|
| D17-EOF-01: legal closed schedule endpoint, half-open renderer | short-E first; no STOP/E−1/E/E+1; same/earlier fatal | EOF_AUDIT: exact identity, absolute time, reason, effective/supersession, renderer-control false, termination references, status; E+1 diagnosed `stop_emit` before output | first0 plus first32768, 1024/1032 source/raw, no appended tail/control |
| B r2/P17 source n→emit n+8 | own four-lane integer short ramp; fixed accepted 4096-sample synthetic record | PCM: every code in all four audio arrays, manual interpolation, startup, record padding, cancellation prefix and source/raw lengths | no fresh, four fresh, valid boundary padding, hard abort and smooth fallback |
| Immutable successful binding/take history | seven frames; takes2562/3074/3586/4098; cancel at4098 and at3100 | HISTORY: fixed identities/times/state/fresh; all53 required IDs and disjoint/exhaustive terminal sets; commit/take events; exact old history vs EOF contrast | four fresh before EOF, prior three fresh retained before4098; commit4097 survives while take4098 suppressed |
| STOP fallback versus fatal | same cancel4098 with STOP or fatal; STOP3100 | PCM: full sample model and strict earlier prefix vs noSTOP; STOP continues full4104raw while fatal stops4098raw; complete fallback by3580 for STOP3100 | no retrospective PCM change; STOP fade start has alpha0, subsequent samples checked |
| Accepted six-ROM-angle numerical table; I17-DAS-ASSET-R-01 | literal copied from accepted EXACT-SAMPLES; 64-sample integer ramp | ANGLE_COUNT requires exactly6; ANGLE_IDENTITY fixes order−180/−90/−45/0/45/90; ANGLE_VALUE checks four delays, source20/emit28, exact manual PCM | each real ROM angle and S5 manual entry; no zip truncation acceptance |
| Active checker and failure propagation | isolated evidence mutations and controlled failed runner child | actual checker child exits1 at predetermined category; runner child exits7 and parent propagates7 | empty/missing table, reordering, delay, PCM, EOF identity/time/control/suppression, old successful take, one audio code; runner cannot swallow failure |

The thirteen CLI cases share inputs where meaning is identical. Twelve produce
normal report exits, one is the expected E+1 schedule rejection. They are not a
rerun of the author's eighteen cases or the former 6000-sample matrix.

## Model card

`reference.py` imports only Python `fractions`; no DUT functions or saved DUT
output generate expected PCM. Fixed interpolation is expressed as rational
sample coordinates and four-channel average with one exact ties-even rounding.
Only genuine record boundaries have zero-valued missing samples. Q12 fade
weights are rounded independently as exact fractions, followed by one final
blend rounding. Saturation is not exercised; the bounded inputs stay in S24.

The automatic model is deliberately specific to the accepted synthetic fixture:
SEARCH/SEARCH/ACQUIRE/LOCKED, then repeated angle0 locks at the four frozen
coordinates. The first mono→beam fade lasts480 emits; each subsequent take
arrives after it ends and requests the same angle. STOP3100/4098 arrive after
that fade, hence produce a directly derivable beam→mono fade. EOF STOP produces
no renderer request. Fatal trims at its local edge. This model makes no claim
about FFT/PHAT/DOA correctness, arbitrary retargeting, or production Tracker
parameters. An observed nonzero angle fails the fixture identity assertion;
it is never adopted to tune expected PCM.

The six-angle literal is an exact-byte copy of the previously independently
derived table, already accepted by A in its limited scope. B-REVIEW authored
that prior derivation and these new assets; reuse is disclosed, not self-signed.
The copied file preserves its original historical `purpose` wording. The input
provenance file binds all copies to SHA256. The long PCM is an already fixed
synthetic input, not a recorded physical source; copied author configuration
is an input encoding only, not an oracle. Short input and schedules are created
without importing the product; `EXPECTATIONS-BEFORE-DUT.json` freezes them and
the reference/checker hashes before the first CLI invocation.

The local `.gitattributes` marks the accepted original JSON literal and its
provenance JSON `-text`: their original exact bytes must survive Git checkout,
including legacy CRLF. Numerical expectations and original hash identities must
not be changed to accommodate Git text normalization. An intermediate test
commit had normalized these two blobs despite successful execution against the
unchanged working files; that asset portability defect and its intermediate
result are retained. The corrected final asset commit preserves both Git blob
and working identities, and receives a complete affected rerun.

## Evidence and limitations

Each child has `command.json`, byte-preserved stdout/stderr, actual exit and
argument-file/source hashes. Runner snapshots before/after product identities
and binds actual HEAD separately from the frozen product SHA. Canary records
retain mutated files and expected assertion category. Failed runs are retained;
use a fresh `--out` for each rerun. An intentionally failed controlled runner
has its own FIRST-FAILURE record; this is expected canary activity, not DUT_FAIL.

The first execution exposed a checker expectation error: fatal exactly at EOF
sets the public interval status ABORTED, but no renderer emission exists at E,
so `audio.aborted_at_emit` is null. The preserved pre-repair checker had expected
E in that local field. Its correction distinguishes public absolute cancellation
from an in-domain renderer stop; it does not change PCM, public audit, status,
or any product file. Original failing input/log/source snapshots are retained
under the first run's `pre-repair-assets/` and referenced in delivery.

The second execution correctly propagated the controlled child failure7. Its
outer canary locator initially checked stdout alone, while the failure diagnostic
was on stderr. That test-harness failure is also preserved with pre-repair asset
snapshots; the locator now searches both raw streams. A further checker assertion
checks the entire ordered public event history, with a dedicated changed-binding
event canary in addition to the termination/take-history canary.

Real hardware visibility, time bounds, physical source identity, production
thresholds, saturation extremes, arbitrary beam-retarget permutations, and
full acoustic-chain correctness are NOT RUN. Former accepted continuous-turn,
6000-sample, and cancellation coverage is reused by the main report at its
original scope; it is not reported here as newly executed. Target result is
`FIXED_PENDING_REVIEW`: offline synthetic functional evidence for original A/R
non-author review, not full FUNCTIONAL_ACCEPTANCE, issue closure, or actual A
member approval.
