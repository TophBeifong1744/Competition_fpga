"""Original-sample window grid and labels fixed independently of algorithm output."""

from __future__ import annotations

from .bundle import BundleError, require, uint


CLASSES = ("INPUT_INVALID", "ACTIVITY_OR_GEOMETRY_UNKNOWN", "EXCLUDED_UNCERTAIN",
           "CONFIRMED_NON_TARGET", "TARGET_N")
TRUTH_LABELS = {"TARGET", "BACKGROUND_PRE", "BACKGROUND_POST", "NON_TARGET",
                "CHALLENGE", "UNKNOWN", "EXCLUDED"}


def _ranges(value: list, label: str, first: int, stop: int) -> list[tuple[int, int]]:
    out = []
    for i, row in enumerate(value):
        require(isinstance(row, list) and len(row) == 2, f"RANGE_SHAPE:{label}:{i}")
        a = uint(row[0], f"{label}.{i}.start")
        b = uint(row[1], f"{label}.{i}.stop")
        require(first <= a < b <= stop, f"RANGE_BOUNDS:{label}:{i}")
        out.append((a, b))
    return out


def _intersects(start: int, stop: int, intervals: list[tuple[int, int]]) -> bool:
    return any(start < b and a < stop for a, b in intervals)


def planned_windows(run: dict) -> dict:
    """Build all full [start,start+1024) windows; never compact missing samples."""
    c, grid, truth = run["capture"], run["window_grid"], run["truth"]
    first, stop, origin = c["first_original_id"], c["stop_original_id"], grid["origin_original_id"]
    if any(type(v) is not int for v in (first, stop, origin)):
        return {"M": None, "tail_samples": None, "windows": [],
                "reason": "ORIGINAL_ID_RANGE_OR_GRID_MISSING"}
    require(origin <= first, f"GRID_ORIGIN_AFTER_RUN_START:{run['run_id']}")
    drop = _ranges(c["drop_ranges"], "drop", first, stop)
    clip = _ranges(c["clip_ranges"], "clip", first, stop)
    truth_map = {}
    truth_rows = truth["windows"] if isinstance(truth["windows"], list) else []
    for row in truth_rows:
        require(isinstance(row, dict), "TRUTH_WINDOW_NOT_OBJECT")
        start = uint(row.get("start_original_id"), "truth.window.start")
        require(start not in truth_map, f"TRUTH_DUPLICATE_WINDOW:{start}")
        require(isinstance(row.get("label"), str) and row["label"] in TRUTH_LABELS,
                f"TRUTH_LABEL_INVALID:{start}")
        require(isinstance(row.get("flags"), list), f"TRUTH_FLAGS_REQUIRED:{start}")
        require(all(isinstance(flag, str) and flag for flag in row["flags"]),
                f"TRUTH_FLAG_NAME_INVALID:{start}")
        truth_map[start] = row
    first_start = origin + ((max(0, first - origin) + 511) // 512) * 512
    windows = []
    for i, start in enumerate(range(first_start, stop - 1024 + 1, 512)):
        end = start + 1024
        label = truth_map.get(start)
        flags = list(label.get("flags", [])) if label else []
        has_drop, has_clip = _intersects(start, end, drop), _intersects(start, end, clip)
        if has_drop:
            flags.append("drop")
        if has_clip:
            flags.append("clip")
        if has_drop:
            primary = "INPUT_INVALID"
        elif label is None or label["label"] == "UNKNOWN" or (
                label["label"] == "TARGET" and
                (label.get("truth_angle_deg") is None or label.get("delta_theta_deg") is None)):
            primary = "ACTIVITY_OR_GEOMETRY_UNKNOWN"
        elif label["label"] == "EXCLUDED" or any(
                f in flags for f in ("marker", "guard", "tail_uncertain", "geometry_uncertain")):
            primary = "EXCLUDED_UNCERTAIN"
        elif label["label"] == "TARGET":
            primary = "TARGET_N"
        else:
            primary = "CONFIRMED_NON_TARGET"
        windows.append({"frame_index": i, "start_original_id": start,
                        "last_original_id": end - 1, "stop_original_id": end,
                        "primary_class": primary, "truth_label": label["label"] if label else "UNKNOWN",
                        "truth_angle_deg": label.get("truth_angle_deg") if label else None,
                        "delta_theta_deg": label.get("delta_theta_deg") if label else None,
                        "flags": sorted(set(flags))})
    unexpected_truth = set(truth_map) - {w["start_original_id"] for w in windows}
    require(not unexpected_truth, f"TRUTH_OUTSIDE_PLANNED_GRID:{sorted(unexpected_truth)[:3]}")
    outside = max(0, stop - (windows[-1]["stop_original_id"] if windows else first_start))
    counts = {name: sum(w["primary_class"] == name for w in windows) for name in CLASSES}
    require(sum(counts.values()) == len(windows), "M_CLASS_CONSERVATION")
    bpre = sum(w["primary_class"] == "CONFIRMED_NON_TARGET" and
               w["truth_label"] == "BACKGROUND_PRE" for w in windows)
    bpost = sum(w["primary_class"] == "CONFIRMED_NON_TARGET" and
                w["truth_label"] == "BACKGROUND_POST" for w in windows)
    return {"M": len(windows), "tail_samples": outside, "windows": windows,
            "classes": counts, "provisional_N": counts["TARGET_N"],
            "provisional_B_pre": bpre, "provisional_B_post": bpost,
            "clip_present": bool(clip), "drop_present": bool(drop), "reason": None}
