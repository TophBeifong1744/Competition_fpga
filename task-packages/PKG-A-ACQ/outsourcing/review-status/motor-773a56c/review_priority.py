"""Independent bounded review of C's fault-priority fix; never edits the package."""
import argparse
import importlib.util
import json
import math
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.dont_write_bytecode = True
APPROVED = "773a56cfacab51c9bb7c7e9f9a05c850c7c3e48b"
PREVIOUS = "34164d557314bd25b65be6c4a35e70241f62e81f"
SOURCE = "task-packages/PKG-A-ACQ/outsourcing/motor_control_plan/validate_control.py"

def checks(cls):
    records = []
    def save(name, passed):
        records.append({"name": name, "pass": bool(passed)})
    faults = ({"encoder_age": .021}, {"heartbeat_age": .101},
              {"estop": True}, {"limit": True})
    for fault in faults:
        for moving in (False, True):
            s = cls()
            s.target = 12.
            for t in (0., .02):
                s.update(t, 30., .9, t, 0.)
            state = s.update(.04, math.nan, .9, .04, 0., moving=moving, **fault)
            label = f"{next(iter(fault))}_nan_angle_moving_{moving}"
            save(label, state == "BRAKE" and s.fault and not s.stable and s.target == 12.)
            save(label + "_latches", s.update(.06, 30., .9, .06, 0.) == "BRAKE" and s.fault)
    for fault in ({"estop": True}, {"limit": True}):
        s = cls()
        save(f"{next(iter(fault))}_bad_moving", s.update(0, 30, .9, 0, 0, moving=None, **fault) == "BRAKE" and s.fault)
    for age_field, threshold in (("encoder_age", .02), ("heartbeat_age", .1)):
        for age in (None, "invalid", math.nan, math.inf, True, -1):
            s = cls()
            save(f"{age_field}_invalid_{age!r}_not_confirmed_fault",
                 s.update(0, 30, .9, 0, 0, moving=True, **{age_field: age}) == "DECEL" and not s.fault)
        s = cls()
        save(age_field + "_exact_boundary_not_fault",
             s.update(0, 30, .9, 0, 0, **{age_field: threshold}) == "ACQUIRE" and not s.fault)
    for moving in (False, True):
        s = cls()
        save(f"invalid_acoustic_without_fault_{moving}",
             s.update(0, math.nan, .9, 0, 0, moving=moving) == ("DECEL" if moving else "HOLD") and not s.fault)
    s = cls()
    for t in (0, .02, 2.):
        s.update(t, 30, .9, t, 0)
    save("old_votes_expire", s.state != "MOVE" and len(s.stable) == 1)
    for t in (2.02, 2.04):
        s.update(t, 30, .9, t, 0)
    save("three_fresh_votes_recover", s.state == "MOVE")
    return records

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("Refusing to overwrite review evidence")
    spec = importlib.util.spec_from_file_location("candidate_control", args.package / "validate_control.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    candidate = checks(module.Supervisor)
    repo = args.repo.resolve().as_posix()
    git = ["git", "-c", "safe.directory=" + repo, "-C", repo, "show"]
    actual_source = (args.package / "validate_control.py").read_bytes()
    expected_source = subprocess.check_output(git + [APPROVED + ":" + SOURCE])
    if actual_source != expected_source:
        raise SystemExit("Candidate does not match reviewed Git blob")
    old = {"__name__": "prior_control"}
    exec(compile(subprocess.check_output(git + [PREVIOUS + ":" + SOURCE]), "prior_control.py", "exec"), old)
    previous = checks(old["Supervisor"])
    result = {"reviewed_commit": APPROVED, "prior_commit": PREVIOUS,
              "checked_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
              "scope": "synthetic control only; no physical simulation, RTL or board approval",
              "candidate": candidate, "prior_failed_checks": [r["name"] for r in previous if not r["pass"]],
              "pass_count": sum(r["pass"] for r in candidate),
              "fail_count": sum(not r["pass"] for r in candidate)}
    with args.output.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2)
    print(json.dumps({key: result[key] for key in ("pass_count", "fail_count", "prior_failed_checks")}))
    raise SystemExit(1 if result["fail_count"] else 0)

if __name__ == "__main__":
    main()
