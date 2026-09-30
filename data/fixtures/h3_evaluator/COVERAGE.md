# Requirement → Test → Checker → Cover

Frozen input order: EVALUATOR-SPEC-r1 (`3d2dfc4c…`), SYNTHETIC-CASE-PLAN (`03fab616…`), MAIN-DECISIONS-r2 (`bb6f4852…`), IMPLEMENTATION-BATCH (`72ec3983…`). `expected.json` was authored from these rules before DUT reports; the pre-DUT shorthand arithmetic correction is retained in the evidence directory. `make_cases.py` does not import product code. The builder encodes synthetic K, events, source-ID intervals, terminal watermarks, independent truth and preregistration; expected values are literal in `expected.json`. `checker.py` compares only original bundle, frozen expected and DUT report. Its generic checks cover exact Run set, grid positions, source-frame K hashes, per-K event and take sets, M and N/B conservation, provisional final quantiles, audio and synthetic scope. The real CLI and checker execute as separate subprocesses.

| Contract item | Bundle(s) | Independent expected / checker cover |
| --- | --- | --- |
| C01 zero N | c01_zero_n | N=0, rate null/zero denominator |
| C02 N=935 | c02_935 | N=935, insufficient exposure |
| C03 all D versus all U | c03_all_d, c03_all_u | zero V; FAIL versus NOT_READY; no fake NO_RESULT |
| C04 80% integer edge | c04_v748, c04_v749 | 748 fails, 749 passes rate |
| C05 background B=0/935/936 | c05_b0/b935/b936 | separate pre denominator and exposure |
| C06 background 1% | c06_f10/f11, c06_post_f11 | pre exact boundary and post independent failure |
| C07 five Run one fail | c07_five_one_fail | all five exact IDs/V; fifth 0 retained |
| C08 sixth Run cannot disappear | c08_sixth_fail | six exact IDs/V; sixth 0 retained |
| C09 nearest-rank | c09_rank | P50=4, P95=11 FAIL |
| C10 wrap180 | c10_wrap | known subset error=2; off-domain final withheld |
| C11 uncertainty interval | c11_uncertainty | P50 lower4/upper6 inconclusive |
| C12 P95/W | c12_bad1/bad2 | one versus two 16-degree outliers, W report only |
| C13 HOLD | c13_hold | V935/D1, HOLD does not become fresh |
| C14 equal angle distinct K | c14_equal_angle | two K, V2, exact K hashes |
| C15 duplicate success | c15_duplicate | D1 protocol reason; exact two-take history |
| C16 unknown session K | c16_unknown_k | UNKNOWN_K issue, original V retained |
| C17 target delivered during background | c17_late_target | original target V1, background F0, delivered-time audit |
| C18 expiry equality / +1 | c18_equal/expired | equality V1, +1 D/TAKE_EXPIRED |
| C19 u64 expiry overflow | c19_overflow | D/T_RESULT_OVERFLOW, no wrap |
| C20 missing required status | c20_status_u/d | incomplete watermark U; sealed absence D |
| C21 missing take | c21_take_u/d | incomplete watermark U; sealed absence NO_RESULT D |
| C22 invalidating late error | c22_late_error | history retained, V demoted to D |
| C23 cancellation order | c23_cancel-unknown/same/after, c23_same_tick_ordered | coarse unordered U; same edge D; earlier take V |
| C24 drop versus clip | c24_drop/clip, grid_five_classes | raw grid, tail41, overlapping flags, five class conservation, clip provisional |
| C25 audio missing | c25_audio_missing | NOT_MEASURABLE |
| R01-A unavoidable angle fail | r01a | v749/u187/g0, both certificates FAIL, final quantiles null |
| R01-B rescuable completion | r01b | v400/u536, no certificate, final null |
| R01-C equality/one below | r01c_equal/fail | P95 g94 versus93; only latter certificate |
| R01-D e_low on threshold | r01d_threshold_equal | g100, no certificate |
| R01-E provisional take | r01e_unsealed_v | late-error watermark absent, V0/U936, no certificate |
| R01-F zero V/unknown denominator | r01f_zero_v, c24_clip | no certificate; clip denominator provisional |
| Full required-instance identity | full53 | 53 fixed status identities and causal first take |
| Mixed same-angle wrong source | mixed_wrong_same_angle | V1 retained, target-identity FAIL |
| Input FAIL plus performance FAIL | input_fail_perf_fail | both axes survive independently |
| Synthetic claim escalation | formal_synthetic_guard | adversarial formal request with synthetic schedule remains U / EVIDENCE_INSUFFICIENT |
| CLI and identity | cli_probe.py | malformed 2, hash mismatch 3, controlled internal 4, existing out 2/unchanged |
| Checker mutation/runner propagation | canaries.py and runner.py | 10 real subprocess rejections with target assertions; injected checker failure returns runner 1 |

Coverage is only offline synthetic evaluator logic. Generated bundles are finite artificial records, not real capture, independent physical ground truth, approved clip policy, target selection, synchronized audio components, actual consumer/anchor/T_result or complete native watermarks. A 51-bundle pass is not a production pass. The checker and fixture builder are new assets by this reviewer and require separate non-author review. The `internal_injected` CLI test invokes the true `main()` with an isolated injected exception; it proves exit-4 handling, not a naturally occurring drift. No physical source bytes were altered.
