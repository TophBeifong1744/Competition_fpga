"""Verify immutable audit evidence; --create is for initial packaging only."""
import argparse
import hashlib
import json
from pathlib import Path

BUNDLE = Path(__file__).resolve().parents[1]
REPO = BUNDLE.parents[3]
MANIFEST = BUNDLE / "file-manifest.json"
REFERENCES = [
    "hardware/reference/xilinx/ds187-zynq-7000-dc-ac.pdf",
    "hardware/reference/infineon/im73d122v01-datasheet-v1.00.pdf",
    "hardware/reference/navigator-zynq/navigator-zynq-baseboard-schematic-v3.9.pdf",
    "hardware/reference/navigator-zynq/zynq7010-7020-coreboard-schematic-v2.5.pdf",
]
MONO = "task-packages/PKG-A-H2-MONO-DIAGNOSTIC/"
REFERENCES += [MONO + "originals/mono_acceptance_20260910/snapshot/" + name for name in
               ("single_mic_top.v", "single_mic_io.xdc", "system_single_mic.bit")]
REFERENCES += [MONO + "publication/mono_closeout_20260910/" + name for name in
               ("system_wrapper_timing_summary_routed.rpt", "system_wrapper_io_placed.rpt")]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", action="store_true")
    args = parser.parse_args()
    if args.create:
        if MANIFEST.exists():
            raise SystemExit("Refusing to replace an existing manifest")
        files = sorted(p for p in BUNDLE.rglob("*") if p.is_file() and "__pycache__" not in p.parts)
        files += [REPO / name for name in REFERENCES]
        rows = [{"path": p.relative_to(REPO).as_posix(), "bytes": p.stat().st_size,
                 "sha256": sha(p)} for p in files]
        MANIFEST.write_text(json.dumps({"schema": "ss-electrical-audit-manifest-1",
                                      "scope": "listed files only; not hardware approval",
                                      "files": rows}, indent=2) + "\n", encoding="utf-8")
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    failures = []
    for row in data["files"]:
        path = (REPO / row["path"]).resolve()
        if not path.is_relative_to(REPO) or not path.is_file():
            failures.append(row["path"] + ": missing/unsafe")
        elif path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
            failures.append(row["path"] + ": changed")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"PASS: {len(data['files'])} listed files; hardware remains NOT_CLOSED")


if __name__ == "__main__":
    main()
