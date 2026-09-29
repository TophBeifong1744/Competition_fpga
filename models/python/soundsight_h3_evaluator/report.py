"""Multi-axis claim reporting without converting missing evidence into failure events."""

from __future__ import annotations

from .bundle import BundleError, portable_link, require
from .events import resolve_events
from .grid import planned_windows
from .metrics import score_cells, score_run

SPEC_SHA256 = "3d2dfc4cfd6f1fa055257cae3642a3f6e0da8058ad30259c7f64370652576238"
CASES_SHA256 = "03fab6166547441893827bd976b2ffbe4cda3c0572953709ceed2a7b19b222f6"
DECISION_SHA256 = "bb6f4852ee6001814adbe3667a802a587eaa20a0de152a76a363414b146a8d49"


def _hex_identity(value, length: int) -> bool:
    return (isinstance(value, str) and len(value) == length and
            all(ch in "0123456789abcdef" for ch in value))


def evaluate(bundle: dict, verified: list[dict]) -> dict:
    policy = bundle["policy_ref"]
    for name, expected in (("spec_sha256", SPEC_SHA256), ("cases_sha256", CASES_SHA256),
                           ("decision_sha256", DECISION_SHA256)):
        require(policy.get(name) == expected, f"FROZEN_CONTRACT_MISMATCH:{name}")
    for forbidden in ("metrics", "decision", "P50", "V", "PASS"):
        require(forbidden not in bundle, f"INPUT_MUST_NOT_PRECOMPUTE_RESULT:{forbidden}")
    results = []
    scope = bundle["claim_scope"]
    for run in bundle["runs"]:
        for forbidden in ("metrics", "decision", "P50", "V", "PASS"):
            require(forbidden not in run, f"RUN_MUST_NOT_PRECOMPUTE_RESULT:{run['run_id']}:{forbidden}")
        grid = planned_windows(run)
        if grid["M"] is None:
            outcomes, issues = {}, []
        else:
            outcomes, issues = resolve_events(run, grid["windows"], scope != "SYNTHETIC_TEST",
                                              {ref["id"] for ref in bundle["references"]})
        result = score_run(run, grid, outcomes, issues, scope,
                           {ref["id"] for ref in bundle["references"]})
        result["portable_link"] = portable_link(run, verified, grid["M"])
        results.append(result)
    cells = score_cells(bundle["runs"], results, scope)
    refs = {ref["id"]: ref for ref in bundle["references"]}
    policy_blockers = []
    if scope != "SYNTHETIC_TEST":
        for slot in bundle["preregistration"]:
            if not isinstance(slot.get("source_ref"), str) or slot["source_ref"] not in refs:
                policy_blockers.append("PREREGISTRATION_SOURCE_UNBOUND:" + slot["run_id"])
        if not _hex_identity(policy.get("algorithm_commit"), 40):
            policy_blockers.append("POLICY_IDENTITY_MISSING_OR_INVALID:algorithm_commit")
        for name in ("config_sha256", "calibration_sha256"):
            if not _hex_identity(policy.get(name), 64):
                policy_blockers.append("POLICY_IDENTITY_MISSING_OR_INVALID:" + name)
        if not isinstance(policy.get("p1_p4_policy_ref"), str):
            policy_blockers.append("POLICY_IDENTITY_MISSING:p1_p4_policy_ref")
        if not isinstance(policy.get("p1_p4_policy_ref"), str) or policy["p1_p4_policy_ref"] not in refs:
            policy_blockers.append("P1_P4_POLICY_ORIGINAL_BYTES_UNBOUND")
        for name, expected in (("spec_ref", SPEC_SHA256), ("cases_ref", CASES_SHA256),
                               ("decision_ref", DECISION_SHA256)):
            ref_id = policy.get(name)
            ref = refs.get(ref_id) if isinstance(ref_id, str) else None
            if not ref or ref["sha256"] != expected:
                policy_blockers.append("FROZEN_CONTRACT_ORIGINAL_BYTES_UNBOUND:" + name)
        for run in bundle["runs"]:
            capture = run["capture"]
            for field, policy_field in (("algorithm_id", "algorithm_commit"),
                                        ("config_id", "config_sha256"),
                                        ("calibration_id", "calibration_sha256")):
                if capture.get(field) != policy.get(policy_field):
                    policy_blockers.append(f"RUN_POLICY_IDENTITY_UNBOUND:{run['run_id']}:{field}")
            clip = capture.get("clip_policy")
            if (isinstance(clip, dict) and clip.get("status") == "FROZEN" and
                    (not isinstance(clip.get("source_ref"), str) or clip["source_ref"] not in refs)):
                policy_blockers.append(f"CLIP_POLICY_SOURCE_UNBOUND:{run['run_id']}")
        if bundle["seal"]["status"] != "SEALED":
            policy_blockers.append("PREREGISTRATION_NOT_SEALED")
        if any(run["scenario"] != "single-source" for run in bundle["runs"]):
            for name in ("target_policy_b_ref", "target_policy_a_ref", "target_selector_sha256"):
                if not isinstance(policy.get(name), str) or not policy[name]:
                    policy_blockers.append("TARGET_POLICY_OR_IMPLEMENTATION_MISSING:" + name)
            if not _hex_identity(policy.get("target_selector_sha256"), 64):
                policy_blockers.append("TARGET_SELECTOR_IDENTITY_INVALID")
            for name in ("target_policy_b_ref", "target_policy_a_ref"):
                if not isinstance(policy.get(name), str) or policy[name] not in refs:
                    policy_blockers.append("TARGET_POLICY_ORIGINAL_BYTES_UNBOUND:" + name)
    states = [item["decision"]["status"] for item in results]
    if scope == "SYNTHETIC_TEST":
        final = "SYNTHETIC_TEST_ONLY"
    elif scope == "DIRECTION_RUN":
        final = states[0]
    else:
        cell_states = [item["status"] for item in cells]
        if "FAIL" in cell_states:
            final = "FAIL"
        elif "EVIDENCE_INSUFFICIENT" in cell_states:
            final = "EVIDENCE_INSUFFICIENT"
        elif "INCONCLUSIVE" in cell_states:
            final = "INCONCLUSIVE"
        else:
            final = "PASS"
        if scope == "P1_P4_BATCH" and final == "PASS":
            # Audio measurement qualification is not frozen or implemented in this batch.
            final = "EVIDENCE_INSUFFICIENT"
    if scope != "SYNTHETIC_TEST" and policy_blockers and final == "PASS":
        final = "EVIDENCE_INSUFFICIENT"
    return {"schema_version": "H3_EVALUATION_REPORT_V1", "claim_scope": scope,
            "evidence_level": bundle["evidence_level"], "input_seal": bundle["seal"],
            "status": final, "policy_qualification": {"status": "EVIDENCE_INSUFFICIENT" if policy_blockers
                else "BOUND", "blockers": policy_blockers}, "runs": results, "cells": cells,
            "limitations": ["OFFLINE_EVIDENCE_CONSUMER_ONLY", "NO_ALGORITHM_EXECUTION",
                            "NO_REAL_TIME_INFERENCE_FROM_SYNTHETIC_TIME",
                            "AUDIO_SNR_MEASUREMENT_NOT_IMPLEMENTED"]}
