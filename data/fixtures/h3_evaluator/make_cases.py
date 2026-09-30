"""Build contract-derived synthetic evidence; never inspect evaluator output."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import sys

SPEC = "3d2dfc4cfd6f1fa055257cae3642a3f6e0da8058ad30259c7f64370652576238"
CASES = "03fab6166547441893827bd976b2ffbe4cda3c0572953709ceed2a7b19b222f6"
DECISION = "bb6f4852ee6001814adbe3667a802a587eaa20a0de152a76a363414b146a8d49"
STREAMS = ("frame", "status", "commit", "take", "cancel", "late_error")
FULL_UNITS = (
    ["transport", "frame_domain", "binding"]
    + [f"{name}_{ch}" for ch in range(4) for name in ("mean", "gate_window", "doa_window")]
    + [f"{domain}_{name}_{ch}" for domain in ("gate", "doa") for ch in range(4)
       for name in ("fft", "fixed4")]
    + ["gate_state"]
    + [f"{name}_{pair}" for pair in ("01", "02", "03", "12", "13", "23")
       for name in ("phat", "ifft", "lag")]
    + ["doa", "tracker", "result_binding"])
assert len(FULL_UNITS) == 53


def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def key(run_id, i, start, offset=0):
    return dict(run_id=run_id, boot_id="boot-independent", session_id="session-independent",
                interval_id="interval-independent", epoch=0, frame_index=i,
                start_original_id=start, last_original_id=start + 1023,
                generation=0, algorithm_id="alg-independent", config_id="cfg-independent",
                calibration_id="cal-independent")


def event(k, tag, kind, tick, result=None, **more):
    row = {"event_id": f"{k['run_id']}-{k['frame_index']}-{tag}", "key": k,
           "kind": kind, "at": {"domain": "INDEPENDENT_SYNTHETIC", "epoch": 0, "tick": tick}}
    if result is not None:
        row["result"] = result
    row.update(more)
    return row


def run(run_id, labels, modes=None, angles=None, *, first=128, ttl=12, tail=0):
    """Every label is a fixed 1024/512 original-ID window, independent of modes."""
    modes = modes or {}
    angles = angles or {}
    n = len(labels)
    assert n > 0
    stop = first + 1024 + (n - 1) * 512 + tail
    truth, events, hashes = [], [], []
    for i, label in enumerate(labels):
        start = first + i * 512
        k = key(run_id, i, start)
        hashes.append(digest(k))
        mode = modes.get(i, "fresh")
        target = label == "TARGET"
        truth.append({"start_original_id": start, "label": label, "flags": [],
                      "truth_angle_deg": 0 if target else None,
                      "delta_theta_deg": 0 if target else None})
        last = start + 1023
        events.extend([event(k, "status", "STATUS", last, "OK", unit="transport"),
                       event(k, "numeric", "NUMERIC", last, "VALID")])
        if mode in ("fresh", "late", "invalid-late", "duplicate", "cancel-same", "cancel-unknown", "cancel-after"):
            take_at = last + (ttl if mode == "late" else 4)
            events.extend([event(k, "available", "AVAILABLE", last + 1,
                                 original_id_interval=[last + 1, last + 1]),
                           event(k, "commit", "COMMIT", last + 2, "SUCCESS"),
                           event(k, "take", "TAKE", take_at, "SUCCESS", delivery="FRESH",
                                 consumer_id="consumer-independent", angle_deg=angles.get(i, 0),
                                 original_id_interval=[take_at, take_at])])
            if mode == "invalid-late":
                events.append(event(k, "late-error", "LATE_ERROR", take_at + 1, invalidates_result=True))
            if mode == "duplicate":
                events.append(event(k, "second-take", "TAKE", take_at + 1, "SUCCESS",
                                    delivery="FRESH", consumer_id="consumer-independent",
                                    angle_deg=angles.get(i, 0), original_id_interval=[take_at + 1, take_at + 1]))
            if mode.startswith("cancel-"):
                cancel_tick = take_at + (1 if mode == "cancel-after" else 0)
                c = event(k, "cancel", "CANCEL", cancel_tick)
                if mode == "cancel-same":
                    c["at"]["edge_id"] = events[-1]["at"]["edge_id"] = f"same-{i}"
                events.append(c)
        elif mode in ("reject", "hold"):
            events.append(event(k, "decision", "DECISION", last + 1,
                                "HOLD" if mode == "hold" else "REJECTED"))
        elif mode in ("none", "none-unsealed", "missing-status", "status-unsealed"):
            if mode in ("missing-status", "status-unsealed"):
                events = [e for e in events if e["event_id"] != f"{run_id}-{i}-status"]
        else:
            raise ValueError(mode)
    terminal = [h for i, h in enumerate(hashes) if modes.get(i) not in ("none-unsealed", "status-unsealed")]
    marks = [{"name": name, "sealed": True, "continuous": True, "lost_count": 0,
              "flush_ack": True, "source_epoch": 0, "first_seq": 0,
              "last_seq": max(0, n - 1), "through_original_id": min((1 << 64) - 1, stop + ttl + 2),
              "terminal_keys": terminal} for name in STREAMS]
    return {"run_id": run_id, "environment": "independent-synthetic", "scenario": "single-source",
            "nominal_angle_deg": 0,
            "capture": {"boot_id": "boot-independent", "session_id": "session-independent",
                        "interval_id": "interval-independent", "epoch": 0, "generation": 0,
                        "algorithm_id": "alg-independent", "config_id": "cfg-independent",
                        "calibration_id": "cal-independent", "first_original_id": first,
                        "stop_original_id": stop, "drop_ranges": [], "clip_ranges": [],
                        "flags_sealed": True},
            "window_grid": {"origin_original_id": first, "length_samples": 1024,
                            "hop_samples": 512},
            "truth": {"sealed": True, "windows": truth},
            "algorithm": {"events": events, "required_units": ["transport"]},
            "time_proof": {"basis": "SYNTHETIC_TIME", "consumer_id": "consumer-independent",
                           "T_result": {"value": ttl, "unit": "original_samples"}, "order_edges": []},
            "watermarks": {"streams": marks},
            "target_identity": {"status": "NOT_APPLICABLE"},
            "audio": {"status": "NOT_MEASURABLE"}}


def bundle(case_id, runs):
    return {"schema_version": "EVIDENCE_BUNDLE_V1", "claim_scope": "SYNTHETIC_TEST",
            "evidence_level": "SYNTHETIC", "seal": {"status": "SEALED", "proof_refs": []},
            "policy_ref": {"spec_sha256": SPEC, "cases_sha256": CASES,
                           "decision_sha256": DECISION},
            "preregistration": [{"run_id": r["run_id"], "environment": r["environment"],
                                 "scenario": r["scenario"], "nominal_angle_deg": 0} for r in runs],
            "references": [], "runs": runs}


def main(out):
    out.mkdir(parents=True, exist_ok=False)
    inventory = {}
    def add(name, runs, references=None, formal=False):
        p = out / (name + ".json")
        data = bundle(name, runs)
        if references is not None:
            data["references"] = references
        if formal:
            data["claim_scope"] = "DIRECTION_RUN"
            data["evidence_level"] = "MIXED"  # deliberate adversarial claim over synthetic evidence
            data["seal"] = {"status": "PROVISIONAL", "proof_refs": []}
            data["policy_ref"]["source_ref"] = "identity"
            data["preregistration"][0]["source_ref"] = "identity"
            for field in ("capture", "truth", "algorithm", "time_proof", "watermarks"):
                runs[0][field]["source_ref"] = "identity"
        raw = (json.dumps(data, separators=(",", ":"), sort_keys=True) + "\n").encode()
        p.write_bytes(raw)
        inventory[name] = {"file": p.name, "sha256": hashlib.sha256(raw).hexdigest(),
                           "runs": [r["run_id"] for r in runs]}
    add("c01_zero_n", [run("C01", ["BACKGROUND_PRE"])])
    add("c02_935", [run("C02", ["TARGET"] * 935)])
    add("c03_all_d", [run("C03D", ["TARGET"] * 936, {i: "reject" for i in range(936)})])
    add("c03_all_u", [run("C03U", ["TARGET"] * 936, {i: "none-unsealed" for i in range(936)})])
    for v in (748, 749):
        add(f"c04_v{v}", [run(f"C04-{v}", ["TARGET"] * 936,
                                 {i: "reject" for i in range(v, 936)})])
    for b in (0, 935, 936):
        add(f"c05_b{b}", [run(f"C05-{b}", ["BACKGROUND_PRE"] * b + ["TARGET"],
                                 {i: "reject" for i in range(b)})])
    for f in (10, 11):
        add(f"c06_f{f}", [run(f"C06-{f}", ["BACKGROUND_PRE"] * 1000 + ["TARGET"],
                                 {i: "reject" for i in range(f, 1000)})])
    add("c06_post_f11", [run("C06P", ["TARGET"] + ["BACKGROUND_POST"] * 1000,
                                  {i: "reject" for i in range(1, 990)})])
    add("c07_five_one_fail", [run(f"C07-{j}", ["TARGET"] * 936,
                                   {i: "reject" for i in range(936)} if j == 4 else {})
                                   for j in range(5)])
    add("c08_sixth_fail", [run(f"C08-{j}", ["TARGET"] * 936,
                                 {i: "reject" for i in range(936)} if j == 5 else {})
                                 for j in range(6)])
    add("c09_rank", [run("C09", ["TARGET"] * 5, angles=dict(enumerate([0, 2, 4, 8, 11])))])
    wrap = run("C10", ["TARGET"], angles={0: -179})
    wrap["truth"]["windows"][0]["truth_angle_deg"] = 179
    add("c10_wrap", [wrap])
    uncert = run("C11", ["TARGET"] * 5, angles=dict(enumerate([1, 2, 5, 5, 9])))
    for t in uncert["truth"]["windows"]: t["delta_theta_deg"] = 1
    add("c11_uncertainty", [uncert])
    for bad in (1, 2):
        add(f"c12_bad{bad}", [run(f"C12-{bad}", ["TARGET"] * 20,
                                      angles={i: 16 for i in range(20-bad, 20)})])
    add("c13_hold", [run("C13", ["TARGET"] * 936, {935: "hold"})])
    add("c14_equal_angle", [run("C14", ["TARGET", "TARGET"])])
    add("c15_duplicate", [run("C15", ["TARGET"], {0: "duplicate"})])
    unknown = run("C16", ["TARGET"])
    ghost = copy.deepcopy(next(e for e in unknown["algorithm"]["events"] if e["kind"] == "TAKE"))
    ghost["event_id"] = "ghost-success"; ghost["key"]["session_id"] = "other-session"
    unknown["algorithm"]["events"].append(ghost)
    add("c16_unknown_k", [unknown])
    late_bg = run("C17", ["TARGET", "BACKGROUND_POST"], {1: "reject"})
    tk = next(e for e in late_bg["algorithm"]["events"] if e["event_id"] == "C17-0-take")
    tk["at"]["tick"] = 128 + 1023 + 10; tk["original_id_interval"] = [1161, 1161]
    add("c17_late_target", [late_bg])
    eq = run("C18E", ["TARGET"], ttl=10)
    tk = next(e for e in eq["algorithm"]["events"] if e["kind"] == "TAKE")
    tk["at"]["tick"] = 128 + 1023 + 10
    tk["original_id_interval"] = [tk["at"]["tick"]]*2
    add("c18_equal", [eq])
    late = run("C18L", ["TARGET"], {0: "late"}, ttl=10)
    tk = next(e for e in late["algorithm"]["events"] if e["kind"] == "TAKE")
    tk["at"]["tick"] += 1; tk["original_id_interval"] = [tk["at"]["tick"]]*2
    add("c18_expired", [late])
    # Near-u64 end leaves one full 1024-sample window but overflows expiry.
    near = (1 << 64) - 1025
    add("c19_overflow", [run("C19", ["TARGET"], {0: "none-unsealed"}, first=near, ttl=3)])
    add("c20_status_u", [run("C20U", ["TARGET"], {0: "status-unsealed"})])
    add("c20_status_d", [run("C20D", ["TARGET"], {0: "missing-status"})])
    add("c21_take_u", [run("C21U", ["TARGET"], {0: "none-unsealed"})])
    add("c21_take_d", [run("C21D", ["TARGET"], {0: "none"})])
    add("c22_late_error", [run("C22", ["TARGET"], {0: "invalid-late"})])
    for name in ("cancel-unknown", "cancel-same", "cancel-after"):
        add("c23_" + name, [run("C23-" + name, ["TARGET"], {0: name})])
    ordered = run("C23-ordered", ["TARGET"], {0: "cancel-after"})
    take = next(e for e in ordered["algorithm"]["events"] if e["kind"] == "TAKE")
    cancel = next(e for e in ordered["algorithm"]["events"] if e["kind"] == "CANCEL")
    cancel["at"]["tick"] = take["at"]["tick"]
    cancel["causes"] = [take["event_id"]]
    add("c23_same_tick_ordered", [ordered])
    drop = run("C24D", ["TARGET", "TARGET"], tail=41)
    drop["capture"]["drop_ranges"] = [[drop["capture"]["first_original_id"]+700,
                                         drop["capture"]["first_original_id"]+701]]
    add("c24_drop", [drop])
    clip = run("C24C", ["TARGET", "TARGET"])
    clip["capture"]["clip_ranges"] = [[clip["capture"]["first_original_id"]+700,
                                         clip["capture"]["first_original_id"]+701]]
    add("c24_clip", [clip])
    classes = run("FIVE_CLASSES", ["TARGET", "UNKNOWN", "EXCLUDED", "CHALLENGE", "TARGET"])
    classes["capture"]["drop_ranges"] = [[228, 229]]  # unique first-half coverage of frame 0
    classes["truth"]["windows"][0]["flags"] = ["marker", "guard"]
    classes["truth"]["windows"][2]["flags"] = ["guard"]
    add("grid_five_classes", [classes])
    both = run("INPUT_AND_PERF", ["TARGET"] * 937,
               {i: "reject" for i in range(937)})
    both["capture"]["drop_ranges"] = [[228, 229]]
    add("input_fail_perf_fail", [both])
    add("c25_audio_missing", [run("C25", ["TARGET"])])
    full = run("FULL53", ["TARGET"])
    full["algorithm"]["required_units"] = FULL_UNITS
    kk = key("FULL53", 0, 128)
    for unit in FULL_UNITS[1:]:
        full["algorithm"]["events"].append(event(kk, "status-"+unit, "STATUS", 1151,
                                                    "OK", unit=unit))
    add("full53", [full])
    source = b"independent synthetic source identity; wrong target at same angle\n"
    (out / "identity-source.txt").write_bytes(source)
    mixed = run("MIXED", ["TARGET"])
    mixed["scenario"] = "target-plus-interferer"
    mixed["target_identity"] = {"status": "WRONG_TARGET", "independent_source_ref": "identity"}
    ref = {"id": "identity", "path": "identity-source.txt", "bytes": len(source),
           "sha256": hashlib.sha256(source).hexdigest(), "role": "synthetic_source_identity",
           "producer": "independent_fixture_author"}
    add("mixed_wrong_same_angle", [mixed], [ref])
    formal = copy.deepcopy(full)
    formal["run_id"] = "FORMAL_GUARD"
    for row in formal["algorithm"]["events"]:
        row["key"]["run_id"] = "FORMAL_GUARD"
        row["event_id"] = row["event_id"].replace("FULL53", "FORMAL_GUARD")
    for mark in formal["watermarks"]["streams"]:
        mark["terminal_keys"] = [digest(key("FORMAL_GUARD", 0, 128))]
    add("formal_synthetic_guard", [formal], [ref], formal=True)
    for name, v, u, err in (("r01a", 749, 187, 20), ("r01b", 400, 536, 6)):
        rr = run(name, ["TARGET"] * 936,
                 {i: "none-unsealed" for i in range(v, v+u)},
                 {i: err for i in range(v)})
        add(name, [rr])
    for name, good in (("r01c_equal", 94), ("r01c_fail", 93)):
        rr = run(name, ["TARGET"] * 120,
                 {i: "none-unsealed" for i in range(100, 120)},
                 {i: 0 if i < good else 20 for i in range(100)})
        add(name, [rr])
    rrd = run("R01D", ["TARGET"] * 120,
              {i: "none-unsealed" for i in range(100, 120)},
              {i: 10 for i in range(100)})
    add("r01d_threshold_equal", [rrd])
    rre = run("R01E", ["TARGET"] * 936, angles={i: 20 for i in range(749)})
    for row in rre["watermarks"]["streams"]:
        if row["name"] == "late_error": row["terminal_keys"] = []
    add("r01e_unsealed_v", [rre])
    add("r01f_zero_v", [run("R01F", ["TARGET"] * 936,
                                {i: "none-unsealed" for i in range(936)})])
    (out / "inventory.json").write_text(json.dumps(inventory, indent=2, sort_keys=True)+"\n")
    print(len(inventory), "independent bundles")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
