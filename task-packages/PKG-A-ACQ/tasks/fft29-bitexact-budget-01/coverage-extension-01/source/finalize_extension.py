"""Finish a user-run FFT29 replay: bind inputs/IP, compare, archive and merge coverage.
No simulator launch, synthesis, hardware access, Git write or deletion.
"""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import numpy as np
import check as checker
import prepare_extension as pe

EXT = Path(__file__).resolve().parent.parent
TASK = EXT.parent


def need(ok, message):
    if not ok:
        raise RuntimeError(message)


def load(path):
    return json.loads(path.read_bytes())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as f:
        f.write(data)


def dump(path, data):
    write(path, (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode())


def copy(source, dest):
    data = source.read_bytes()
    write(dest, data)
    need(digest(source) == digest(dest), "Source changed during evidence copy: " + str(source))


def run_command(args, out, name):
    command = [str(x) for x in args]
    started = datetime.now(timezone.utc).isoformat()
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    write(out / (name + ".log"), result.stdout)
    dump(out / (name + "-command.json"), {"argv": command, "cwd": str(Path.cwd()),
         "started_at_utc": started, "finished_at_utc": datetime.now(timezone.utc).isoformat(),
         "returncode": result.returncode})
    need(result.returncode == 0, name + " failed; preserve original run and new logs")


def verify_preparation():
    old = load(EXT / "PREPARATION-SHA256.json")
    mapping = load(EXT / "PREPARATION-HISTORY.json")["paths"]
    for entry in old["files"]:
        path = EXT / mapping.get(entry["path"], entry["path"])
        need(digest(path) == entry["sha256"], "Preparation snapshot changed: " + entry["path"])


def wrapper_signature(text):
    text = re.sub(r"--[^\n]*", "", text)
    pattern = r"(?ims)^\s*ATTRIBUTE\s+(?:X_CORE_INFO|CHECK_LICENSE_TYPE|CORE_GENERATION_INFO)\b.*?;"
    text, removed = re.subn(pattern, "", text)
    return re.sub(r"\s+", "", text).lower(), removed


def configuration_check(run, sim, out):
    new_xci = run / "project/fft29_budget.srcs/sources_1/ip/ss_fft29/ss_fft29.xci"
    old_xci = TASK / "evidence/run01/reports/ss_fft29.xci"
    new, old = load(new_xci)["ip_inst"], load(old_xci)["ip_inst"]
    need(new["component_reference"] == old["component_reference"] == "xilinx.com:ip:xfft:9.1",
         "FFT IP version changed")
    need(new["ip_revision"] == old["ip_revision"] == "15", "FFT revision changed")
    for group in ("component_parameters", "model_parameters"):
        need(new["parameters"][group] == old["parameters"][group], group + " changed")
    version = (run / "project/tool-version.txt").read_text()
    need("Vivado v2025.2" in version and "SW Build 6299465" in version and
         "PART=xc7z020clg400-2" in version, "Wrong real tool/device")
    # Follow the actual HDL compiler project files, not merely a proposed source list.
    prj = (sim / "tb_fft29_vlog.prj").read_text()
    sv = re.findall(r'"([^"\n]+\.sv)"', prj)
    need(len(sv) == 1 and (sim / sv[0]).resolve() == (run / "source/tb_fft29.sv").resolve(),
         "Compiled testbench path differs")
    vhdl_prj = (sim / "tb_fft29_vhdl.prj").read_text()
    paths = re.findall(r'"([^"\n]+\.vhd)"', vhdl_prj)
    need(len(paths) == 1, "Unknown generated wrapper list")
    actual_wrapper = (sim / paths[0]).resolve()
    reference_wrapper = TASK / "evidence/run01/reports/ss_fft29-wrapper.vhd"
    actual_sig, actual_removed = wrapper_signature(actual_wrapper.read_text())
    reference_sig, reference_removed = wrapper_signature(reference_wrapper.read_text())
    need(actual_sig == reference_sig and actual_removed == 0 and reference_removed == 6,
         "Wrapper differs beyond the known simulation-only metadata omission")
    compile_log = (sim / "compile.log").read_text()
    need((run / "source/tb_fft29.sv").as_posix() in compile_log and
         actual_wrapper.as_posix() in compile_log, "Compiler did not log the bound sources")
    for name in ("tb_fft29.sv", "check.py", "create_sim.tcl"):
        need((run / "source" / name).read_bytes() == (EXT / "source" / name).read_bytes(),
             "Run used another extension source: " + name)
    need((run / "source/prepare.py").read_bytes() == (TASK / "source/prepare.py").read_bytes(),
         "Original packer was changed")
    need((run / "configuration.json").read_bytes() == (TASK / "configuration.json").read_bytes(),
         "Candidate configuration description changed")
    for source, name in ((new_xci, "ss_fft29.xci"), (actual_wrapper, "ss_fft29-sim-wrapper.vhd"),
                         (run / "project/tool-version.txt", "tool-version.txt"),
                         (run / "project/ip-properties.txt", "ip-properties.txt"),
                         (run / "project/fft29_budget.xpr", "fft29_budget.xpr")):
        copy(source, out / "reports" / name)
    result = {"status": "PASS_IDENTICAL_FFT29_CONFIGURATION", "old_xci_sha256": digest(old_xci),
              "actual_xci_sha256": digest(new_xci), "component_and_model_parameters_exact": True,
              "actual_compiled_tb": str((sim / sv[0]).resolve()), "actual_compiled_wrapper": str(actual_wrapper),
              "compiled_tb_sha256": digest(run / "source/tb_fft29.sv"),
              "compiled_wrapper_sha256": digest(actual_wrapper),
              "wrapper_difference": "Simulation-only wrapper omits 6 declarations/attributes for X_CORE_INFO, CHECK_LICENSE_TYPE, CORE_GENERATION_INFO; remaining code equal",
              "new_synthesis_or_route": False, "historical_resources": "../evidence/run01/reports",
              "configuration_hex": "0x0AAAAB", "clock_MHz": 100, "board_test": "NOT_RUN"}
    dump(out / "configuration-check.json", result)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--screenshot", type=Path)
    args = ap.parse_args()
    run, out = args.run.resolve(), args.out.resolve()
    need(run.is_dir() and not out.exists(), "Run must exist; output must be new")
    need(EXT.resolve() in out.parents and run not in out.parents, "Output must be a new extension evidence directory")
    out.mkdir(parents=True, exist_ok=False)
    dump(out / "invocation.json", {"argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd()),
                                  "started_at_utc": datetime.now(timezone.utc).isoformat(),
                                  "simulator_started_by_this_script": False})
    sim = run / "project/fft29_budget.sim/sim_1/behav/xsim"
    try:
        verify_preparation()
        index, tree = pe.audit()
        dump(out / "input-index.json", index)
        for name, info in load(run / "prepared-sha256.json").items():
            need(digest(run / name) == info["sha256"] and (run / name).stat().st_size == info["bytes"],
                 "Prepared run input/source changed: " + name)
        for entry in index["files"]:
            need(digest(run / "reference" / entry["local"]) == entry["sha256"],
                 "Actual NPZ/index is not the pinned B archive: " + entry["local"])
        for name in ("inputs.mem", "job-count.mem"):
            need((sim / name).read_bytes() == (run / "vectors" / name).read_bytes(),
                 "Actual XSim memory differs from packed input")
        for name in ("inputs.mem", "job-count.mem", "expected.npy", "selection.json"):
            copy(run / "vectors" / name, out / "vectors" / name)
        for name in ("prepare-command.json", "prepare-result.json", "packing-command.json", "packing.log",
                     "prepared-sha256.json", "input-index.json"):
            copy(run / name, out / "preparation" / name)
        for name in ("tb_fft29.sv", "check.py", "create_sim.tcl", "prepare.py"):
            copy(run / "source" / name, out / "sources_used" / name)
        configuration_check(run, sim, out)
        run_command([sys.executable, "-B", EXT / "source/test_extension.py"], out, "checker-tests")
        run_command([sys.executable, "-B", EXT / "source/check.py", "--vectors", out / "vectors",
                     "--simulation", sim, "--out", out / "check.json"], out, "compare")
        run_command([sys.executable, "-B", EXT / "source/collect_simulation.py", "--simulation", sim,
                     "--out", out / "simulation"], out, "collect")
        # Keep actual compiler/elaborator/launcher commands and useful kernel diagnostics.
        for name in ("compile.bat", "elaborate.bat", "simulate.bat", "xsim.ini"):
            copy(sim / name, out / "simulation" / name)
        for name in ("xsimkernel.log", "xsimcrash.log"):
            copy(sim / "xsim.dir/tb_fft29_behav" / name, out / "simulation" / name)
        if args.screenshot:
            copy(args.screenshot, out / "user-run-screenshot.png")
        selection = load(out / "vectors/selection.json")
        result = load(out / "check.json")
        need(selection["selected_cases"] == index["selected_cases"] == result["covered_case_ids"],
             "Executed case IDs do not match the remaining set")
        jobs = selection["jobs"]
        pairs = [(j["case"], j["channel"]) for j in jobs[:-1]]
        need(pairs == [(c, k) for c in index["selected_cases"] for k in range(6)] and len(jobs) == 817,
             "Duplicate/missing/reordered case/channel coverage")
        need((jobs[-1]["case"], jobs[-1]["channel"], jobs[-1]["backpressure"]) == (1, 0, True),
             "Wrong explicit backpressure repeat")
        expected = np.load(out / "vectors/expected.npy", allow_pickle=False)
        rows = checker.table(out / "simulation/outputs.csv.gz")
        actual = rows[:, 2:].reshape(817, 1024, 2)
        status = checker.table(out / "simulation/status.csv.gz")
        with (sim / "inputs.mem").open() as stream:
            words = np.fromiter((int(line, 16) for line in stream), dtype=np.uint64).reshape(817, 1024)
        frames = json.loads(gzip.decompress((run / "reference/evidence/run01/frames.json.gz").read_bytes()))
        npz_flags = {f["case"]: f["candidates"]["wide29"]["flags"]["fft_overflow"] for f in frames}
        frame_hashes = {f["case"]: f["npz_sha256"] for f in frames}
        del frames
        by_job = []
        for position, case in enumerate(index["selected_cases"]):
            npz = run / f"reference/evidence/run01/case-{case:03d}.npz"
            need(digest(npz) == frame_hashes[case], "Frame index/NPZ mismatch")
            with np.load(npz, allow_pickle=False) as data:
                windowed, raw = data["windowed"], data["wide29_raw_fft"]
                need(windowed.dtype == np.int64 and windowed.shape == (6, 1024), "Wrong windowed layout")
                need(raw.dtype == np.int64 and raw.shape == (6, 1024, 2), "Wrong raw_fft layout")
                need(np.all((windowed >= -(1 << 24)) & (windowed < (1 << 24))), "Windowed cannot widen safely")
                widened = windowed << 4
                wanted_words = (widened & ((1 << 29) - 1)).astype(np.uint64)
                start = position * 6
                need(np.array_equal(words[start:start+6], wanted_words), "Integer input widening/packing mismatch")
                need(np.array_equal(expected[start:start+6], raw), "Expected array differs from B raw_fft")
                for channel in range(6):
                    job = start + channel
                    need(bool(jobs[job]["expected_overflow"]) == bool(npz_flags[case][channel]),
                         "Overflow expectation differs from B frame index")
                    delta = actual[job] - raw[channel]
                    by_job.append({"job": job, "case": case, "channel": channel, "backpressure": False,
                        "integer_components": 2048, "mismatches": int(np.count_nonzero(delta)),
                        "maximum_integer_delta": int(np.abs(delta).max()), "overflow": int(status[job, 2])})
        need(np.array_equal(words[-1], words[0]) and np.array_equal(expected[-1], expected[0]),
             "Repeat input/golden not equal to declared first job")
        delta = actual[-1] - expected[0]
        by_job.append({"job": 816, "case": 1, "channel": 0, "backpressure": True,
                       "integer_components": 2048, "mismatches": int(np.count_nonzero(delta)),
                       "maximum_integer_delta": int(np.abs(delta).max()), "overflow": int(status[-1, 2])})
        dump(out / "per-job-results.json", by_job)
        per_case = [{"case": case, "channels": list(range(6)), "unique_transforms": 6,
                     "integer_components": 12288, "mismatches": sum(r["mismatches"] for r in by_job if r["case"] == case and not r["backpressure"]),
                     "maximum_integer_delta": max(r["maximum_integer_delta"] for r in by_job if r["case"] == case and not r["backpressure"]),
                     "npz_sha256": frame_hashes[case]} for case in index["selected_cases"]]
        dump(out / "per-case-results.json", per_case)
        old = load(TASK / "evidence/run01/check.json")
        old_cases, new_cases = set(old["covered_case_ids"]), set(result["covered_case_ids"])
        need(not old_cases & new_cases and old_cases | new_cases == set(range(196)), "Coverage union mismatch")
        need(result["pass"] and all(r["mismatches"] == 0 and r["overflow"] == 0 for r in by_job),
             "Actual integer/protocol comparison failed")
        log = (sim / "simulate.log").read_text()
        need(log.count("PASS FFT29 archive replay: 817 jobs;") == 1 and "$finish called at time : 60182750 ns" in log,
             "Run completion/count differs from the claimed execution")
        coverage = {
            "status": "PASS_ALL_196_ARCHIVED_FORWARD_FFT29_CASES_AUTHOR_CHECK_NOT_ACCEPTANCE",
            "B_source_commit": pe.B_SHA,
            "historical": {"cases": sorted(old_cases), "unique_transforms": 360, "XSim_jobs": 361,
                           "counted_as_new_execution": False,
                           "author_result": "../evidence/run01/check.json",
                           "B_review": "task-packages/PKG-B-ALG/tasks/phat-fixed-03/closeout-01/a29-review-01/README.md"},
            "this_round": {"cases": sorted(new_cases), "case_count": 136, "unique_transforms": 816,
                           "XSim_runs": 1, "XSim_jobs": 817, "extra_backpressure_jobs": 1,
                           "integer_components_unique": 816*1024*2, "integer_components_including_repeat": 817*1024*2,
                           "mismatches": 0, "maximum_integer_delta": 0, "overflow_transforms": 0,
                           "protocol": "TB TLAST/index/status/unknown-data/backpressure checks passed",
                           "simulation_end_ns": 60182750, "operator": "Toph, Vivado GUI"},
            "union": {"case_ids": sorted(old_cases | new_cases), "case_count": 196, "missing_case_ids": [],
                      "overlap_case_ids": [], "unique_transforms": 1176, "unique_integer_components": 1176*1024*2},
            "new_synthesis": False, "new_place_route": False, "board_test": "NOT_RUN",
            "limits": ["Six-channel offline archives only; no physical channel expansion",
                       "No reference25/PHAT/IFFT/tracker/default algorithm changes",
                       "No common-shift RTL, localization accuracy, complete fixed chain or H3 approval",
                       "Pending work-execution delivery check and B independent review"]}
        dump(out / "coverage.json", coverage)
        dump(out / "run-origin.json", {"run": str(run), "XSim_executed_by_user": True,
             "XSim_executed_by_finalizer": False,
             "GUI_commands_from_operation_sheet": [
                 "source E:/fft29-coverage-01/source/create_sim.tcl",
                 "fft29_coverage_create E:/fft29-coverage-01/project E:/fft29-coverage-01/vectors",
                 "run all"],
             "GUI_journal_available": False,
             "command_evidence": "Generated compile/elaborate/simulate .bat and .prj, compiler logs, XCI, tool-version, simulate.log, user screenshot",
             "GUI_command_list_is_not_a_fabricated_journal": True})
        # Every copied raw stream is checked byte-for-byte after collection.
        for entry in load(out / "simulation/packing.json"):
            payload = (out / "simulation" / entry["stored_name"]).read_bytes()
            raw = gzip.decompress(payload) if entry["stored_name"].endswith(".gz") else payload
            need(hashlib.sha256(raw).hexdigest() == entry["original_sha256"] and
                 raw == (sim / entry["original_name"]).read_bytes(), "Raw archive differs from user run")
        dump(out / "result.json", {"status": "PASS_AUTHOR_COVERAGE_EXTENSION_NOT_INDEPENDENT_ACCEPTANCE",
             "finished_at_utc": datetime.now(timezone.utc).isoformat(),
             "new_XSim_runs_started_by_finalizer": 0, "observed_user_run_jobs": 817,
             "cases_new": 136, "cases_union_with_history": 196, "mismatches": 0})
        dump(out / "artifact-sha256.json", {
             p.relative_to(out).as_posix(): {"sha256": digest(p), "bytes": p.stat().st_size}
             for p in sorted(out.rglob("*")) if p.is_file()})
        print("PASS author check: new cases=136, XSim jobs=817, components=1673216, mismatches=0; union=196/196")
    except Exception as error:
        dump(out / "failure.json", {"status": "FINALIZATION_FAILED_KEEP_ALL_EVIDENCE", "error": str(error)})
        raise


if __name__ == "__main__":
    main()
