"""Offline per-run and preregistered-cell metrics; no result-selected denominators."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_FLOOR

from .bundle import BundleError


def decimal(value, label: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise BundleError(f"DECIMAL_REQUIRED:{label}")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise BundleError(f"DECIMAL_INVALID:{label}") from exc
    if not number.is_finite():
        raise BundleError(f"DECIMAL_NOT_FINITE:{label}")
    return number


def angle_error(estimate, truth, uncertainty) -> dict:
    estimate, truth = decimal(estimate, "angle.estimate"), decimal(truth, "angle.truth")
    uncertainty = decimal(uncertainty, "angle.uncertainty")
    if uncertainty < 0:
        raise BundleError("NEGATIVE_ANGLE_UNCERTAINTY")
    shifted = estimate - truth + 180
    turns = (shifted / 360).to_integral_value(rounding=ROUND_FLOOR)
    error = abs(shifted - 360 * turns - 180)
    return {"nominal": error, "low": max(Decimal(0), error - uncertainty),
            "high": min(Decimal(180), error + uncertainty)}


def nearest_rank(values: list[Decimal], numerator: int, denominator: int) -> Decimal | None:
    if not values:
        return None
    rank = (numerator * len(values) + denominator - 1) // denominator
    return sorted(values)[rank - 1]


def certify_unavoidable_fail(errors: list[dict], u: int, numerator: int,
                              denominator: int, threshold: Decimal) -> dict | None:
    v = len(errors)
    if v == 0:
        return None
    g = sum(error["low"] <= threshold for error in errors)
    left, right = denominator * (g + u), numerator * (v + u)
    return {"v": v, "u": u, "g": g, "p_num": numerator, "p_den": denominator,
            "threshold_deg": str(threshold), "left": left, "right": right,
            "fail_for_all_completions": left < right}


def _rate_gate(valid: int, unresolved: int, total: int | None, min_total: int,
               lhs_factor: int, rhs_factor: int, upper_limit: bool = False) -> dict:
    if total is None:
        return {"status": "NOT_READY", "reason": "DENOMINATOR_PROVISIONAL", "ratio": None}
    if total == 0:
        return {"status": "NOT_READY", "reason": "ZERO_DENOMINATOR", "ratio": None}
    ratio = {"num": valid, "den": total}
    if total < min_total:
        return {"status": "NOT_READY", "reason": "INSUFFICIENT_EXPOSURE", "ratio": ratio}
    if upper_limit:
        if lhs_factor * valid > rhs_factor * total:
            return {"status": "FAIL", "reason": "SEALED_EXCESS_FRESH", "ratio": ratio}
        if unresolved:
            return {"status": "NOT_READY", "reason": "UNRESOLVED_OUTCOMES", "ratio": ratio,
                    "possible_upper": {"num": valid + unresolved, "den": total}}
        return {"status": "PASS", "reason": None, "ratio": ratio}
    if lhs_factor * (valid + unresolved) < rhs_factor * total:
        return {"status": "FAIL", "reason": "EVEN_BEST_COMPLETION_BELOW_MINIMUM", "ratio": ratio,
                "possible_upper": {"num": valid + unresolved, "den": total}}
    if unresolved:
        return {"status": "NOT_READY", "reason": "UNRESOLVED_OUTCOMES", "ratio": ratio,
                "possible_upper": {"num": valid + unresolved, "den": total}}
    return {"status": "PASS" if lhs_factor * valid >= rhs_factor * total else "FAIL",
            "reason": None if lhs_factor * valid >= rhs_factor * total else "BELOW_MINIMUM",
            "ratio": ratio}


def _quantile_gate(errors: list[dict], u: int, p_num: int, p_den: int,
                   threshold: Decimal, cert_allowed: bool) -> dict:
    known = {name: nearest_rank([e[name] for e in errors], p_num, p_den)
             for name in ("nominal", "low", "high")}
    subset = {key + "_deg": str(value) if value is not None else None
              for key, value in known.items()}
    if u:
        certificate = certify_unavoidable_fail(errors, u, p_num, p_den, threshold) if cert_allowed else None
        fail = certificate is not None and certificate["fail_for_all_completions"]
        return {"status": "FAIL" if fail else "NOT_READY",
                "reason": "FAIL_CERTIFIED_FOR_ALL_COMPLETIONS" if fail else "PENDING_COMPLETION",
                "final_nominal_deg": None, "final_low_deg": None, "final_high_deg": None,
                "known_subset": subset, "certificate": certificate}
    if not errors:
        return {"status": "NOT_READY", "reason": "ZERO_VALID_FRESH",
                "final_nominal_deg": None, "final_low_deg": None, "final_high_deg": None,
                "known_subset": subset, "certificate": None}
    if known["low"] > threshold:
        status = "FAIL"
    elif known["high"] <= threshold:
        status = "PASS"
    else:
        status = "INCONCLUSIVE"
    return {"status": status, "reason": "ANGLE_INTERVAL_CROSSES_LIMIT" if status == "INCONCLUSIVE" else None,
            "final_nominal_deg": subset["nominal_deg"],
            "final_low_deg": subset["low_deg"], "final_high_deg": subset["high_deg"],
            "known_subset": subset, "certificate": None}


def score_run(run: dict, grid: dict, outcomes: dict[int, dict], issues: list[dict],
              claim_scope: str, verified_ref_ids: set[str]) -> dict:
    if grid["M"] is None:
        return {"run_id": run["run_id"], "input_qualification": {"status": "EVIDENCE_INSUFFICIENT",
                "reasons": [grid["reason"]]}, "metrics": {"M": None, "N": None, "V": None,
                "D_N": None, "U_N": None,
                "null_reasons": {"M": grid["reason"], "N": grid["reason"],
                                 "V": grid["reason"], "D_N": grid["reason"],
                                 "U_N": grid["reason"]}}, "gates": {}, "protocol_numeric_failures": issues,
                "target_identity_qualification": {"status": "NOT_ESTABLISHED"},
                "audio_qualification": {"status": "NOT_MEASURABLE"},
                "decision": {"status": "EVIDENCE_INSUFFICIENT", "blockers": [grid["reason"]]},
                "windows": []}
    input_reasons = []
    input_fail = False
    if grid["drop_present"]:
        input_fail = True
        input_reasons.append("ORIGINAL_SAMPLE_DROP")
    if run["capture"]["flags_sealed"] is not True:
        input_reasons.append("CAPTURE_FLAGS_NOT_SEALED")
    if run["truth"].get("sealed") is not True:
        input_reasons.append("INDEPENDENT_TRUTH_NOT_SEALED")
    if claim_scope != "SYNTHETIC_TEST":
        for name in ("capture", "truth", "algorithm", "time_proof", "watermarks"):
            source_ref = run[name].get("source_ref")
            if not isinstance(source_ref, str) or source_ref not in verified_ref_ids:
                input_reasons.append("NATIVE_SOURCE_NOT_BOUND:" + name)
    # The present-case policy is not implemented in this first product batch.
    # A claimed policy reference alone cannot decide whether clipped windows enter N/B.
    clipped = grid["clip_present"]
    if clipped:
        input_reasons.append("CLIP_PRESENT_POLICY_NOT_IMPLEMENTED")
    if grid["classes"]["ACTIVITY_OR_GEOMETRY_UNKNOWN"]:
        input_reasons.append("WINDOW_TRUTH_UNKNOWN")
    for window in grid["windows"]:
        if window["primary_class"] == "TARGET_N":
            delta = decimal(window["delta_theta_deg"], "delta_theta_deg")
            if delta > 1 or delta < 0:
                input_reasons.append("GEOMETRY_UNCERTAINTY_EXCEEDS_1_DEG")
            truth = decimal(window["truth_angle_deg"], "truth_angle_deg")
            if abs(truth) > 45:
                input_reasons.append("TARGET_OUTSIDE_P1_DOMAIN")
    input_reasons = sorted(set(input_reasons))
    input_state = "INPUT_FAIL" if input_fail else "EVIDENCE_INSUFFICIENT" if input_reasons else "QUALIFIED"
    n_windows = [w for w in grid["windows"] if w["primary_class"] == "TARGET_N"]
    pre_windows = [w for w in grid["windows"] if w["primary_class"] == "CONFIRMED_NON_TARGET" and
                   w["truth_label"] == "BACKGROUND_PRE"]
    post_windows = [w for w in grid["windows"] if w["primary_class"] == "CONFIRMED_NON_TARGET" and
                    w["truth_label"] == "BACKGROUND_POST"]

    def count(windows: list[dict]) -> dict:
        parts = {"VALID_FRESH": 0, "DETERMINATE_NONFRESH": 0, "UNRESOLVED": 0}
        for w in windows:
            parts[outcomes[w["frame_index"]]["class"]] += 1
        return parts

    n, pre, post = count(n_windows), count(pre_windows), count(post_windows)
    assert sum(n.values()) == len(n_windows)
    assert sum(pre.values()) == len(pre_windows)
    assert sum(post.values()) == len(post_windows)
    denominator_provisional = clipped or run["truth"].get("sealed") is not True or (
        run["capture"]["flags_sealed"] is not True or
        grid["classes"]["ACTIVITY_OR_GEOMETRY_UNKNOWN"] > 0)
    N, Bpre, Bpost = (None, None, None) if denominator_provisional else (
        len(n_windows), len(pre_windows), len(post_windows))
    errors = []
    for w in n_windows:
        result = outcomes[w["frame_index"]]
        if result["class"] == "VALID_FRESH":
            errors.append(angle_error(result["angle_deg"], w["truth_angle_deg"], w["delta_theta_deg"]))
    v, u = n["VALID_FRESH"], n["UNRESOLVED"]
    cert_allowed = N is not None and not issues and not input_reasons and v > 0
    gates = {
        "target_exposure": {"status": "PASS" if N is not None and N >= 936 else "NOT_READY",
                            "reason": None if N is not None and N >= 936 else "N_BELOW_936_OR_PROVISIONAL"},
        "valid_rate": _rate_gate(v, u, N, 936, 5, 4),
        "background_pre": _rate_gate(pre["VALID_FRESH"], pre["UNRESOLVED"], Bpre, 936, 100, 1, True),
        "background_post": _rate_gate(post["VALID_FRESH"], post["UNRESOLVED"], Bpost, 936, 100, 1, True),
        "P50": _quantile_gate(errors, u, 1, 2, Decimal(5), cert_allowed),
        "P95": _quantile_gate(errors, u, 19, 20, Decimal(10), cert_allowed),
    }
    if N is None or input_reasons or issues:
        for name in ("P50", "P95"):
            gates[name]["status"] = "NOT_READY"
            gates[name]["reason"] = "INDEPENDENT_TRUTH_INPUT_OR_IDENTITY_NOT_QUALIFIED"
            gates[name]["final_nominal_deg"] = None
            gates[name]["final_low_deg"] = None
            gates[name]["final_high_deg"] = None
            gates[name]["certificate"] = None
    W = sum(e["nominal"] > 15 for e in errors)
    metrics = {"M": grid["M"], "M_classes": grid["classes"], "tail_samples": grid["tail_samples"],
               "N": N, "N_provisional": len(n_windows), "V": v,
               "D_N": n["DETERMINATE_NONFRESH"], "U_N": u,
               "B_pre": Bpre, "B_pre_provisional": len(pre_windows),
               "F_pre": pre["VALID_FRESH"], "D_pre": pre["DETERMINATE_NONFRESH"],
               "U_pre": pre["UNRESOLVED"], "B_post": Bpost,
               "B_post_provisional": len(post_windows), "F_post": post["VALID_FRESH"],
               "D_post": post["DETERMINATE_NONFRESH"], "U_post": post["UNRESOLVED"],
               "W_known": W, "W_over_V": {"num": W, "den": v} if v else None,
               "W_over_N": {"num": W, "den": N} if N else None}
    metrics["null_reasons"] = {
        key: reason for key, reason in (
            ("N", "CLIP_OR_TRUTH_OR_FLAGS_PROVISIONAL" if N is None else None),
            ("B_pre", "CLIP_OR_TRUTH_OR_FLAGS_PROVISIONAL" if Bpre is None else None),
            ("B_post", "CLIP_OR_TRUTH_OR_FLAGS_PROVISIONAL" if Bpost is None else None),
            ("W_over_V", "ZERO_VALID_FRESH" if v == 0 else None),
            ("W_over_N", "PROVISIONAL_OR_ZERO_DENOMINATOR" if not N else None))
        if reason is not None}
    protocol = list(issues)
    outcome_reasons = {}
    for w in grid["windows"]:
        result = outcomes[w["frame_index"]]
        reason = result["reason"]
        outcome_reasons[reason] = outcome_reasons.get(reason, 0) + 1
        if result["failure_flags"]:
            protocol.append({"kind": result["reason"], "key_sha256": result["key_sha256"],
                             "flags": result["failure_flags"], "event_ids": result["event_ids"]})
    event_rows = run["algorithm"]["events"] if isinstance(run["algorithm"]["events"], list) else []
    event_kinds = {}
    for event in event_rows:
        kind = event.get("kind")
        event_kinds[kind] = event_kinds.get(kind, 0) + 1
    background_spans = [(w["start_original_id"], w["stop_original_id"])
                        for w in pre_windows + post_windows]
    target_keys = {outcomes[w["frame_index"]]["key_sha256"] for w in n_windows}
    old_target_takes_during_background = []
    from .events import key_digest
    for event in event_rows:
        if event.get("kind") != "TAKE" or event.get("result") != "SUCCESS" or not isinstance(event.get("key"), dict):
            continue
        interval = event.get("original_id_interval")
        if (key_digest(event["key"]) in target_keys and isinstance(interval, list) and len(interval) == 2
                and all(type(x) is int for x in interval) and
                any(a <= interval[0] <= interval[1] < b for a, b in background_spans)):
            old_target_takes_during_background.append(event["event_id"])
    audit = {"outcome_reason_counts": outcome_reasons, "event_kind_counts": event_kinds,
             "historical_successful_take_count": sum(len(o["take_history"]) for o in outcomes.values()),
             "old_target_take_during_background_event_ids": old_target_takes_during_background,
             "HOLD_outcome_count": outcome_reasons.get("HOLD", 0),
             "REJECTED_outcome_count": outcome_reasons.get("REJECTED", 0),
             "TAKE_EXPIRED_outcome_count": outcome_reasons.get("TAKE_EXPIRED", 0)}
    target = dict(run["target_identity"])
    if run["scenario"] == "single-source":
        target_status = "NOT_APPLICABLE_SINGLE_SOURCE"
    elif (target.get("status") == "WRONG_TARGET" and
          isinstance(target.get("independent_source_ref"), str) and
          target["independent_source_ref"] in verified_ref_ids):
        target_status = "FAIL"
    elif (target.get("status") == "ESTABLISHED" and target.get("policy_id") and
          isinstance(target.get("independent_source_ref"), str) and
          target["independent_source_ref"] in verified_ref_ids):
        target_status = "ESTABLISHED"
    else:
        target_status = "NOT_ESTABLISHED"
    audio = {"status": "NOT_MEASURABLE", "reason": "MEASUREMENT_QUALIFICATION_NOT_FROZEN_OR_NOT_IMPLEMENTED"}
    blockers = list(input_reasons)
    if protocol:
        blockers.append("PROTOCOL_OR_NUMERIC_FAILURE")
    if target_status == "FAIL":
        blockers.append("WRONG_TARGET_IDENTITY")
    elif run["scenario"] != "single-source" and target_status != "ESTABLISHED":
        blockers.append("TARGET_IDENTITY_NOT_ESTABLISHED")
    if claim_scope == "P1_P4_BATCH":
        blockers.append("AUDIO_NOT_MEASURABLE")
    failed_gates = [name for name, result in gates.items() if result["status"] == "FAIL"]
    pending_gates = [name for name, result in gates.items() if result["status"] == "NOT_READY"]
    inconclusive = [name for name, result in gates.items() if result["status"] == "INCONCLUSIVE"]
    if (protocol or target_status == "FAIL" or (claim_scope == "P1_P4_BATCH" and input_fail)
            or (failed_gates and not input_fail)):
        decision = "FAIL"
    elif blockers or pending_gates or input_fail:
        decision = "EVIDENCE_INSUFFICIENT"
    elif inconclusive:
        decision = "INCONCLUSIVE"
    else:
        decision = "PASS"
    if claim_scope == "SYNTHETIC_TEST":
        decision = "SYNTHETIC_TEST_ONLY"
    return {"run_id": run["run_id"],
            "input_qualification": {"status": input_state, "reasons": input_reasons},
            "metrics": metrics, "gates": gates, "audit": audit,
            "protocol_numeric_failures": protocol,
            "target_identity_qualification": {"status": target_status, "evidence": target},
            "audio_qualification": audio,
            "decision": {"status": decision, "failed_gates": failed_gates,
                         "pending_gates": pending_gates, "inconclusive_gates": inconclusive,
                         "gate_qualification": "DEVELOPMENT_ONLY_INPUT_FAIL" if input_fail else "ELIGIBLE_IF_OTHER_EVIDENCE_COMPLETE",
                         "blockers": sorted(set(blockers + pending_gates))},
            "windows": [{**w, "outcome": outcomes[w["frame_index"]]} for w in grid["windows"]]}


def score_cells(runs: list[dict], results: list[dict], scope: str) -> list[dict]:
    groups = {}
    for run, result in zip(runs, results):
        key = (run["environment"], run["scenario"], str(run["nominal_angle_deg"]))
        groups.setdefault(key, []).append((run, result))
    out = []
    for (environment, scenario, angle), items in groups.items():
        states = [r["decision"]["status"] for _, r in items]
        sources = [r["capture"].get("source_ref") for r, _ in items]
        independent = (all(isinstance(source, str) and source for source in sources) and
                       len(sources) == len(set(source for source in sources if isinstance(source, str))))
        if scope == "SYNTHETIC_TEST":
            status = "SYNTHETIC_TEST_ONLY"
        elif "FAIL" in states:
            status = "FAIL"
        elif len(items) < 5 or not independent or "EVIDENCE_INSUFFICIENT" in states:
            status = "EVIDENCE_INSUFFICIENT"
        elif "INCONCLUSIVE" in states:
            status = "INCONCLUSIVE"
        else:
            status = "PASS"
        out.append({"environment": environment, "scenario": scenario,
                    "nominal_angle_deg": angle, "run_ids": [r["run_id"] for _, r in items],
                    "independent_run_count": len(items) if independent else None,
                    "independence_proven_by_distinct_capture_refs": independent,
                    "status": status})
    return out
