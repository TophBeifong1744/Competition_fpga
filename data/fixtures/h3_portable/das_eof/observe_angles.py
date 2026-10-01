"""Observation only: actual bound ROM plus portable audio manual entry."""
import argparse
import json
from pathlib import Path
import sys

import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        parser.error("OUTPUT_EXISTS")
    sys.path.insert(0, str(args.repo / "models/python"))
    from soundsight_h3_portable.bindings import Bindings
    from soundsight_h3_portable.audio import render_three_lanes
    bound = Bindings(args.repo)
    n = np.arange(64, dtype=np.int64)
    pcm = np.asarray([8 * n, 16 * n, 24 * n, 32 * n + 4096])
    rows = []
    for angle in (-180, -90, -45, 0, 45, 90):
        audio = render_three_lanes(pcm, angle * 256, [], bound)
        rows.append({"angle_deg": angle, "delays_q12": list(map(int, bound.delay_rom.lookup(angle * 256))),
                     "source_n": 20, "emit": 28, "beam": int(audio["manual"][20])})
    bound.verify_post()
    args.out.write_text(json.dumps({"entry": "soundsight_h3_portable.audio.render_three_lanes",
                                    "angle_samples": rows, "source_identity": bound.identity}, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
