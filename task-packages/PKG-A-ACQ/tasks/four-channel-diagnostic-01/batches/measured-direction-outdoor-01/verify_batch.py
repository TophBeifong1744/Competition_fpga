"""Offline integrity and provisional marker checks for the Issue #15 outdoor batch.

Reads the original, unchanged S1 verifier and marker functions from their
historical files. It never accesses a board or changes capture files.
"""

import argparse
import ast
import hashlib
import json
import re
import wave
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / "document/project-identity.md").is_file())
BATCHES = HERE.parent
S1 = BATCHES / "background-target-stop-20260917/finish_scene.py"
MARKERS = BATCHES / "trusted-direction-input-20260918/scripts/process_capture.py"
PLAY = BATCHES / "trusted-direction-input-20260918/playback-v1"
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def original_functions(path, names, namespace):
    """Compile selected function bodies verbatim, avoiding stale import roots."""
    parsed = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    selected = [node for node in parsed.body if isinstance(node, ast.FunctionDef) and node.name in names]
    if {node.name for node in selected} != set(names):
        raise ValueError(f"Missing expected source functions in {path}")
    module = ast.Module(body=selected, type_ignores=[])
    exec(compile(module, str(path), "exec"), namespace)
    return namespace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-root", type=Path, default=HERE, help="outdoor or indoor sibling batch")
    parser.add_argument("--out", type=Path, required=True, help="new JSON result path")
    args = parser.parse_args()
    batch = args.batch_root.resolve()
    if batch.parent != BATCHES.resolve() or not (batch / "captures").is_dir():
        raise ValueError("Batch root must be a sibling capture package")
    if args.out.exists():
        raise FileExistsError(args.out)
    if args.out.parent.resolve() != (batch / "evidence").resolve():
        raise ValueError("Output must be a new file directly under the selected batch's evidence directory")

    s1 = original_functions(S1, ("need", "one", "verify"), {"np": np, "re": re})
    markers = original_functions(
        MARKERS,
        ("read_wav", "marker_peak", "align"),
        {"np": np, "json": json, "wave": wave, "PLAY": PLAY, "sha": sha},
    )
    rows = []
    captures = sorted(path for path in (batch / "captures").iterdir() if path.is_dir())
    if len(captures) != 8:
        raise ValueError(f"Expected exactly eight captures, found {len(captures)}")
    if sum(path.name.startswith("az") for path in captures) != 6 or sum(
        path.name.startswith("bg") for path in captures
    ) != 2:
        raise ValueError("Expected six targets and two backgrounds")
    for cap in captures:
        capture_id = cap.name
        raw_path, log_path = cap / "raw.bin", cap / "serial.log"
        row = {
            "capture_id": capture_id,
            "raw_sha256": sha(raw_path),
            "serial_sha256": sha(log_path),
            "h1_reader_result": f"evidence/h1-reader-current/{capture_id}.json",
        }
        try:
            raw = raw_path.read_bytes()
            log = log_path.read_text(encoding="utf-8-sig")
            checked = s1["verify"](raw, log)
            row["s1_integrity"] = "PASS"
            row["capture"] = checked
            if capture_id.startswith("az"):
                pcm = np.frombuffer(raw, "<u4").reshape(-1, 8)[:, 2:6].view("<i4")
                alignment = markers["align"](pcm)
                row["marker_alignment"] = alignment
                for lane in alignment["channels"]:
                    if lane.get("source_file_interval_mapped_samples"):
                        lane["estimated_source_end_margin_samples"] = (
                            len(pcm) - lane["source_file_interval_mapped_samples"][1]
                        )
            else:
                row["marker_alignment"] = "NOT_APPLICABLE_BACKGROUND"
        except Exception as exc:
            row["s1_integrity"] = "FAIL"
            row["error"] = str(exc)
        rows.append(row)

    target_channels = [
        channel
        for row in rows
        if isinstance(row.get("marker_alignment"), dict)
        for channel in row["marker_alignment"]["channels"]
    ]
    if any(row["s1_integrity"] != "PASS" for row in rows):
        status = "INTEGRITY_FAIL"
    elif any(channel["status"] != "CANDIDATE_ALIGNMENT_REVIEW_REQUIRED" for channel in target_channels):
        status = "INTEGRITY_PASS_MARKER_UNRESOLVED"
    elif any(channel.get("source_file_fits_capture") is not True for channel in target_channels):
        status = "INTEGRITY_PASS_SOURCE_COVERAGE_EXCEPTION"
    else:
        status = "INTEGRITY_PASS_SCENE_REVIEW_PENDING"

    result = {
        "claim": "Offline raw/UART integrity and provisional marker alignment only",
        "status": status,
        "source_function_sha256": {str(S1.relative_to(REPO)): sha(S1), str(MARKERS.relative_to(REPO)): sha(MARKERS)},
        "source_playback_sha256": sha(PLAY / "soundsight-target-v1.wav"),
        "method": "Selected original function bodies compiled verbatim; no stale docs/team-workflow.md import root executed",
        "limits": [
            "Marker alignment is a candidate, not exact acoustic start/end or direction truth.",
            "source_file_fits_capture is a two-marker affine estimate and needs waveform/listening review.",
            "Host bit/ELF checks, actual Run entry, phone playback identity and measured positions are separate evidence.",
            "No B independent approval, H3/M1, SNR, precision direction or realtime claim.",
        ],
        "captures": rows,
    }
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(result["status"], len(rows), args.out)
    return 0 if result["status"].startswith("INTEGRITY_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
