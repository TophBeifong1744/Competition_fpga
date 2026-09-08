"""Check authored H1 fixtures only; not B's production reader or its tests."""
import csv
import json
from pathlib import Path


def require(condition, message):
    if not condition:
        raise ValueError(message)


def check():
    root = Path(__file__).resolve().parents[1] / "examples" / "h1"
    expected = {
        "code-pattern": [
            [9007199254740992, 0, 1, -1, 2, 0, ""],
            [9007199254740993, 8388607, -8388608, 123, -456, 0, ""],
            [9007199254740995, 10, 20, 30, 40, 1, "drop;overflow"],
            [9007199254740996, -10, -20, -30, -40, 0, ""],
            [9007199254740997, 0, 0, 0, 0, 1, "unknown"],
            [9007199254740998, 100, 200, 300, 400, 0, ""],
        ],
        "restart": [[0, 101, 201, 301, 401, 0, ""], [1, -101, -201, -301, -401, 0, ""]],
    }
    acquisitions = set()
    header = ["sample_id", "mic0", "mic1", "mic2", "mic3", "stream_error", "error_flags"]
    for name, wanted in expected.items():
        meta = json.loads((root / name / "metadata.json").read_text(encoding="utf-8-sig"))
        require(meta["schema_version"] == "ss-data-draft-0.3", "schema")
        require(meta["channel_order"] == header[1:5], "channel order")
        require(meta["sample_format"] == {
            "encoding": "signed-pcm", "storage_dtype": "int32", "valid_bits": 24,
            "alignment": "right", "fractional_bits": 0,
        }, "sample format")
        require(meta["source_kind"] == "synthetic-code" and meta["evidence_level"] == "synthetic", "evidence")
        require(meta["coordinates_m"] == [[-.02, -.02, 0], [.02, -.02, 0], [.02, .02, 0], [-.02, .02, 0]], "geometry")
        require(meta["sample_rate_hz"] == 48000, "nominal rate")
        require(meta["coordinate_system"] == "x-forward_y-left_z-up", "axes")
        require(meta["direction_convention"] == "array-to-source" and meta["angle_unit"] == "deg", "direction")
        require(meta["calibration_status"] == "not-calibrated", "calibration")
        require(set(meta["provisional_fields"]) == {"channel_order", "coordinates_m", "sample_rate_hz", "sample_format"}, "provisional")
        require(meta["acquisition_id"] not in acquisitions, "restart identity")
        acquisitions.add(meta["acquisition_id"])
        with (root / name / "samples.csv").open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.reader(stream))
        require(rows[0] == header, "header")
        actual = [[int(v) for v in row[:6]] + [row[6]] for row in rows[1:]]
        require(actual == wanted, f"exact values: {name}")
        for index, row in enumerate(actual):
            require(0 <= row[0] < 2**64, "uint64")
            require(all(-2**23 <= value < 2**23 for value in row[1:5]), "PCM range")
            require(bool(row[5]) == bool(row[6]), "error/flags agreement")
            if index:
                require(row[0] > actual[index-1][0], "monotonic")
                if row[0] > actual[index-1][0] + 1:
                    require(row[5] == 1 and "drop" in row[6].split(";"), "gap indication")
        print(f"PASS fixture {name}: {len(actual)} rows")
    plan = json.loads((root / "reader-test-plan.json").read_text(encoding="utf-8"))
    require(len(plan["cases"]) == 15, "test-plan count")
    require(all(case["reader_test_status"] == "NOT_RUN" for case in plan["cases"]), "not reader test evidence")
    print("PASS authored fixtures and 15 planned reader cases; B reader tests NOT_RUN; H1 confirmation pending")


if __name__ == "__main__":
    check()
