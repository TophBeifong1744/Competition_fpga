"""Read-only archive recheck; no F/E temporary run directory or Vivado required.
Requires this repository's pinned B Git objects, Python and NumPy.
"""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import numpy as np
import check as checker
import prepare_extension as pe
from finalize_extension import verify_preparation, wrapper_signature

EXT = Path(__file__).resolve().parent.parent
TASK = EXT.parent


def need(ok, message):
    if not ok:
        raise RuntimeError(message)


def read(path):
    return json.loads(path.read_bytes())


def verify_manifest(root, entries, exclude=()):
    expected = {p for p in entries}
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()}
    need(actual - set(exclude) == expected, "Manifest file membership mismatch")
    for path, record in entries.items():
        data = (root / path).read_bytes()
        need(hashlib.sha256(data).hexdigest() == record["sha256"] and len(data) == record["bytes"],
             "Manifest hash/size mismatch: " + path)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", type=Path, default=EXT / "evidence/run01")
    args = ap.parse_args()
    bundle = args.bundle.resolve()
    verify_preparation()
    if (EXT / "SHA256SUMS.json").is_file():
        verify_manifest(EXT, read(EXT / "SHA256SUMS.json"), ["SHA256SUMS.json"])
    verify_manifest(bundle, read(bundle / "artifact-sha256.json"), ["artifact-sha256.json"])
    index, tree = pe.audit()
    selection = read(bundle / "vectors/selection.json")
    coverage = read(bundle / "coverage.json")
    old = read(TASK / "evidence/run01/check.json")
    cases = selection["selected_cases"]
    need(cases == index["selected_cases"] == coverage["this_round"]["cases"], "New case ID mismatch")
    need(old["covered_case_ids"] == coverage["historical"]["cases"], "Historical case ID mismatch")
    need(not set(cases) & set(old["covered_case_ids"]) and
         set(cases) | set(old["covered_case_ids"]) == set(range(196)), "Coverage union mismatch")
    jobs = selection["jobs"]
    need(len(jobs) == 817 and [(j["case"], j["channel"]) for j in jobs[:-1]] ==
         [(c, ch) for c in cases for ch in range(6)], "Wrong job mapping")
    expected = np.load(bundle / "vectors/expected.npy", allow_pickle=False)
    rows = checker.table(bundle / "simulation/outputs.csv.gz")
    status = checker.table(bundle / "simulation/status.csv.gz")
    result = checker.compare(rows, expected, status, jobs)
    need(result["pass"], "Archived raw integer comparison failed: " + str(result))
    with (bundle / "vectors/inputs.mem").open() as stream:
        words = np.fromiter((int(line, 16) for line in stream), dtype=np.uint64).reshape(817, 1024)
    frames = json.loads(gzip.decompress(
        pe.blob(tree, pe.PREFIX + "evidence/run01/frames.json.gz")))
    flags = {f["case"]: f["candidates"]["wide29"]["flags"]["fft_overflow"] for f in frames}
    frame_hash = {f["case"]: f["npz_sha256"] for f in frames}
    del frames
    for i, case in enumerate(cases):
        payload = pe.blob(tree, pe.PREFIX + f"evidence/run01/case-{case:03d}.npz")
        need(hashlib.sha256(payload).hexdigest() == frame_hash[case], "B frame/NPZ hash mismatch")
        with np.load(io.BytesIO(payload), allow_pickle=False) as data:
            need(data["windowed"].dtype == np.int64 and data["wide29_raw_fft"].dtype == np.int64,
                 "NPZ integers changed")
            codes = ((data["windowed"] << 4) & ((1 << 29) - 1)).astype(np.uint64)
            need(np.array_equal(words[i*6:i*6+6], codes), "Input packing differs from B integers")
            need(np.array_equal(expected[i*6:i*6+6], data["wide29_raw_fft"]), "Golden differs from B raw_fft")
            for channel in range(6):
                need(bool(jobs[i*6+channel]["expected_overflow"]) == bool(flags[case][channel]),
                     "B overflow expectation mismatch")
    need(np.array_equal(expected[-1], expected[0]) and np.array_equal(words[-1], words[0])
         and (jobs[-1]["case"], jobs[-1]["channel"], jobs[-1]["backpressure"]) == (1, 0, True),
         "Wrong repeat mapping")
    log = (bundle / "simulation/simulate.log").read_text()
    need(log.count("PASS FFT29 archive replay: 817 jobs;") == 1 and "Fatal:" not in log
         and "$finish called at time : 60182750 ns" in log, "TB protocol/end marker failed")
    cycles = checker.table(bundle / "simulation/cycles.csv.gz")
    need(cycles.shape == (817, 6) and np.array_equal(cycles[:,0], np.arange(817)), "Cycle order/count failed")
    for entry in read(bundle / "simulation/packing.json"):
        p = bundle / "simulation" / entry["stored_name"]
        payload = p.read_bytes()
        original = gzip.decompress(payload) if p.suffix == ".gz" else payload
        need(hashlib.sha256(payload).hexdigest() == entry["stored_sha256"] and
             hashlib.sha256(original).hexdigest() == entry["original_sha256"] and
             len(original) == entry["original_bytes"], "Lossless log archive mismatch")
    actual_ip = read(bundle / "reports/ss_fft29.xci")["ip_inst"]
    old_ip = read(TASK / "evidence/run01/reports/ss_fft29.xci")["ip_inst"]
    for group in ("component_parameters", "model_parameters"):
        need(actual_ip["parameters"][group] == old_ip["parameters"][group], "IP configuration changed")
    actual_wrapper = wrapper_signature((bundle / "reports/ss_fft29-sim-wrapper.vhd").read_text())
    old_wrapper = wrapper_signature((TASK / "evidence/run01/reports/ss_fft29-wrapper.vhd").read_text())
    need(actual_wrapper[0] == old_wrapper[0] and (actual_wrapper[1], old_wrapper[1]) == (0, 6),
         "Wrapper differs beyond recorded nonfunctional metadata")
    for name in ("tb_fft29.sv", "check.py", "create_sim.tcl"):
        need((bundle / "sources_used" / name).read_bytes() == (EXT / "source" / name).read_bytes(),
             "Actual source differs from candidate")
    per_job = read(bundle / "per-job-results.json")
    need(len(per_job) == 817, "Missing per-job checks")
    for i, row in enumerate(per_job):
        delta = rows[i*1024:(i+1)*1024, 2:] - expected[i]
        need((row["job"], row["case"], row["channel"]) == (i, jobs[i]["case"], jobs[i]["channel"]),
             "Per-job labels differ")
        need(row["mismatches"] == int(np.count_nonzero(delta)) == 0 and
             row["maximum_integer_delta"] == int(np.abs(delta).max()) == 0 and row["overflow"] == 0,
             "Per-job result differs from raw outputs")
    case_results = read(bundle / "per-case-results.json")
    need([r["case"] for r in case_results] == cases and
         all(r["channels"] == list(range(6)) and r["mismatches"] == 0 and
             r["npz_sha256"] == frame_hash[r["case"]] for r in case_results), "Per-case coverage differs")
    print(json.dumps({"status": "PASS_READ_ONLY_ARCHIVE_RECHECK_NOT_NEW_XSIM",
                      "new_cases_from_user_run": 136, "historical_cases": 60, "union_cases": 196,
                      "user_run_jobs": 817, "integer_components": result["integer_components"],
                      "mismatches": result["mismatched_components"], "B_NPZ_bound": 136,
                      "old_155_files_and_preparation_snapshot_unchanged": True,
                      "temporary_run_directory_required": False, "Vivado_started": False,
                      "independent_review": "PENDING_B"}, indent=2))


if __name__ == "__main__":
    main()
