# Independent portable H3 verification fixture

This directory is a separate verification asset for product commit
`5efc4b67ad49de2c2bd99eb38ba8995b6f312289` and Draft PR #34. It tests
research-only portable integer composition and `SYNTHETIC_TIME` events. It is
authored by B-REVIEW after the product writer released the clean checkout; its
author cannot independently approve this new checker or reference. Formal #17
evaluation r2, production parameters, physical timing, RTL and measured acoustic
performance remain outside this claim.

## Independent basis

The frozen B r2 contract has two distinct windows: direct S24 Hann for DOA and
per-channel RNE mean removal in S25 before Hann for the gate. Each domain runs
four radix-2 FFT29 transforms, ten RNE /2 stages, then a separate RNE /16
half-spectrum adapter. The six PHAT pairs use the DOA spectrum in the frozen
01/02/03/12/13/23 order. Gate attack 3/3 requires all four explicit power
references. A gate-closed frame still completes all eight front-end transforms
and names all six later pairs as skipped. ACQUIRE retains candidate history but
does not provide a beam or fresh. First legal fresh may retarget the automatic
lane only at its supplied take time; source sample `n` maps to emit `n+8`.
Without an external time anchor, the numeric CLI cannot claim fresh or control.

`independent_reference.py` contains its own signed nearest-even division,
complex adapter, even/odd recursive FFT, window and gate-power equations, and
PHAT cross/mask arithmetic. It never imports the DUT or historic leaf code.
The frozen Hann/twiddle/atan bytes are intentionally shared inputs: all 2046
twiddle values and 24 atan values are checked against the extraction formula,
but that common table identity alone does not prove an independently generated
hardware ROM. The positive golden is computed before invoking the DUT and is
stored in the evidence run, not checked into source as a claimed universal
golden. The xorshift32 PCM is a new deterministic broadband scene with a
synthetic six-sample inter-column offset, distinct from the author's LCG/tiled
diagnostic. Its 40 mm geometry and unit power reference are research assumptions,
not measured array truth or production defaults.

## Reproduce

Use Python 3.13 with NumPy 2.2 (the known working environment). Supply a new
output directory and the exact fixed 21-object index, for example:

```text
python -B data/fixtures/h3_portable/run_verification.py \
  --repo <checkout-at-5efc4b67> --python <python-3.13-executable> \
  --fixed-input-index <ASSEMBLY-PLAN-INPUTS.json> --out <new-codex_out-directory>
```

The runner records commands, stdout/stderr, exit codes, product Git-blob versus
worktree byte hashes (including the two checkout-only CRLF JSON manifests),
source bindings, source index, test-asset hashes, and independent outputs. It
never edits product files. A nonzero `boundary` substep is intentionally retained
as a product-contract discrepancy, not relabeled PASS; the runner itself exits
2 for `DUT_BOUNDARY_FAIL`. An initial development runner returned 0 while its
index correctly said `DUT_BOUNDARY_FAIL`; its original log is retained and a
later run verifies the corrected exit propagation. `checker.py --self-test`
performs four **in-memory** isolated corruptions; it never changes actual CLI
artifacts. The CLI negatives each get their own bad config and must fail for
the intended identity, missing-field, or type reason before writing an output.

## Requirement → test → checker → covered scope

| Requirement | Input/operation | Independent check | Coverage and limit |
| --- | --- | --- | --- |
| Exact identity | fixed Git product plus source/table manifests | runner raw SHA/Git comparisons; CLI wrong-manifest rejection | exact local bytes; not cross-platform execution |
| S24/S25 dual windows | 7 complete 1024/512 frames of four-channel PCM | RNE mean/Hann arrays and independent FFT/half-spectrum/power for all frames | 77 array names; no AMD equivalence |
| Frozen tables | 2×1023 Q30 complex twiddles, 24 atan codes | formula versus every item, raw byte SHA | one specified Python/NumPy profile |
| Activity/instance closure | two gate-closed, five active frames | 56 forward instances, 30 conditional IFFT, named skipped units, 7 exact expected sets | does not independently derive every IFFT output or every DOA vector code |
| DOA and CORDIC integration | coherent synthetic x-axis signal | DOA validity, angle within predeclared ±8°, normalized CORDIC status; independent PHAT cross/mask | bounded geometry/integration, not all angle codes |
| Causal Tracker | explicit status/available/commit/take sequence | SEARCH→ACQUIRE→LOCKED, four fresh, one take per frame, no premature beam | synthetic service only; HOLD/late fault/STOP still untested in this first packet |
| Audio | common source/emit, manual 0° | independent full manual Q12 interpolation; auto equals mono before first fresh, output coordinate/length and 2-beam/17-history limits | full dynamic PCM after retarget not independently modeled |
| CLI rejection | wrong manifest, missing tracker field, bool integer | nonzero and exact intended error; no success output | three bad-input classes |
| Checker sensitivity | in-memory numeric/fresh/event/audio corruption | intended first error for each | four canaries, not an exhaustive fault model |
| Fixed4 overflow contract | S29 positive max and signed tie codes | `boundary_probe.py` independent B14-02 expectation | **current DUT-bound adapter mismatches zero placeholder and per-component flag exposure** |

## Current finding and untested boundaries

`I17-H3-V1-01` is the first observed product discrepancy: B r2 B14-02 requires
one overflowing component to produce a complex `(0,0)` placeholder with a
component overflow indication and `numeric_valid=false`. The bound software
adapter in the new chain calls the legacy `adapt_fft29_to_s25` through
`checked_adapter`, which returns the positive S25 saturation code for a crafted
maximum S29 real input, plus only a cumulative overflow count. RNE tie codes
match. The normal legal-PCM scene did not reach this boundary; its successful
run does not erase the direct interface discrepancy. The product owner/main
flow must decide whether the portable software artifact is required to expose
the full B14-02 adapter contract at this boundary, or explicitly narrow the
portable claim and keep the fixed4 leaf as separately verified. No DUT edit or
new profile was made here.

This first packet deliberately stops at that specific mismatch. HOLD/reacquire,
TTL equality/overflow, fatal versus STOP, missing/late statuses, full PHAT/IFFT
and DOA code-by-code, dynamic fade PCM, and chunking remain NOT_TESTED by this
independent packet; the author's `DIAGNOSTIC_SMOKE` is not independent
acceptance evidence for those items. A follow-up should resolve the first
contract scope issue before interpreting broader FUNCTIONAL_SIM acceptance.
