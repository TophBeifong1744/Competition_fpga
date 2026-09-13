"""Independent bounded B1/B2 review. B2 semantics require manual review.

Use a fresh --out outside an exact git-archive extraction of REVIEW_SHA.
Never changes the candidate. Does not run motors, hardware or old dynamics.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import platform
import random
import shutil
import subprocess
import sys
import tempfile
import zipfile

REVIEW_SHA = "407849e3d18e0a6e98a2716c7e5342afb1ea8581"
OLD_SHA = "f90d608fdb4aaaa9cfb0c528732f7e0b94530e3c"
PACKAGE = "task-packages/PKG-A-ACQ/outsourcing/motor_control_plan"
RECORD = "task-packages/PKG-A-ACQ/outsourcing/review-status/motor-407849e"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False)+"\n", encoding="utf-8", newline="\n")


def reference(j, v, a, b, energy=.01, delay=.03):
    w = math.radians(v)
    return math.degrees((b*w*delay+j*w*w/2+b*a*delay*delay/(2*j)+energy)/(b-a))+1.5


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    repo, source, out = args.repo.resolve(), args.source.resolve(), args.out.resolve()
    assert out != source and source not in out.parents
    out.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    def git(*a):
        return subprocess.check_output(["git", "-C", str(repo), *a])
    def tree(commit):
        result = {}
        for row in git("ls-tree", "-r", "-z", commit, "--", PACKAGE).split(b"\0"):
            if row:
                meta, path = row.split(b"\t",1)
                mode, kind, oid = meta.decode().split()
                assert kind == "blob" and mode in ("100644","100755")
                result[path.decode()[len(PACKAGE)+1:]] = oid
        return result
    def hashes(root):
        return {p.relative_to(root).as_posix():sha(p.read_bytes()) for p in root.rglob("*") if p.is_file()}
    def protected():
        paths=set(git("ls-files","-m","-o","--exclude-standard","-z").decode().split("\0"))
        paths.update(git("ls-files","-z","--","task-packages/PKG-A-ACQ/outsourcing/review-status/motor-f90d608",
                         "task-packages/PKG-A-ACQ/outsourcing/review-status/motor-773a56c",
                         "task-packages/PKG-A-ACQ/payload/hardware").decode().split("\0"))
        return {p:sha((repo/p).read_bytes()) for p in sorted(paths)
                if p and not p.startswith(RECORD+"/") and (repo/p).is_file()}
    before = hashes(source)
    preserved = protected()
    current, old = tree(REVIEW_SHA), tree(OLD_SHA)
    assert set(before)==set(current)
    identities={n:{"git_blob":oid,"sha256":sha(git("cat-file","blob",oid))} for n,oid in current.items()}
    assert all(before[n]==r["sha256"] for n,r in identities.items())
    historical=[n for n in old if n.startswith("results/") or n.startswith("single_axis_") or n in ("simulate.py","validate_control.py","test_delivery.py","run_all.ps1")]
    assert all(current[n]==old[n] for n in historical)
    dump(out/"identity.json",{"review_sha":REVIEW_SHA,"previous_sha":OLD_SHA,
         "main_at_start":git("rev-parse","main").decode().strip(),"files":identities,
         "unchanged_historical_files":historical,"delta":git("diff","--name-status",OLD_SHA,REVIEW_SHA,"--",PACKAGE).decode()})

    records=[]
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE="1",PYTHONUTF8="1")
    def run(name,command,expected=0,marker=None):
        t=datetime.now(timezone.utc).isoformat()
        p=subprocess.run(command,cwd=source,env=env,capture_output=True,text=True,encoding="utf-8",errors="replace")
        item={"name":name,"command":[str(c) for c in command],"started_utc":t,
              "finished_utc":datetime.now(timezone.utc).isoformat(),"exit_code":p.returncode,
              "stdout":p.stdout,"stderr":p.stderr,"expected_exit":expected,"expected_marker":marker}
        records.append(item); dump(out/"commands.json",records)
        assert p.returncode==expected, name
        if marker: assert marker in p.stdout+p.stderr, name+": unexpected failure cause"
        return p
    py=[sys.executable,"-B"]
    run("sizing",py+["size_dual_axis.py","--out",str(out/"sizing")])
    run("author_budget_regression",py+["test_stop_budget.py"],marker="Ran 5 tests")
    run("control",py+["validate_control.py","--out",str(out/"control")],marker="556 supervisory checks PASS")
    run("delivery",py+["check_delivery.py","--root",str(source),"--report",str(out/"delivery.json")])
    run("author_delivery_negative",py+["test_delivery.py","--root",str(source)])
    output_before={"sizing":hashes(out/"sizing"),"control":hashes(out/"control")}
    run("sizing_overwrite",py+["size_dual_axis.py","--out",str(out/"sizing")],1,"FileExistsError")
    run("control_overwrite",py+["validate_control.py","--out",str(out/"control")],1,"Refusing to overwrite existing control_checks.json")
    run("legacy_wrapper_overwrite",["powershell.exe","-NoProfile","-ExecutionPolicy","Bypass","-File","run_all.ps1",
        "-PythonPath",sys.executable,"-OutputDirectory",str(out/"sizing")],1,"Refusing to overwrite an existing evidence directory")
    assert output_before=={"sizing":hashes(out/"sizing"),"control":hashes(out/"control")}

    budget=json.loads((out/"sizing/selection_budget.json").read_text())
    original=json.loads((source/"results/revision_b1_b2/sizing/selection_budget.json").read_text())
    ignored={"executed_utc","python","platform"}
    assert {k:v for k,v in budget.items() if k not in ignored}=={k:v for k,v in original.items() if k not in ignored}
    controls=json.loads((out/"control/control_checks.json").read_text())
    assert controls["checks"]==json.loads((source/"results/revision_b1_b2/control/control_checks.json").read_text())["checks"]
    spec=importlib.util.spec_from_file_location("candidate_budget",source/"size_dual_axis.py")
    module=importlib.util.module_from_spec(spec); sys.dont_write_bytecode=True; spec.loader.exec_module(module)
    checks=[]
    def check(name,ok):
        checks.append({"name":name,"pass":bool(ok)})
        assert ok,name
    grids={}; sensitivity={}; rng=random.Random(407849)
    for axis,lo,hi,v,a,b,wanted in [("yaw",.01,.04,65,.14,.6,8.612838097186728),
                                  ("pitch",.004,.012,35,.37544,.8,9.48878799990562)]:
        endpoints=[reference(j,v,a,b) for j in (lo,hi)]
        bound=max(endpoints)
        check(axis+"_expected_bound",abs(bound-wanted)<1e-11)
        check(axis+"_convex_coefficient_positive",b*a*.03**2/(b-a)>0)
        # Stationary point is a MINIMUM; endpoints cover the continuous interval.
        stationary=.03*math.sqrt(b*a)/math.radians(v)
        max_error=0.; max_observed=0.
        for i in range(2001):
            j=lo+(hi-lo)*i/2000
            actual=module.stop_budget(j,v,a,b,.01)["travel_with_energy_and_tolerance_deg"]
            max_error=max(max_error,abs(actual-reference(j,v,a,b)))
            max_observed=max(max_observed,actual)
        check(axis+"_independent_2001_points",max_error<1e-10 and max_observed<=bound+1e-10)
        sampled_max=0.
        for _ in range(512):
            j=rng.uniform(lo,hi); speed=rng.uniform(0,v); assist=rng.uniform(0,a)
            brake=rng.uniform(b,b*2); energy=rng.uniform(0,.01); delay=rng.uniform(0,.03)
            sampled_max=max(sampled_max,reference(j,speed,assist,brake,energy,delay))
        check(axis+"_all_parameter_interior_samples",sampled_max<=bound+1e-10)
        grids[axis]={"interval":[lo,hi],"endpoints_deg":endpoints,"max_deg":bound,
                     "stationary_minimum_J":stationary,"independent_point_count":2001,
                     "maximum_formula_difference_deg":max_error,"interior_parameter_samples":512}
        j=lo; w=math.radians(v); net=b-a
        quadratic=b*a/(2*j); linear=b*w; constant=j*w*w/2+.01-math.radians(8.5)*net
        delay_limit=(-linear+math.sqrt(linear*linear-4*quadratic*constant))/(2*quadratic)
        sensitivity[axis]={"lowest_J":j,"rigid_speed_at_brake_engagement_deg_s":v+math.degrees(a/j*.03),
                           "delay_at_10deg_other_assumptions_fixed_s":delay_limit}
    for group in ("pitch_stop_cases","yaw_stop_cases","historical_stop_cases"):
        for i,row in enumerate(budget[group]):
            ref=reference(row["J_kg_m2"],row["initial_speed_deg_s"],row["assist_Nm"],row["brake_min_Nm"],row["stored_energy_J"])
            check(f"{group}_{i}",abs(ref-row["travel_with_energy_and_tolerance_deg"])<1e-10 and row["pass_budget"]==(ref<10))
    check("historical_failure_is_retained",budget["historical_envelope_pass"] is False and
          sum(not r["pass_budget"] for r in budget["historical_stop_cases"])==1 and
          abs(budget["retained_low_inertia_failure"]["travel_with_energy_and_tolerance_deg"]-10.983614837439264)<1e-10)
    check("new_stop_cases_all_pass",all(r["pass_budget"] for r in budget["pitch_stop_cases"]+budget["yaw_stop_cases"]))
    check("static_hold_factor_two",.8>=2*.37544)

    # Independently inspect the actual reasons of corrupt-delivery process exits.
    negative=[]
    with tempfile.TemporaryDirectory(prefix="delivery-negative-",dir=out) as tmp:
        copy=Path(tmp)/"package"; shutil.copytree(source,copy)
        manifest_data=(copy/"manifest.json").read_bytes()
        corrupt=[("missing_log","results/run.log",None,False,"missing: results/run.log"),
                 ("wrong_hash","README.md",(copy/"README.md").read_bytes()+b"X",False,"hash: README.md"),
                 ("bad_png","results/motion.png",b"bad png",True,"decode: results/motion.png"),
                 ("truncated_npz","results/traces.npz",(copy/"results/traces.npz").read_bytes()[:100],True,"decode: results/traces.npz")]
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,"w") as z:z.writestr("array.npy",b"invalid NPY")
        corrupt.append(("bad_array","results/full_range.npz",buf.getvalue(),True,"decode: results/full_range.npz"))
        for label,name,replacement,rehash,expected in corrupt:
            path=copy/name; raw=path.read_bytes()
            if replacement is None:path.unlink()
            else:path.write_bytes(replacement)
            if rehash:
                manifest=json.loads(manifest_data);manifest["files"][name]=sha(replacement);dump(copy/"manifest.json",manifest)
            p=run("independent_"+label,py+["check_delivery.py","--root",str(copy)],1,expected)
            result=json.loads(p.stdout)
            check(label+"_real_rejection",result["pass"] is False and any(expected in e for e in result["errors"]))
            negative.append({"name":label,"exit_code":p.returncode,"errors":result["errors"]})
            path.write_bytes(raw);(copy/"manifest.json").write_bytes(manifest_data)
        run("independent_restored_package",py+["check_delivery.py","--root",str(copy)])
    check("candidate_unchanged",before==hashes(source))
    check("protected_shared_material_unchanged",preserved==protected())
    dump(out/"protected-materials.json",{"sha256":preserved,"unchanged":True})
    dump(out/"independent.json",{"checks":checks,"pass_count":len(checks),"intervals":grids,
         "sensitivity_only_not_hardware":sensitivity,"negative_exit_reasons":negative,
         "scope":"conditional rigid stopping envelope only; B2 table manually reviewed, not implemented"})
    dump(out/"summary.json",{"review_sha":REVIEW_SHA,"started_utc":started,"finished_utc":datetime.now(timezone.utc).isoformat(),
         "python":sys.version,"platform":platform.platform(),"package_files":len(current),
         "delivery":json.loads((out/"delivery.json").read_text()),"author_budget_tests":5,"control_checks":556,
         "author_delivery_cases":7,"independent_rejection_causes":5,"overwrite_protections":3,
         "independent_assertions":len(checks),"budget_reproduced_exact_except_metadata":True,
         "historical_files_preserved":True,"B1_conditional_calculation_pass":True,
         "B2_status":"manual review only; see README", "physics_or_hardware_run":False})
    print(json.dumps({"assertions":len(checks),"intervals":grids,"sensitivity":sensitivity},indent=2))


if __name__=="__main__":
    main()
