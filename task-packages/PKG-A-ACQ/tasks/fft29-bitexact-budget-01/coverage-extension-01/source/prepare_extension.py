"""Pinned remaining-case preparation. No Vivado launch, network, Git writes or acoustic synthesis."""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

EXT = Path(__file__).resolve().parent.parent
TASK = EXT.parent
ROOT = TASK.parents[3]
BASELINE = "e670eef5de66e85981db8880bee6d41d9afb3a18"
B_SHA = "bff45e7bbedab321fc4815e1432f1575c750edc4"
PREFIX = "task-packages/PKG-B-ALG/tasks/phat-fixed-03/dynamic-range/"


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def save_json(path, obj):
    save(path, (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


def git(*args):
    env = dict(os.environ, GIT_NO_LAZY_FETCH="1", GIT_TERMINAL_PROMPT="0")
    return subprocess.check_output(
        ["git", "-c", "core.longpaths=true", "-C", str(ROOT), *args], env=env)


def blob(tree, rel):
    require(rel in tree, "Path missing in fixed B commit: " + rel)
    oid = tree[rel]
    local = ROOT / rel
    # Current archive can be reused ONLY if its blob ID matches the fixed commit.
    data = local.read_bytes() if local.is_file() else git("cat-file", "blob", oid)
    actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    if actual != oid:
        data = git("cat-file", "blob", oid)
        actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    require(actual == oid, "Git blob mismatch: " + rel)
    return data


def audit():
    git("merge-base", "--is-ancestor", BASELINE, "HEAD")
    task_rel = TASK.relative_to(ROOT).as_posix()
    changed = git("diff", "--name-only", BASELINE, "HEAD", "--", task_rel).decode().splitlines()
    require(all(p.startswith(task_rel + "/coverage-extension-01/") for p in changed),
            "Historical FFT29 task changed since supplied baseline; review first")
    require(git("show", BASELINE + ":" + task_rel + "/SHA256SUMS.json") ==
            (TASK / "SHA256SUMS.json").read_bytes(), "Historical manifest differs from baseline")
    old_manifest = json.loads((TASK / "SHA256SUMS.json").read_bytes())
    for name, info in old_manifest.items():
        data = (TASK / name).read_bytes()
        require(sha(data) == info["sha256"] and len(data) == info["bytes"], "Old evidence changed: " + name)
    selection = json.loads((TASK / "evidence/run01/vectors/selection.json").read_bytes())
    check = json.loads((TASK / "evidence/run01/check.json").read_bytes())
    old = selection["selected_cases"]
    remaining = sorted(set(range(196)) - set(old))
    require(len(old) == len(set(old)) == 60 and len(remaining) == 136, "Wrong old/remaining case counts")
    require(old == check["covered_case_ids"], "Old selection/check case mismatch")
    require(remaining == selection["unselected_cases"] == check["not_covered_case_ids"], "Remaining case mismatch")
    require(check["pass"] and check["mismatched_components"] == 0 and check["transform_count"] == 361,
            "Old historical result is not the approved 361-job run")
    expected_old = [(case, channel) for case in old for channel in range(6)]
    require([(j["case"], j["channel"]) for j in selection["jobs"][:-1]] == expected_old,
            "Historical case/channel coverage mismatch")
    require(selection["source_commit"] == check["source_commit"] == B_SHA, "Historical B SHA mismatch")
    tree = {}
    for entry in git("ls-tree", "-r", "-z", B_SHA, "--", PREFIX).split(b"\0"):
        if entry:
            meta, name = entry.split(b"\t", 1)
            tree[name.decode()] = meta.split()[2].decode()
    manifest = json.loads(blob(tree, PREFIX + "manifest.json"))
    npz_paths = {PREFIX + f"evidence/run01/case-{case:03d}.npz" for case in range(196)}
    require(npz_paths <= tree.keys(), "Fixed B tree does not contain all 196 NPZ paths")
    small = ["manifest.json", "evidence/run01/frames.json.gz", "evidence/run01/packing.json"]
    names = small + [f"evidence/run01/case-{case:03d}.npz" for case in remaining]
    records = []
    for rel in names:
        data = blob(tree, PREFIX + rel)
        digest = sha(data)
        if rel in manifest:
            require(digest == manifest[rel], "B manifest hash mismatch: " + rel)
        if rel.endswith("frames.json.gz"):
            require(digest == sha((TASK / "reference/b-dynamic-range" / rel).read_bytes()),
                    "Full frame index differs from old fixed archive")
            # B manifest binds the gzip; the pinned packing record binds decoded bytes.
            packing_data = blob(tree, PREFIX + "evidence/run01/packing.json")
            require(sha(packing_data) == manifest["evidence/run01/packing.json"], "Packing hash mismatch")
            packing = json.loads(packing_data)
            decoded = gzip.decompress(data)
            require(sha(decoded) == packing["original_sha256"] and
                    len(decoded) == packing["original_bytes"], "Full frame JSON differs from B packing record")
            del decoded
        records.append({"source": PREFIX + rel, "local": rel, "git_blob": tree[PREFIX + rel],
                        "sha256": digest, "bytes": len(data), "b_manifest_verified": rel in manifest})
    report = {
        "status": "INPUTS_VERIFIED_NOT_SIMULATED",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested_main_baseline": BASELINE, "actual_HEAD": git("rev-parse", "HEAD").decode().strip(),
        "historical_FFT29_files_unchanged_since_baseline": True,
        "source_commit": B_SHA, "old_manifest_entries_unchanged": len(old_manifest),
        "historical_covered_case_ids": old, "selected_cases": remaining, "unselected_cases": old,
        "historical_covered_cases": 60, "prepared_case_count": 136,
        "unique_new_transforms_planned": 816, "backpressure_repeats_planned": 1,
        "backpressure_repeat": {"case": remaining[0], "channel": 0},
        "jobs_planned": 817, "new_XSim_transforms_executed": 0,
        "new_XSim_case_coverage": [], "planned_union_count_not_new_result": 196,
        "files": records,
        "limits": ["Six-channel archives are offline research only",
                   "No new synthesis/place/route, board run, H3 or default change",
                   "Historical 60-case results are not new executions"],
    }
    return report, tree


def output_root(path):
    require(path.is_absolute(), "Use an absolute short output path")
    require(not path.exists(), "Output exists; preserve it and select another name")
    for node in (path, *path.parents):
        if node.exists():
            info = node.lstat()
            require(not stat.S_ISLNK(info.st_mode) and not getattr(info, "st_file_attributes", 0) & 0x400,
                    "Output reparse/junction path refused: " + str(node))
    require(path.parent.is_dir(), "Output parent does not exist")
    resolved = path.resolve()
    require(ROOT != resolved and ROOT not in resolved.parents and resolved not in ROOT.parents,
            "Vivado work output must be outside the repository")
    require(resolved.name.lower().startswith("fft29-coverage-"),
            "Use a clearly scoped new directory named fft29-coverage-*")
    require(len(str(resolved)) < 100, "Use a short path for Vivado on Windows")
    return resolved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--report", type=Path, help="New read-only-audit report path, never overwrite")
    parser.add_argument("--out", type=Path, help="New isolated output root; no simulation is launched")
    args = parser.parse_args()
    require(args.check_only != bool(args.out), "Choose --check-only or --out, not both")
    if args.report:
        require(not args.report.exists(), "Report already exists")
    out = output_root(args.out) if args.out else None
    report, tree = audit()
    if args.check_only:
        if args.report:
            save_json(args.report, report)
        print(json.dumps({k: v for k, v in report.items() if k not in
                          ("files", "historical_covered_case_ids", "selected_cases", "unselected_cases")}, indent=2))
        return
    out.mkdir(exist_ok=False)
    save_json(out / "input-index.json", report)
    save_json(out / "prepare-command.json", {"argv": [sys.executable, *sys.argv], "cwd": str(Path.cwd())})
    try:
        for entry in report["files"]:
            data = blob(tree, entry["source"])
            require(sha(data) == entry["sha256"], "Input changed during snapshot")
            save(out / "reference" / entry["local"], data)
        save_json(out / "reference/provenance.json", report)
        for p in sorted((EXT / "source").iterdir()):
            if p.is_file() and p.suffix in (".py", ".sv", ".tcl"):
                save(out / "source" / p.name, p.read_bytes())
        save(out / "source/prepare.py", (TASK / "source/prepare.py").read_bytes())
        save(out / "configuration.json", (TASK / "configuration.json").read_bytes())
        command = [sys.executable, "-B", str(out / "source/prepare.py"), "--reference",
                   str(out / "reference"), "--out", str(out / "vectors")]
        save_json(out / "packing-command.json", {"argv": command, "cwd": str(out)})
        with (out / "packing.log").open("xb") as stream:
            run = subprocess.run(command, cwd=out, stdout=stream, stderr=subprocess.STDOUT)
        require(run.returncode == 0, "Original packer failed; preserve packing.log and output directory")
        selection = json.loads((out / "vectors/selection.json").read_bytes())
        require(selection["selected_cases"] == report["selected_cases"] and len(selection["jobs"]) == 817,
                "Packed case list/job count mismatch")
        require(selection["jobs"][-1]["case"] == 1 and selection["jobs"][-1]["channel"] == 0,
                "Unexpected backpressure repeat")
        save_json(out / "prepared-sha256.json", {
            p.relative_to(out).as_posix(): {"sha256": sha(p.read_bytes()), "bytes": p.stat().st_size}
            for p in sorted(out.rglob("*")) if p.is_file()})
        save_json(out / "prepare-result.json", {"status": "READY_FOR_USER_XSIM_NOT_SIMULATED",
                  "cases": 136, "unique_transforms": 816, "backpressure_repeats": 1, "jobs": 817,
                  "simulation_executed": False, "output": str(out)})
        print("READY_FOR_USER_XSIM_NOT_SIMULATED: cases=136 unique_fft=816 repeat=1 jobs=817")
        print("Next: use the snapshotted source/create_sim.tcl in an empty Vivado 2025.2 session.")
    except Exception as error:
        save_json(out / "prepare-failure.json", {"status": "FAILED_NOT_SIMULATED", "error": str(error)})
        raise


if __name__ == "__main__":
    main()
