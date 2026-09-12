"""Read-only delivery audit; --record exclusively creates final audit artifacts.

No builds, board operations, git writes or cleanup. This is an author check,
not B's independent review. Local F-drive evidence must remain available.
"""
import argparse
import ast
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
REPO = BASE.parents[4]
sys.path.insert(0, str(BASE))
import build_current as bc
import ps_contract as pc

BASELINE = "050d06f5dc6fed4fa476e72fa416e9736bc7fef3"
BRANCH = "codex/toph/four-channel-engineering-review-20260912"
PREFIX = BASE.relative_to(REPO).as_posix() + "/"
CHANGED_OLD = {".gitattributes", ".gitignore", "README.md", "build_current.py"}
AUTHORED = ["build_current.py", "ps_contract.py", "test_ps_contract.py", "README.md",
            "repair_ps_contract/README.md", "repair_ps_contract/HANDOFF.md",
            "repair_ps_contract/check_repair.py",
            "repair_ps_contract/reproduce_legacy_false_positive.py",
            "repair_ps_contract/run_real_matrix.py"]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def need(ok, message):
    if not ok:
        raise RuntimeError(message)


def git(*args):
    return subprocess.check_output(
        ["git", "-c", "safe.directory=" + REPO.as_posix(),
         "-c", "core.longpaths=true", *args], cwd=REPO)


def verify_entries(root, entries):
    for rel, info in entries.items():
        path = root / rel
        need(path.is_file() and bc.sha(path) == info["sha256"].lower(),
             "File hash differs: " + str(path))
        if "bytes" in info:
            need(path.stat().st_size == info["bytes"], "File size differs: " + str(path))


def audit():
    report = {"kind": "AUTHOR_DELIVERY_AUDIT_NOT_INDEPENDENT_REVIEW",
              "baseline": BASELINE, "board_test": "NOT_RUN", "B_21_tests": "NOT_OBTAINED_NOT_RUN"}
    git("merge-base", "--is-ancestor", BASELINE, "HEAD")
    report["checked_HEAD"] = git("rev-parse", "HEAD").decode().strip()
    report["checked_branch"] = git("branch", "--show-current").decode().strip()
    report["author_task_branch"] = BRANCH
    changed = set(git("diff", "--name-only", BASELINE, "-z").decode().split("\0"))
    changed.update(git("ls-files", "--others", "--exclude-standard", "-z").decode().split("\0"))
    need(all(not p or p.startswith(PREFIX) for p in changed), "Changes outside current_build")
    ignored = git("ls-files", "--others", "--ignored", "--exclude-standard", "-z", "--", PREFIX)
    need(not ignored, "Ignored untracked delivery material requires explicit handling")
    for rel in ("test_build_current.py", "build_hw.tcl", "RESULTS.md", "ENVELOPE-SHA256.json"):
        need(git("show", BASELINE + ":" + PREFIX + rel) == (BASE / rel).read_bytes(),
             "Original frozen current-build file changed: " + rel)
    frozen = read(BASE.parent / "DELIVERY-MANIFEST-20260912.json")["files"]
    verify_entries(REPO, {i["path"]: i for i in frozen})
    old = read(BASE / "ENVELOPE-SHA256.json")["files"]
    verify_entries(BASE, {i["path"]: i for i in old if i["path"] not in CHANGED_OLD})
    report["frozen_files_verified"] = len(frozen)
    report["old_envelope_unchanged_entries"] = len(old) - len(CHANGED_OLD)
    report["old_envelope_explicit_active_replacements"] = sorted(CHANGED_OLD)
    old_runs = []
    for i in range(1, 5):
        archive = BASE / "evidence" / ("run%02d" % i)
        original = Path(read(archive / "preflight.json")["output"])
        for rel in ("result.json", "artifacts-sha256.json"):
            need(bc.sha(archive / rel) == bc.sha(original / rel), "Old run record changed")
        verify_entries(original, read(original / "artifacts-sha256.json"))
        old_runs.append({"path": str(original), "status": read(original / "result.json")["status"],
                         "artifacts_verified": True})
    report["historical_runs_not_reclassified"] = old_runs
    legal = HERE / "evidence/legal-ps-02"
    plan = read(legal / "preflight.json")
    original = Path(plan["output"])
    need(not bc.unchanged(plan), "Actual one/PS/BSP/protected input changed")
    verify_entries(original, read(original / "artifacts-sha256.json"))
    for rel in ("build_current.py", "ps_contract.py"):
        need(bc.sha(BASE / rel) == bc.sha(legal / rel) == bc.sha(original / rel),
             "Real legal run does not bind final active entry: " + rel)
    need(read(legal / "result.json")["status"] == "PS_CONTRACT_PASS_NOT_HW_BUILD", "Legal run failed")
    bound = read(legal / "ps_check/contract-result.json")
    verify_entries(original, {p: {"sha256": h} for p, h in bound["bindings_sha256"].items()})
    report["legal_compiler_bound_values"] = bound["values"]
    report["actual_protected_inputs_unchanged"] = True
    proof = HERE / "evidence/compiled-proof"
    for name in ("ps_build_unit.o", "four_mic_capture.elf", "four_mic_capture.map"):
        need(bc.sha(proof / "valid" / name) == bc.sha(original / "ps_check" / name),
             "Archived real compilation bytes differ: " + name)
    exe = pc.Elf32(proof / "valid/four_mic_capture.elf", 2)
    obj = pc.Elf32(proof / "valid/ps_build_unit.o", 1)
    need(exe.contract() == obj.contract() == bound["compiled_values"], "Archived compiled values differ")
    pc.validate_values(exe.contract(), bound["hardware"], exe.allocated + exe.loads, exe.symbol_value("end"))
    report["archived_real_ELF_redecoded"] = True
    legacy = HERE / "legacy-counterexample-01"
    need(read(legacy / "counterexample-summary.json")["false_positive_reproduced"], "Missing old false positive")
    after = HERE / "evidence/exact-legacy-after"
    after_plan = read(after / "preflight.json")
    bad = [p for p in legacy.rglob("main_four_capture.c")]
    same_hash = "5a21c65da0f29707fafe64e7d1fe4c7382ef6d23e09598464a52bd0b0d394c32"
    need(bad and all(bc.sha(p) == same_hash for p in bad), "Legacy source bytes changed")
    real_bad = Path(after_plan["output"]) / "inputs/ps/main_four_capture.c"
    need(bc.sha(real_bad) == same_hash, "Before/after source bytes differ")
    need(bc.sha(proof / "rejected/ps_build_unit.o") ==
         bc.sha(Path(after_plan["output"]) / "ps_check/ps_build_unit.o"), "Rejected object bytes differ")
    need(pc.Elf32(proof / "rejected/ps_build_unit.o", 1).contract()["BASE"] == 0x00100000,
         "Archived rejected object lacks changed BASE")
    need(read(after / "ps_check/compiled-contract.json")["compiled_values"]["BASE"] == 0x00100000,
         "Changed BASE was not compiled")
    need(read(after / "result.json")["error"] == "Unsupported changed fixed PS contract", "Counterexample not rejected")
    report["same_byte_counterexample_before_after_sha256"] = same_hash
    matrix = read(HERE / "evidence/matrix03/matrix-result.json")
    need(len(matrix["cases"]) == 14 and all(c["expectation_met"] for c in matrix["cases"]), "Real matrix failed")
    need(sum(c["expected_pass"] for c in matrix["cases"]) == 2, "Unexpected positive/negative coverage")
    edge = read(HERE / "evidence/matrix03/result-legal-program-end-at-base/ps_check/contract-result.json")
    need(edge["values"]["program_end"] == edge["values"]["rx_start"], "Missing real legal end=BASE case")
    report["real_matrix"] = {"cases": 14, "legal_pass": 2, "expected_rejections": 12}
    json_count = 0
    for p in HERE.rglob("*.json"):
        read(p)
        json_count += 1
    for rel in AUTHORED:
        p = BASE / rel
        if p.suffix == ".py":
            ast.parse(p.read_text(encoding="utf-8"), filename=str(p))
        check = subprocess.run(["git", "-c", "core.autocrlf=false", "diff", "--no-index", "--check", "--",
                                "NUL", str(p)], capture_output=True)
        need(check.returncode in (0, 1) and not check.stdout and not check.stderr,
             "New-file whitespace check: " + rel + " " + check.stdout.decode(errors="replace"))
    git("diff", "--check")
    report["json_parse_count"] = json_count
    report["syntax_and_whitespace"] = "PASS"
    command = [sys.executable, "-B", "-m", "unittest", "discover", "-s", ".", "-p", "test_*.py", "-v"]
    proc = subprocess.run(command, cwd=BASE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log = proc.stdout.decode("utf-8", errors="replace")
    need(proc.returncode == 0 and "Ran 63 tests" in log and log.rstrip().endswith("OK"), "34+29 unit tests failed: " + log)
    report["unit_tests"] = {"command": command, "cwd": str(BASE), "exit_code": proc.returncode,
                            "original_unchanged": 34, "new": 29, "total": 63}
    report["status"] = "AUTHOR_AUDIT_PASS_NOT_ACCEPTANCE"
    return report, log


def repair_files():
    files = [BASE / p for p in sorted(CHANGED_OLD | {"ps_contract.py", "test_ps_contract.py"})]
    files += sorted(p for p in HERE.rglob("*") if p.is_file() and p != HERE / "REPAIR-MANIFEST.json")
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", action="store_true", help="Create new final evidence, never overwrite")
    args = parser.parse_args()
    outputs = [HERE / "evidence/final-unit-tests.log", HERE / "evidence/verification.json", HERE / "REPAIR-MANIFEST.json"]
    if args.record:
        need(not any(p.exists() for p in outputs), "Final evidence already exists; no overwrite")
    report, log = audit()
    if args.record:
        with outputs[0].open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(log)
        bc.write_json(outputs[1], report)
        files = repair_files()
        entries = [{"path": p.relative_to(BASE).as_posix(), "bytes": p.stat().st_size, "sha256": bc.sha(p)} for p in files]
        bc.write_json(outputs[2], {"status": "AUTHOR_SELF_CHECK_PENDING_INDEPENDENT_REVIEW", "baseline": BASELINE,
                                 "path_root": "current_build", "excludes": ["repair_ps_contract/REPAIR-MANIFEST.json"],
                                 "files": entries})
    if outputs[2].exists():
        entries = {i["path"]: i for i in read(outputs[2])["files"]}
        need(set(entries) == {p.relative_to(BASE).as_posix() for p in repair_files()},
             "Manifest membership differs from current repair files")
        verify_entries(BASE, entries)
        report["repair_manifest"] = "ALL_LISTED_HASHES_MATCH"
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
