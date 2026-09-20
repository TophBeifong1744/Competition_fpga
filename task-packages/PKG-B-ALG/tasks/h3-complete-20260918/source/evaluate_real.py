"""Evaluate the frozen presence candidate on already approved diagnostic inputs.

No P50/P95, wrong-direction rate, target-presence accuracy or SNR is computed:
the inputs do not have trustworthy frame-level truth for those metrics.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

from fixed_golden import FixedTracker
from presence import evaluate as presence


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError(args.out)
    root = args.repo.resolve()
    package = Path(__file__).resolve().parents[1]
    config = json.loads((package / "config.json").read_text(encoding="utf-8"))
    track = root / "task-packages/PKG-B-ALG/tasks/four-channel-track-01"
    reader = load_module("h3_reader", root / "task-packages/PKG-B-ALG/payload/model/python/h1_reader.py")
    track_config = json.loads((track / "config.json").read_text(encoding="utf-8"))
    reports = []
    frame_records = []
    for item in track_config["recordings"]:
        recording = reader.ReaderSession().load(root / item["directory"])
        frozen = json.loads((track / "evidence/run02" / f"{item['label']}-frames.json").read_text(encoding="utf-8"))
        tracker = FixedTracker()
        counts = Counter()
        for row in frozen:
            pcm = recording.samples[row["row_start"]:row["row_stop"]]
            gate = presence(pcm, **{k: config["presence_gate"][k] for k in
                                   ("rms_min_codes", "peak_min_codes", "minimum_active_channels")})
            numeric = bool(row["numeric_candidate_valid"])
            angle = row["projection"].get("advisory_azimuth_deg")
            angle_q8 = None if angle is None else round(float(angle) * 256)
            accepted_candidate = gate["present"] and numeric
            tracked = tracker.update(int(row["last_sample_id"]) + 1, angle_q8, accepted_candidate)
            direction_accepted = bool(tracked["fresh_valid"])
            counts.update(presence_present=gate["present"], numeric_candidate=numeric,
                          accepted_candidate=accepted_candidate, fresh_direction=direction_accepted)
            frame_records.append({"recording": item["label"], "frame_index": row["frame_index"],
                                  "first_sample_id": row["first_sample_id"], "last_sample_id": row["last_sample_id"],
                                  "presence": gate, "numeric_candidate": numeric,
                                  "candidate_for_tracker": accepted_candidate,
                                  "direction_acceptance": tracked})
        reports.append({"recording": item["label"], "frames": len(frozen), "counts": dict(counts),
                        "label_quality": "diagnostic_no_trustworthy_frame_truth",
                        "direction_p50_deg": None, "direction_p95_deg": None,
                        "valid_output_ratio": None, "wrong_direction_ratio": None,
                        "objective_audio_improvement": None})
    payload = {"status": "PASS_DIAGNOSTIC_EXECUTION_NOT_METRIC_ACCEPTANCE", "thresholds": config["presence_gate"],
               "recordings": reports,
               "audio": {"existing_three_way_source": "task-packages/PKG-B-ALG/tasks/four-channel-track-01/audio-01/evidence/run02/audio",
                         "same_input_clock_and_common_gain": "previously limited-approved at f364a023; not rerun here",
                         "single_manual_auto": True, "objective_metric": "NOT_RUN_NO_TARGET_INTERFERENCE_REFERENCE"},
               "not_run": ["presence accuracy", "direction P50/P95", "valid output ratio against truth",
                           "wrong-direction rate against truth", "SNR/SI-SDR/audio benefit"]}
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "frames.json").write_text(json.dumps(frame_records, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    (args.out / "summary.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    hashes = {p.name: sha(p) for p in sorted(args.out.iterdir()) if p.is_file()}
    (args.out / "SHA256.json").write_text(json.dumps(hashes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "recordings": reports}, ensure_ascii=False))


if __name__ == "__main__":
    main()
