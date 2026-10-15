"""Portable bounded verification runner. Each child has raw command evidence.

No author scripts, no hardware tools, no product edits. See README.md for scope.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

import numpy as np

from reference import schedule

HERE = Path(__file__).resolve().parent
PRODUCT = "dcaf9ef13d1a2ce4fc766b50f08f8a00836ccb37"
ACCEPTED_EXACT = "234e1e9afc0c57ecc048592a3a2e312a33367d6ed746340a58da71fbab4f9d11"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def files_identity(paths):
    return {str(path): digest(path) for path in paths if path.is_file()}


class ChildFailure(Exception):
    def __init__(self, name, code):
        self.code = code if code else 1
        super().__init__(f"substep {name} returned {code}")


class Run:
    def __init__(self, repo, out):
        self.repo, self.out = repo, out
        self.env = dict(os.environ)
        self.env.update({"PYTHONPATH": str(repo / "models/python"), "PYTHONDONTWRITEBYTECODE": "1",
                         "PYTHONUTF8": "1", "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "safe.directory",
                         "GIT_CONFIG_VALUE_0": str(repo).replace("\\", "/")})
        self.records = []

    def child(self, name, command, expected=0, category=None):
        directory = self.out / "commands" / name
        directory.mkdir(parents=True, exist_ok=False)
        inputs = [Path(value) for value in command if Path(value).is_file()]
        record = {"argv": command, "cwd": str(self.repo), "environment_overrides":
                  {key: self.env[key] for key in ("PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "PYTHONUTF8",
                                                  "GIT_CONFIG_COUNT", "GIT_CONFIG_KEY_0", "GIT_CONFIG_VALUE_0")},
                  "input_argument_files_sha256": files_identity(inputs),
                  "asset_files_sha256": files_identity(sorted(HERE.glob("*"))),
                  "expected_exit": expected, "expected_category": category}
        dump(directory / "command.json", record)
        process = subprocess.run(command, cwd=self.repo, env=self.env, capture_output=True)
        (directory / "stdout.txt").write_bytes(process.stdout)
        (directory / "stderr.txt").write_bytes(process.stderr)
        record.update({"exit_code": process.returncode, "stdout_sha256": digest(directory / "stdout.txt"),
                       "stderr_sha256": digest(directory / "stderr.txt")})
        dump(directory / "command.json", record)
        self.records.append({"name": name, "exit_code": process.returncode, "expected_exit": expected,
                             "expected_category": category})
        dump(self.out / "command-summary.json", self.records)
        if process.returncode != expected:
            dump(self.out / "FIRST-FAILURE.json", {"name": name, "exit_code": process.returncode,
                                                   "expected_exit": expected, "classification": "INCONCLUSIVE",
                                                   "raw": str(directory)})
            raise ChildFailure(name, process.returncode)
        if category and category.encode("utf-8") not in process.stdout + process.stderr:
            dump(self.out / "FIRST-FAILURE.json", {"name": name, "classification": "ASSERTION_FAIL",
                                                   "reason": "canary did not hit intended category", "expected": category})
            raise ChildFailure(name + " category", 1)
        return process

    def check(self, name, case, *, result=None, arrays=None, expected=0, category=None):
        command = [sys.executable, "-X", "utf8", "-B", str(HERE / "checker.py"),
                   "--result", str(result or case["out"] / "result.json"),
                   "--arrays", str(arrays or case["out"] / "stages-and-audio.npz"),
                   "--schedule", str(case["schedule"]), "--pcm", str(case["pcm"])]
        if case["long"]:
            command += ["--long"]
        return self.child(name, command, expected, category)


def ensure(condition, detail):
    if not condition:
        raise RuntimeError(detail)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--controlled-failure", action="store_true", help="isolated runner-propagation canary")
    args = parser.parse_args()
    repo, out = args.repo.resolve(), args.out.resolve()
    if out.exists():
        parser.error("OUTPUT_EXISTS: create a new run directory")
    if out == HERE or HERE.is_relative_to(out) or out.is_relative_to(HERE):
        parser.error("OUTPUT_MUST_BE_OUTSIDE_ASSETS")
    out.mkdir(parents=True, exist_ok=False)
    run = Run(repo, out)
    try:
        if args.controlled_failure:
            # Expected=0 is deliberate: this models an unexpected failed child.
            run.child("controlled-child-failure", [sys.executable, "-X", "utf8", "-B", "-c",
                                                  "import sys;print('CONTROLLED_FAILURE_CANARY');sys.exit(7)"])
            raise RuntimeError("controlled failure was swallowed")
        product_files = sorted((repo / "models/python/soundsight_h3_portable").rglob("*"))
        before = files_identity(product_files)
        dump(out / "product-before.json", before)
        ensure(digest(HERE / "accepted-exact-samples.json") == ACCEPTED_EXACT, "accepted exact-table drift")
        provenance = json.loads((HERE / "input-provenance.json").read_text(encoding="utf-8"))
        for name, expected in provenance["asset_sha256"].items():
            ensure(digest(HERE / name) == expected, "fixture identity drift: " + name)
        head = run.child("git-head", ["git", "rev-parse", "HEAD"]).stdout.decode().strip()
        dump(out / "run-identity.json", {"product_sha": PRODUCT, "actual_test_head": head,
                                         "model_actual": "UNKNOWN", "python": sys.version,
                                         "numpy": np.__version__, "assets_sha256": files_identity(sorted(HERE.glob("*")))})
        run.child("python-version", [sys.executable, "-X", "utf8", "-B", "-c",
                                     "import sys,numpy;print(sys.version);print(numpy.__version__)"])
        inputs = out / "inputs"
        inputs.mkdir()
        shutil.copyfile(HERE / "config.json", inputs / "config.json")
        shutil.copyfile(HERE / "long-pcm.npy", inputs / "long-pcm.npy")
        n = np.arange(1024, dtype=np.int64)
        np.save(inputs / "short-pcm.npy", np.asarray([8*n, 16*n, 24*n, 32*n+4096]))
        # Before the first DUT invocation, freeze all test-case and expected rules.
        specs = [("short-e", False, 0, 1032, None), ("short-none", False, 0, None, None),
                 ("short-e-minus-one", False, 0, 1031, None), ("short-e-plus-one", False, 0, 1033, None),
                 ("short-same-fatal", False, 0, 1032, 1032), ("short-earlier-fatal", False, 0, 1032, 1031),
                 ("short-offset-e", False, 32768, 1032, None),
                 ("long-none", True, 0, None, None), ("long-e", True, 0, 4104, None),
                 ("long-offset-e", True, 32768, 4104, None),
                 ("long-cancel-stop", True, 0, 4098, None), ("long-cancel-fatal", True, 0, 4098, 4098),
                 ("long-fallback-stop", True, 0, 3100, None)]
        cases = {}
        for name, long, first, stop, fatal in specs:
            path = inputs / (name + ".json")
            dump(path, schedule(first, long=long, stop=stop, fatal=fatal))
            cases[name] = {"out": out / "runs" / name, "schedule": path,
                           "pcm": inputs / ("long-pcm.npy" if long else "short-pcm.npy"), "long": long}
        dump(out / "EXPECTATIONS-BEFORE-DUT.json", {"contract": "D17-EOF-01 + B-r2/P17 + accepted EXACT-SAMPLES",
                                                    "specs": specs, "first_representative": "short-e",
                                                    "all_input_sha256": files_identity(sorted(inputs.glob("*"))),
                                                    "reference_sha256": digest(HERE / "reference.py"),
                                                    "checker_sha256": digest(HERE / "checker.py")})
        (out / "runs").mkdir()
        for name, *_rest in specs:
            case = cases[name]
            command = [sys.executable, "-X", "utf8", "-B", "-m", "soundsight_h3_portable", "--repo", str(repo),
                       "--config", str(inputs / "config.json"), "--pcm", str(case["pcm"]),
                       "--schedule", str(case["schedule"]), "--manual-angle-q8", "0", "--out", str(case["out"])]
            if name == "short-e-plus-one":
                rejection = run.child("cli-" + name, command, expected=1)
                ensure(b"CONFIG_INCOMPLETE_OR_INVALID: stop_emit" in rejection.stderr, "wrong E+1 rejection reason")
                ensure(not case["out"].exists(), "E+1 must not publish outputs")
            else:
                run.child("cli-" + name, command)
                run.check("check-" + name, case)
        angle_path = out / "angles.json"
        run.child("observe-six-angles", [sys.executable, "-X", "utf8", "-B", str(HERE / "observe_angles.py"),
                                         "--repo", str(repo), "--out", str(angle_path)])
        run.child("check-six-angles", [sys.executable, "-X", "utf8", "-B", str(HERE / "checker.py"), "--angles", str(angle_path)])
        # EOF histories must be byte-value equivalent after accounting for the
        # explicitly new later-end audit. This is unchanged behavior comparison.
        comparisons = []
        for left, right in (("short-none", "short-e"), ("long-none", "long-e")):
            baseline = json.loads((cases[left]["out"] / "result.json").read_text(encoding="utf-8"))
            eof = json.loads((cases[right]["out"] / "result.json").read_text(encoding="utf-8"))
            for field in ("frames", "events", "stage_details", "audio", "observations"):
                ensure(baseline[field] == eof[field], left + "/" + right + " history differs: " + field)
            comparisons.append({"baseline": left, "EOF": right, "fields_identical": ["frames", "events", "stage_details", "audio", "observations"]})
        normal = np.load(cases["long-none"]["out"] / "stages-and-audio.npz", allow_pickle=False)["audio_automatic_raw"]
        fatal = np.load(cases["long-cancel-fatal"]["out"] / "stages-and-audio.npz", allow_pickle=False)["audio_automatic_raw"]
        stop = np.load(cases["long-cancel-stop"]["out"] / "stages-and-audio.npz", allow_pickle=False)["audio_automatic_raw"]
        ensure(np.array_equal(fatal, normal[:4098]), "fatal must retain exact earlier raw PCM prefix")
        ensure(np.array_equal(stop[:4098], normal[:4098]), "STOP must retain exact earlier raw PCM prefix")
        comparisons.append({"cancel_edge": 4098, "fatal_raw_length": len(fatal), "stop_raw_length": len(stop),
                            "prior_prefix_codes_equal": 4098, "stop_tail_codes": stop[4098:].tolist(),
                            "normal_tail_codes": normal[4098:].tolist()})
        dump(out / "history-and-prefix-comparisons.json", comparisons)
        mutations = out / "mutations"
        mutations.mkdir()
        angle_actual = json.loads(angle_path.read_text(encoding="utf-8"))
        for name, operation, category in (
            ("angles-empty", lambda v: v.update(angle_samples=[]), "ANGLE_COUNT"),
            ("angles-missing-one", lambda v: v["angle_samples"].pop(), "ANGLE_COUNT"),
            ("angles-reordered", lambda v: v["angle_samples"].reverse(), "ANGLE_IDENTITY"),
            ("angle-delay", lambda v: v["angle_samples"][0]["delays_q12"].__setitem__(1, -22927), "ANGLE_VALUE"),
            ("angle-pcm", lambda v: v["angle_samples"][0].__setitem__("beam", 1481), "ANGLE_VALUE")):
            value = copy.deepcopy(angle_actual)
            operation(value)
            path = mutations / (name + ".json")
            dump(path, value)
            run.child("canary-" + name, [sys.executable, "-X", "utf8", "-B", str(HERE / "checker.py"), "--angles", str(path)], 1, category)
        case = cases["long-e"]
        original = json.loads((case["out"] / "result.json").read_text(encoding="utf-8"))
        for name, operation, category in (
            ("eof-identity", lambda v: v["eof_stop_audit"]["identity"].__setitem__("generation", 24), "EOF_AUDIT"),
            ("eof-time", lambda v: v["eof_stop_audit"].__setitem__("at", 4103), "EOF_AUDIT"),
            ("eof-control", lambda v: v["eof_stop_audit"].__setitem__("renderer_control_emitted", True), "EOF_AUDIT"),
            ("history-take", lambda v: v["terminations"][3].__setitem__("successful_take_at", 2563), "HISTORY"),
            ("history-binding-event", lambda v: next(e for e in v["events"] if e["unit"] == "result_binding" and e["frame"] == 3).__setitem__("visible_at", 2562), "HISTORY")):
            value = copy.deepcopy(original)
            operation(value)
            path = mutations / (name + ".json")
            dump(path, value)
            run.check("canary-" + name, case, result=path, expected=1, category=category)
        suppressed_case = cases["short-same-fatal"]
        suppressed = json.loads((suppressed_case["out"] / "result.json").read_text(encoding="utf-8"))
        suppressed["eof_stop_audit"]["effective"] = True
        path = mutations / "eof-suppression.json"
        dump(path, suppressed)
        run.check("canary-eof-suppression", suppressed_case, result=path, expected=1, category="EOF_AUDIT")
        arrays = np.load(case["out"] / "stages-and-audio.npz", allow_pickle=False)
        changed = {key: arrays[key].copy() for key in arrays.files}
        changed["audio_automatic_raw"][2563] += 1
        path = mutations / "pcm-one-code.npz"
        np.savez_compressed(path, **changed)
        run.check("canary-pcm-one-code", case, arrays=path, expected=1, category="PCM")
        run.child("canary-runner-failure", [sys.executable, "-X", "utf8", "-B", str(HERE / "runner.py"),
                                            "--repo", str(repo), "--out", str(out / "runner-controlled-failure"),
                                            "--controlled-failure"], 7, "substep controlled-child-failure returned 7")
        after = files_identity(product_files)
        dump(out / "product-after.json", after)
        ensure(before == after, "PRODUCT_CHANGED_DURING_RUN")
        dump(out / "SUMMARY.json", {"status": "FIXED_PENDING_REVIEW", "claim": "OFFLINE_SYNTHETIC_FUNCTIONAL_EVIDENCE_PENDING_NONAUTHOR_REVIEW",
                                    "product_sha": PRODUCT, "test_head": head, "normal_CLI_cases": 12,
                                    "expected_rejected_CLI_cases": 1, "six_ROM_rows": 6, "checker_canaries": 12,
                                    "runner_failure_exit": 7, "product_unchanged": True,
                                    "author_participation": "new assets author; prior accepted mathematical derivation author",
                                    "unmeasured": ["real time", "physical source identity", "production parameters", "hardware", "full FFT/DOA algorithm acceptance"]})
        print("FIXED_PENDING_REVIEW: bounded EOF, PCM/history, six-angle and subprocess canary execution complete")
        return 0
    except ChildFailure as exc:
        print(str(exc), file=sys.stderr)
        return exc.code
    except BaseException:
        (out / "FIRST-FAILURE.txt").write_text(traceback.format_exc(), encoding="utf-8")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
