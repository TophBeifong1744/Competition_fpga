# PS bridge Spec-axis review

Target: `fbbaa161098582ba1e5e112b86d39533769bb3e7`. Read PUBLICATION-PS-BRIDGE-20260921.md then candidate README/CONTRACT/MEMORY and original C. Author originals untouched; exact historical dependencies not replaced by a7f70c5.

## Findings

1. **[P1] Batch payload/configuration errors can arrive after an early commit.** `src/ps_bridge.c:197-207` skips all validation for a result already COMMITTED by an earlier element of the same batch. Independent normal-API reproducer submits `{status=3,payload=7}` followed by `{status=1,payload=99}` for the same token. dispatch returns REJECT but result_take returns OK with 7; reversing the two elements makes take reject. A wrong-binding second element gives the same order dependence. Violates CONTRACT.md:34 (nonzero fragments' payload must agree), :38-40 and :44 (whole-batch errors precede commit and order-independent priority). Validate/aggregate every element for each transaction before changing any result to COMMITTED; include payload, binding and illegal-status conflicts, not only the explicit error flag. Preserve rejection audit. `probe.c`/O0.txt/O2.txt reproduce with identical outputs.

2. **[P2] Current-session unknown error is mislabeled stale when slot is out of range.** `src/ps_bridge.c:172-174` combines session mismatch and invalid slot. Same-session error=true, slot=PSB_RESULTS produces STALE, failed=0, active=1. CONTRACT.md:38/:42 requires unknown current-transaction error to fail-stop; only old-session errors should avoid killing current session. Classify session first, then reject current unknown/malformed token conservatively before commits. No invalid memory access was used in this reproduction.

3. **[P2, additional finite-boundary finding] Last legal generation is invisible to acquire.** `src/ps_bridge.c:133-135` initializes oldest=UINT64_MAX and tests strictly less. The token allocator permits generation UINT64_MAX. Contract-permitted counter injection to MAX-2 before final enqueue/publish yields a READY frame at MAX, but frame_acquire returns WAIT with failed=0. It must select the first eligible slot independently of the sentinel or explicitly fail-stop before publishing that generation. CONTRACT.md:32 promises explicit refusal/fail-stop at finite boundaries. Separate generation.c/generation.txt reproduce; not a claim this naturally occurs within a short run.

## Passing checks and scope

Independent probes verify commit→CLIP/STOP/RESET→late error all fail-stop with was_committed preserved; old-session errors do not kill new session; released current-session errors fail-stop; modifying the caller's original config does not modify the bridge snapshot. These C semantics do not repeat the old Python E01/E02 failures.

Conclusion: **needs modification** for this host C candidate. No claim about ARM, actual concurrent ISR/CDC, production ABI, clocks or real-time hardware. Official author-entry tests are separately reported by root review; independent recorder exit0 is successful reproduction, not a PASS verdict for observed findings.

## Actual commands and execution history

Working environment PowerShell. Compiler `F:/STUDY/IT/C/develop/mingw64/bin/gcc.exe`. Set `$src` to the exact candidate `src` directory and `$out` to this external evidence directory:

```powershell
& $cc -std=c11 -O0 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror -I $src "$out/probe.c" "$src/ps_bridge.c" -o "$out/probe-O0.exe"
& "$out/probe-O0.exe"
& $cc -std=c11 -O2 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror -I $src "$out/probe.c" "$src/ps_bridge.c" -o "$out/probe-O2.exe"
& "$out/probe-O2.exe"
& $cc -std=c11 -O2 -Wall -Wextra -Wpedantic -Wconversion -Wshadow -Werror -I $src "$out/generation.c" "$src/ps_bridge.c" -o "$out/generation.exe"
& "$out/generation.exe"
```

All six final commands exited0. O0/O2 recorded stdout identical. Preliminary harness-only compilation attempts exited1 because this older MinGW emits non-ISO PRIu64/I64 format diagnostics under Werror, followed by rejecting `%llu`; author C was not changed. Harness now prints its bounded payload as unsigned after asserting <=99, eliminating the toolchain-specific formatting issue. These two setup failures are not author defects or negative tests.
