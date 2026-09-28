"""Reproduce the bounded independent portable-H3 verification packet.

The runner preserves every command/exit/log. A known boundary mismatch remains
a real nonzero DUT finding; it does not erase the passing positive evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import numpy as np


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--python", type=Path, required=True)
    ap.add_argument("--fixed-input-index", type=Path, required=True,
                    help="The frozen 21-object ASSEMBLY-PLAN INPUTS.json")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if a.out.exists():
        raise FileExistsError(a.out)
    a.out.mkdir(parents=True)
    here = Path(__file__).resolve().parent
    python = str(a.python.resolve(strict=True))
    repo = a.repo.resolve(strict=True)
    steps = []

    def run(name, argv, *, cli=False):
        process = subprocess.run(argv, cwd=repo / "models/python" if cli else here,
                                 capture_output=True)
        (a.out / (name + ".stdout.log")).write_bytes(process.stdout)
        (a.out / (name + ".stderr.log")).write_bytes(process.stderr)
        record = {"name": name, "argv": list(map(str, argv)), "cwd": str(repo / "models/python" if cli else here),
                  "exit_code": process.returncode,
                  "stdout_sha256": digest(a.out / (name + ".stdout.log")),
                  "stderr_sha256": digest(a.out / (name + ".stderr.log"))}
        steps.append(record)
        return process.returncode

    base = [python, "-B"]
    fixture = a.out / "fixture"
    reference = a.out / "reference"
    numeric = a.out / "numeric"
    causal = a.out / "causal"
    checked = a.out / "checked"
    negatives = a.out / "cli-negatives"
    boundary = a.out / "boundary"
    jobs = [
        ("fixture", base + [str(here / "make_fixture.py"), "--repo", str(repo), "--out", str(fixture)], False),
        ("reference", base + [str(here / "independent_reference.py"), "--repo", str(repo),
                              "--fixture", str(fixture), "--out", str(reference)], False),
        ("numeric", base + ["-m", "soundsight_h3_portable", "--repo", str(repo),
                            "--config", str(fixture / "config.json"), "--pcm", str(fixture / "pcm.npy"),
                            "--out", str(numeric)], True),
        ("causal", base + ["-m", "soundsight_h3_portable", "--repo", str(repo),
                           "--config", str(fixture / "config.json"), "--pcm", str(fixture / "pcm.npy"),
                           "--schedule", str(fixture / "schedule.json"), "--manual-angle-q8", "0",
                           "--out", str(causal)], True),
        ("checker", base + [str(here / "checker.py"), "--repo", str(repo),
                            "--fixture", str(fixture), "--reference", str(reference),
                            "--result", str(causal), "--manual-angle-q8", "0", "--self-test",
                            "--out", str(checked)], False),
        ("cli-negatives", base + [str(here / "cli_negative.py"), "--python", python,
                                  "--repo", str(repo), "--fixture", str(fixture),
                                  "--out", str(negatives)], False),
        ("boundary", base + [str(here / "boundary_probe.py"), "--repo", str(repo),
                              "--out", str(boundary)], False),
    ]
    for name, argv, cli in jobs:
        code = run(name, argv, cli=cli)
        if code != 0 and name != "boundary":
            break
    completed = [row["name"] for row in steps]
    unexpected = [row for row in steps if row["exit_code"] and row["name"] != "boundary"]
    bound = next((row for row in steps if row["name"] == "boundary"), None)
    product_paths = subprocess.run(["git", "-C", str(repo), "ls-files", "models/python/soundsight_h3_portable"],
                                   capture_output=True, text=True, check=True).stdout.splitlines()
    product_commit = "5efc4b67ad49de2c2bd99eb38ba8995b6f312289"
    product_files = {}
    for path in product_paths:
        worktree_bytes = (repo / path).read_bytes()
        git_bytes = subprocess.run(["git", "-C", str(repo), "show", product_commit + ":" + path],
                                   capture_output=True, check=True).stdout
        same = worktree_bytes == git_bytes
        crlf_only = not same and worktree_bytes.replace(b"\r\n", b"\n") == git_bytes
        if not (same or crlf_only):
            raise RuntimeError("PRODUCT_WORKTREE_GIT_BYTES_MISMATCH: " + path)
        product_files[path] = {
            "worktree_sha256": hashlib.sha256(worktree_bytes).hexdigest(),
            "git_blob_sha256": hashlib.sha256(git_bytes).hexdigest(),
            "same_raw_bytes": same, "crlf_checkout_only": crlf_only,
        }
    require_index = a.fixed_input_index.resolve(strict=True)
    if digest(require_index) != "7ffc495f26a778a312e93dd2199d65ee4d2c050d6dc609393f6c4af83d862db0":
        raise RuntimeError("FIXED_21_OBJECT_INDEX_MISMATCH")
    source_manifest = json.loads((repo / "models/python/soundsight_h3_portable/tables/source-manifest.json").read_text())
    source_files = {}
    for role, row in source_manifest["entries"].items():
        observed = digest(repo / row["path"])
        if observed != row["sha256"]:
            raise RuntimeError("SOURCE_BINDING_MISMATCH: " + role)
        source_files[role] = observed
    identity = {"product_commit": product_commit, "python": sys.version,
                "numpy": np.__version__, "product_files": product_files,
                "fixed_21_object_index_sha256": digest(require_index),
                "source_binding_sha256": source_files,
                "asset_sha256": {path.name: digest(path) for path in here.iterdir() if path.is_file()}}
    packet = {"status": "DUT_BOUNDARY_FAIL" if bound and bound["exit_code"] == 1 and not unexpected else
                ("PASS_SCOPED" if len(steps) == len(jobs) and not unexpected else "INCOMPLETE"),
              "steps": steps, "completed": completed, "identity": identity,
              "boundary_is_expected_to_flag_contract_discrepancy": True,
              "not_measured": ["real clock", "RTL", "AMD", "production", "recorded acoustics", "SNR"]}
    (a.out / "evidence-index.json").write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": packet["status"], "completed": completed,
                      "index_sha256": digest(a.out / "evidence-index.json")}))
    if unexpected or packet["status"] == "INCOMPLETE":
        return 1
    if packet["status"] == "DUT_BOUNDARY_FAIL":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
