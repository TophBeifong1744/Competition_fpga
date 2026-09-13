"""Bounded independent review; never modifies the candidate or its results.

Run against a git-archive extraction of REVIEW_SHA, with a new --out directory.
Exit 0 means the checks ran as expected, NOT that the candidate is approved.
The reproduced stopping counterexample is an expected review finding.
"""
import argparse
import hashlib
import importlib.util
import itertools
import json
import math
import os
from pathlib import Path
import platform
import subprocess
import sys
from datetime import datetime, timezone

REVIEW_SHA = "f90d608fdb4aaaa9cfb0c528732f7e0b94530e3c"
OLD_SHA = "773a56cfacab51c9bb7c7e9f9a05c850c7c3e48b"
PACKAGE = "task-packages/PKG-A-ACQ/outsourcing/motor_control_plan"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def expanded_stop(j, speed, assist, brake, energy, delay=0.03):
    # Independent energy balance, expanded to expose both J and 1/J terms.
    v = math.radians(speed)
    net = brake - assist
    if net <= 0:
        return None
    angle = (brake*v*delay + j*v*v/2 + brake*assist*delay*delay/(2*j) + energy)/net
    return math.degrees(angle) + 1.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.repo, a.source, a.out = a.repo.resolve(), a.source.resolve(), a.out.resolve()
    if a.source == a.out or a.source in a.out.parents:
        raise ValueError("Outputs must be outside the candidate package")
    a.out.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()

    def git(*args):
        return subprocess.check_output(["git", "-C", str(a.repo), *args])

    def tree(sha):
        result = {}
        for row in git("ls-tree", "-r", "-z", sha, "--", PACKAGE).split(b"\0"):
            if not row:
                continue
            meta, name = row.split(b"\t", 1)
            mode, kind, oid = meta.decode().split()
            assert mode in ("100644", "100755") and kind == "blob"
            result[name.decode()[len(PACKAGE)+1:]] = oid
        return result

    def protected_files():
        paths = set(git("ls-files", "-m", "-o", "--exclude-standard", "-z").decode().split("\0"))
        paths.update([PACKAGE + "/" + name for name in tree("main")])
        paths.update(["task-packages/PKG-A-ACQ/payload/hardware/turntable-procurement-guide.md",
                      "task-packages/PKG-A-ACQ/payload/hardware/turntable-procurement-publication-20260912.md"])
        return {p: digest((a.repo/p).read_bytes()) for p in sorted(paths)
                if p and (a.repo/p).is_file() and "review-status/motor-f90d608/" not in p}

    protected_before = protected_files()
    current, old = tree(REVIEW_SHA), tree(OLD_SHA)
    source_before = {p.relative_to(a.source).as_posix(): digest(p.read_bytes())
                     for p in a.source.rglob("*") if p.is_file()}
    assert set(source_before) == set(current), "extraction file set differs from pinned commit"
    identities = {name: {"blob": oid, "sha256": digest(git("cat-file", "blob", oid))}
                  for name, oid in current.items()}
    assert all(source_before[n] == item["sha256"] for n, item in identities.items())
    unchanged = [n for n in old if current.get(n) == old[n]]
    assert current["single_axis_reference.md"] == old["motor_plan.md"]
    assert current["single_axis_report.html"] == old["report.html"]
    dump(a.out/"identity.json", {"review_sha": REVIEW_SHA, "historical_sha": OLD_SHA,
         "main_at_start": git("rev-parse", "main").decode().strip(), "files": identities,
         "unchanged_old_paths": unchanged, "historical_document_aliases_byte_identical": True,
         "delta": git("diff", "--name-status", OLD_SHA, REVIEW_SHA, "--", PACKAGE).decode()})

    invocations = []
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONUTF8="1")

    def run(name, args, success=True, expected_error=None):
        t = datetime.now(timezone.utc).isoformat()
        p = subprocess.run(args, cwd=a.source, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
        invocations.append({"name": name, "command": [str(x) for x in args], "started_utc": t,
                            "finished_utc": datetime.now(timezone.utc).isoformat(), "returncode": p.returncode,
                            "stdout": p.stdout, "stderr": p.stderr, "expected_success": success,
                            "expected_error_text": expected_error})
        dump(a.out/"commands.json", invocations)
        assert (p.returncode == 0) == success, name
        if not success:
            assert expected_error and expected_error in p.stdout+p.stderr, name+": unexpected failure reason"

    py = [sys.executable, "-B"]
    run("delivery_integrity", py+["check_delivery.py", "--root", str(a.source), "--report", str(a.out/"delivery.json")])
    run("delivery_positive_negative", py+["test_delivery.py", "--root", str(a.source)])
    run("dual_sizing", py+["size_dual_axis.py", "--out", str(a.out/"sizing")])
    run("single_supervisor", py+["validate_control.py", "--out", str(a.out/"control")])
    run("sizing_overwrite_refusal", py+["size_dual_axis.py", "--out", str(a.out/"sizing")], False, "FileExistsError")
    control_hash = digest((a.out/"control/control_checks.json").read_bytes())
    run("control_overwrite_refusal", py+["validate_control.py", "--out", str(a.out/"control")], False,
        "Refusing to overwrite existing control_checks.json")
    assert control_hash == digest((a.out/"control/control_checks.json").read_bytes())
    run("legacy_wrapper_overwrite_refusal", ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", "run_all.ps1",
        "-PythonPath", sys.executable, "-OutputDirectory", str(a.out/"sizing")], False,
        "Refusing to overwrite an existing evidence directory")

    author_budget = json.loads((a.source/"results/dual_axis_selection_budget.json").read_text())
    reproduced = json.loads((a.out/"sizing/selection_budget.json").read_text())
    ignored = {"executed_utc", "python", "platform"}
    assert {k:v for k,v in author_budget.items() if k not in ignored} == {k:v for k,v in reproduced.items() if k not in ignored}
    controls = json.loads((a.out/"control/control_checks.json").read_text())
    old_controls = json.loads((a.source/"results/control_checks.json").read_text())
    assert controls["checks"] == old_controls["checks"] and controls["pass_count"] == 556
    verification = json.loads((a.source/"results/verification.json").read_text())
    assert verification["script_sha256"] == source_before["simulate.py"]

    sys.dont_write_bytecode = True
    def load(name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    sizing = load("candidate_sizing", a.source/"size_dual_axis.py")
    supervisor = load("candidate_supervisor", a.source/"validate_control.py")
    checks = []
    def check(name, ok):
        checks.append({"name": name, "pass": bool(ok)})
        assert ok, name

    pitch_rows = []
    for m, e, j in itertools.product([.05, .5, 1.], [.005, .01, .02], [.003, .006, .012]):
        gravity = (m+.2)*9.81*e
        demand = j*math.pi/3 + gravity + .14
        check(f"pitch_torque_{m}_{e}_{j}", math.isclose(demand, sizing.pitch_budget(m,e,j)["demand_Nm"], abs_tol=1e-12))
        travel = expanded_stop(j,35,gravity+.14,.8,.01)
        native = sizing.stop_budget(j,35,gravity+.14,.8,.01)
        check(f"pitch_stop_equivalence_{m}_{e}_{j}", math.isclose(travel,native["travel_with_energy_and_tolerance_deg"],abs_tol=1e-10))
        pitch_rows.append({"payload_kg":m,"offset_m":e,"J_kg_m2":j,"travel_deg":travel,"fits_10deg":travel<10})
    yaw_rows = []
    for j in [.01,.025,.04]:
        d = j*math.pi/2+.14
        actual = next(c["demand_Nm"] for c in reproduced["yaw_cases"] if c["inertia_kg_m2"] == j)
        check(f"yaw_torque_{j}", math.isclose(d,actual,abs_tol=1e-12))
        travel = expanded_stop(j,65,.14,.6,.01)
        check(f"yaw_stop_equivalence_{j}", math.isclose(travel,sizing.stop_budget(j,65,.14,.6,.01)["travel_with_energy_and_tolerance_deg"],abs_tol=1e-10))
        yaw_rows.append({"J_kg_m2":j,"travel_deg":travel,"fits_10deg":travel<10})
    failures = [r for r in pitch_rows if not r["fits_10deg"]]
    check("included_pitch_corner_exceeds_10deg", len(failures)>0)
    check("counterexample_respects_parallel_axis_lower_bound", .003 >= 1.2*.02**2)
    # No hardware prediction: zero drive/brake, maximum horizontal CG lever arm.
    gravity_max = 1.2*9.81*.02
    freefall_30ms_deg = math.degrees(.5*gravity_max/.003*.03**2)
    check("gravity_worst_case_upper_bound", math.isclose(gravity_max,.23544,abs_tol=1e-12))
    matching = {}
    for axis, n, speed in [("yaw",4,60),("pitch",6,30)]:
        matching[axis] = {"motor_rpm":speed*n/6,"continuous_motor_Nm":1/(n*.85),
            "short_motor_Nm":1.5/(n*.85),"command_step_deg":1.8/(16*n),
            "step_hz":speed/(1.8/(16*n))}
    check("yaw_motor_rpm", matching["yaw"]["motor_rpm"]==40)
    check("pitch_motor_rpm", matching["pitch"]["motor_rpm"]==30)
    check("yaw_step_hz", math.isclose(matching["yaw"]["step_hz"],2133.3333333333335))
    check("pitch_step_hz", matching["pitch"]["step_hz"]==1600)
    # Independent safety-dominance regression, without adding a dual controller.
    priority_count = 0
    for fault in [{"estop":True},{"limit":True},{"encoder_age":.021},{"heartbeat_age":.101}]:
        for bad in [{"angle":float("nan")},{"frame_time":float("inf")},{"moving":None}]:
            for moving in [False,True]:
                s = supervisor.Supervisor()
                s.stable=[(0,30),(.02,30)]
                kw=dict(now=.04,angle=30,confidence=.9,frame_time=.04,position=0,moving=moving)
                kw.update(bad); kw.update(fault)
                check(f"safety_dominance_{priority_count}", s.update(**kw)=="BRAKE" and s.fault and not s.stable)
                check(f"safety_latch_{priority_count}", s.update(.06,0,.9,.06,0)=="BRAKE")
                priority_count += 1

    # Independent numerical check of the corner, splitting at the brake event.
    j=.003; assist=.37544; brake=.8; v=math.radians(35); q=0.; dt=1e-6
    for _ in range(30000):
        acc=assist/j; q += v*dt+.5*acc*dt*dt; v += acc*dt
    while v > 0:
        acc=(assist-brake)/j; step=min(dt,v/(-acc))
        q += v*step+.5*acc*step*step; v=max(0.,v+acc*step)
    numeric=math.degrees(q+.01/(brake-assist))+1.5
    check("independent_piecewise_integrator_matches_counterexample", abs(numeric-expanded_stop(j,35,assist,brake,.01))<1e-8)
    source_after = {p.relative_to(a.source).as_posix():digest(p.read_bytes()) for p in a.source.rglob("*") if p.is_file()}
    check("candidate_all_bytes_unchanged",source_before==source_after)
    check("shared_materials_unchanged",protected_before==protected_files())
    dump(a.out/"protected-materials.json", {"before_sha256":protected_before,"unchanged":protected_before==protected_files()})
    dump(a.out/"independent.json", {"checks":checks,"pass_count":len(checks),"pitch_stop_grid":pitch_rows,
         "yaw_stop_grid":yaw_rows,"pitch_failing_corners":failures,"matching":matching,
         "maximum_gravity_Nm":gravity_max,"unheld_30ms_gravity_only_displacement_deg":freefall_30ms_deg,
         "counterexample_numeric_deg":numeric,"normal_stop_example_deg":{
             "yaw_65deg_s_net90deg_s2_delay10ms":65*.01+65**2/(2*90),
             "pitch_35deg_s_net60deg_s2_delay10ms":35*.01+35**2/(2*60)},
         "normal_stop_example_status":"illustration using assumed NET deceleration, not guaranteed by command limits",
         "scope":"bounded independent algebra and synthetic logic, no coupled dynamics or hardware"})
    dump(a.out/"summary.json", {"review_sha":REVIEW_SHA,"started_utc":started,
         "finished_utc":datetime.now(timezone.utc).isoformat(),"python":sys.version,"platform":platform.platform(),
         "candidate_file_count":len(current),"delivery":json.loads((a.out/"delivery.json").read_text()),
         "author_budget_reproduced":True,"original_control_check_count":556,"independent_check_count":len(checks),
         "safety_dominance_combinations":priority_count,"pitch_stop_grid_fail_count":len(failures),
         "historical_149_physics_rerun":False,"all_invocations_expected":True,
         "technical_approval":False,"reason":"pitch stop envelope counterexample; see manual review for safety contract"})
    print(json.dumps({"independent_checks_pass":len(checks),"pitch_stop_grid_failures":failures,
                      "technical_approval":False},indent=2))


if __name__ == "__main__":
    main()
