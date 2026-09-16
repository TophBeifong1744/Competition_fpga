"""Audit archive/current-file binding. Never builds firmware or accesses hardware."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
E1 = HERE.parent
BUILD = E1 / "evidence/user-build-20260916-2052"
UART = "endurance_300s_10x10s_20260916_01.log"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def put(path, data):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def equal(actual, expected, label):
    if actual != expected:
        raise ValueError(f"binding mismatch: {label}")


def run(out, name, argv):
    put(out / (name + ".command.json"), {"argv": argv, "cwd": str(HERE)})
    result = subprocess.run(argv, cwd=HERE, capture_output=True, text=True, encoding="utf-8", errors="replace")
    with (out / (name + ".log")).open("x", encoding="utf-8") as stream:
        stream.write(result.stdout + result.stderr)
    if result.returncode:
        raise ValueError(f"{name} exit={result.returncode}; see preserved log")


def record(args):
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {"scope": "post-run file/hash binding plus UART audit; NOT new ARM compilation or new board execution",
              "recorded_at": datetime.now().astimezone().isoformat(),
              "app": str(args.app), "platform": str(args.platform), "status": "INCOMPLETE"}
    try:
        # Reuse the previous real-build evidence, do not relabel it as a new build.
        batch = read(BUILD / "BATCH-SHA256.json")["files"]
        for name, expected in batch.items():
            equal(digest(E1 / name), expected, name)
        report["prior_build_manifest_files_verified"] = len(batch)
        snapshot = read(BUILD / "snapshot-binding.json")
        for name, expected in snapshot.items():
            equal(digest(args.app / name), expected, "current app/" + name)
            equal(digest(BUILD / "app" / name), expected, "archived app/" + name)
        report["current_app_and_archive_files_verified"] = len(snapshot)
        report["build_binding"] = read(BUILD / "build-binding.json")
        policy_path = E1.parent / "timerfixed-entry-01/POLICY.json"
        policy = read(policy_path)
        bsp = args.platform / "export/continuous_platform/sw/standalone_ps7_cortexa9_0"
        for name, expected in policy["bsp_sha256"].items():
            equal(digest(bsp / name), expected, "BSP/" + name)
        report["bsp_files_verified"] = len(policy["bsp_sha256"])
        report["bsp_policy_sha256"] = digest(policy_path)
        hardware = {}
        for name, expected in policy["hardware_sha256"].items():
            archived = E1.parent / "board-run-20260915-02/runtime" / name
            if name.endswith(".xsa"):
                current = args.platform / "export/continuous_platform/hw" / name
            else:
                folder = "bitstream" if name.endswith(".bit") else "psinit"
                current = args.app / "_ide" / folder / name
            equal(digest(current), expected, str(current))
            equal(digest(archived), expected, str(archived))
            hardware[name] = {"sha256": expected, "current": str(current), "existing_archive": str(archived)}
        report["hardware"] = hardware
        equal(digest(args.log), digest(HERE / UART), "original and archived UART")
        equal(digest(HERE / UART), "6920a852e43f2f6e4f47c2f1a4aefb8c3058ff5d108fc8ec5b4ea80e9cd41fd5", "UART pin")
        run(out, "parser_tests", [sys.executable, "-B", str(HERE / "test_verify_log.py")])
        run(out, "uart_audit", [sys.executable, "-B", str(HERE / "verify_log.py"), str(HERE / UART), "--out", str(out / "log-check.json")])
        report["totals"] = read(out / "log-check.json")["totals"]
        report["status"] = "ARCHIVE_AND_UART_CHECK_PASS_NOT_ACCEPTANCE"
    except Exception as exc:
        report["status"] = "REJECTED"
        report["error"] = str(exc)
    put(out / "result.json", report)
    print(report["status"], out)
    return 1 if report["status"] == "REJECTED" else 0


def manifest(mode):
    path = HERE / "SHA256.json"
    if mode == "seal":
        files = {p.relative_to(E1).as_posix(): digest(p) for p in sorted(E1.rglob("*"))
                 if p.is_file() and p != path}
        put(path, {"scope": "E1 package at this archive point; manifest excluded; external dependencies separately pinned",
                   "files": files})
    expected = read(path)["files"]
    # New evidence can be added later; this checks every sealed byte, never overwrites.
    for name, sha in expected.items():
        equal(digest(E1 / name), sha, name)
    print("SEALED_HASH_CHECK_PASS files=" + str(len(expected)))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    rec = sub.add_parser("record")
    rec.add_argument("--app", type=Path, required=True)
    rec.add_argument("--platform", type=Path, required=True)
    rec.add_argument("--log", type=Path, required=True)
    rec.add_argument("--out", type=Path, required=True, help="must not exist")
    sub.add_parser("seal")
    sub.add_parser("verify")
    args = parser.parse_args()
    return record(args) if args.mode == "record" else manifest(args.mode)


if __name__ == "__main__":
    raise SystemExit(main())
