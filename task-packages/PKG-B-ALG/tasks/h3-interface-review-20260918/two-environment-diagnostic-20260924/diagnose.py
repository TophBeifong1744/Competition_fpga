"""Two-environment development diagnostic. Real captures require a full S1 receipt."""

import argparse
import hashlib
import importlib.util
import json
import math
import pathlib
import platform
import re
import sys
import zipfile

import numpy as np


SCENES = {"bg_pre": ("01",), "bg_post": ("01",),
          "000": ("01", "02"), "m045": ("01", "02"), "p045": ("01", "02")}
ENVIRONMENTS = ("indoor", "outdoor")
HASH = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
DATE = "20260922"
STATUS = "CONDITIONAL_DEVELOPMENT_DIAGNOSTIC_NOT_ACCEPTANCE"
REFERENCE_COMMIT = "21e93570cb054f81c629675bd4f1b99a6249edc6"
PINNED_DEPENDENCIES = (
    "dd1f8a1375cd50187ba012235226c53548d75f95fbe6cf5e4483af9d47e9a163",
    "3360fdbfc07f073b9e3c45883811dfeee3177a4ec6a1d50ba4cae2468a138cb4",
    "7acd56bd7742baf174b0273f0aee2e54bacfe730840c7cb8019c07e3b2b675de",
    "2297aa7f94058e3e4faf3da792c6f1beef6c68fa72121100ec672d60ade5ec50",
    "eb5c19b1ff30ec5926170c2f1c216ac764f3aa855c0d165c9822c6d59e11a9a7",
)
PINNED_IMPORTS = {
    "tasks/phat-fixed-03/phat_model.py": "84eaa9691f62aba7164e3172aa94b2e361cb99672647477d98f8b3f3889f3144",
    "tasks/fft-window-02/window_model.py": "3fd314bcf6c866b2a2ed8185ea1be2dd1079d38e38dc11f5caa883b748889bce",
    "tasks/fft-bitexact-01/compare_cmodel.py": "d14e589b559a5afbf5e1e2d6e095d54896fef1f33ffd482c5a80ad293398b1d8",
    "payload/model/python/six_mic_baseline_core.py": "23184058f08fa54af4c61b9681f2fbe40341430f0ba48f8574676f27ce4964b0",
    "payload/model/python/h1_reader.py": "104d15e41cc186b8622df8b0ce52b0aae9b06085eab5e0b982a4b0053c9b2fa9",
}


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def read_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    need(spec is not None and spec.loader is not None, "DEPENDENCY_IMPORT_FAILED: " + str(path))
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def canonical(environment, scene, run):
    return "c_{}_{}_{}_{}".format(environment, scene, DATE, run)


def mapping_for_environment(mapping, environment, zip_path):
    """Validate the complete mapping before selecting either environment."""
    need(environment in ENVIRONMENTS, "UNKNOWN_ENVIRONMENT")
    files = mapping.get("files")
    need(isinstance(files, list) and len(files) == 32, "MAPPING_NEEDS_32_FILES")
    expected = {canonical(env, scene, run) for env in ENVIRONMENTS
                for scene, runs in SCENES.items() for run in runs}
    pairs = {}
    member_keys = set()
    target_keys = set()
    zip_identity = {}
    for entry in files:
        need(isinstance(entry, dict), "INVALID_MAPPING_ROW")
        env, scene, run, ext = (entry.get(key) for key in
                                ("environment", "scene", "run_tag", "extension"))
        need(env in ENVIRONMENTS and scene in SCENES and run in SCENES[scene]
             and ext in (".bin", ".log"), "INVALID_SCENE_OR_EXTENSION")
        stem = canonical(env, scene, run)
        need(entry.get("canonical_stem") == stem and entry.get("date") == DATE,
             "CANONICAL_IDENTITY_MISMATCH")
        standard = stem + ext
        need(entry.get("standard_name") == standard and
             entry.get("standard_relative_path") == "normalized/{}/{}".format(env, standard),
             "STANDARD_PATH_MISMATCH")
        source = entry.get("source_member_path")
        need(isinstance(source, str) and source.endswith(ext) and
             pathlib.PurePosixPath(source).name != "" and
             not pathlib.PurePosixPath(source).is_absolute() and
             ".." not in pathlib.PurePosixPath(source).parts and "\\" not in source,
             "UNSAFE_SOURCE_MEMBER")
        need(entry.get("source_name") == source and
             pathlib.PurePosixPath(source).stem == entry.get("source_stem"),
             "SOURCE_NAME_MISMATCH")
        member_sha = entry.get("source_member_sha256")
        zip_sha = entry.get("source_zip_sha256")
        need(isinstance(member_sha, str) and HASH.fullmatch(member_sha) and
             entry.get("target_sha256") == member_sha and
             entry.get("byte_identical") is True and
             isinstance(entry.get("source_bytes"), int) and entry["source_bytes"] > 0 and
             entry.get("target_bytes") == entry["source_bytes"],
             "MEMBER_IDENTITY_MISMATCH")
        need(isinstance(zip_sha, str) and HASH.fullmatch(zip_sha) and
             isinstance(entry.get("source_zip_path"), str), "ZIP_IDENTITY_MISSING")
        zip_id = (entry["source_zip_path"], zip_sha)
        need(env not in zip_identity or zip_identity[env] == zip_id,
             "MULTIPLE_ZIPS_FOR_ENVIRONMENT")
        zip_identity[env] = zip_id
        key = (env, stem, ext)
        need(key not in pairs and (env, source) not in member_keys and
             entry["standard_relative_path"] not in target_keys,
             "DUPLICATE_OR_AMBIGUOUS_MAPPING")
        pairs[key] = entry
        member_keys.add((env, source))
        target_keys.add(entry["standard_relative_path"])
    need(set(stem for _, stem, _ in pairs) == expected and len(pairs) == 32,
         "INCOMPLETE_SCENE_MAPPING")
    need(zip_identity["indoor"] != zip_identity["outdoor"], "ENVIRONMENTS_SHARE_ZIP")
    selected_path, selected_sha = zip_identity[environment]
    need(pathlib.Path(selected_path).resolve() == pathlib.Path(zip_path).resolve(),
         "ZIP_PATH_MISMATCH")
    runs = []
    for scene, run_tags in SCENES.items():
        for run in run_tags:
            stem = canonical(environment, scene, run)
            binary, log = (pairs[(environment, stem, ext)] for ext in (".bin", ".log"))
            need(binary["source_stem"] == log["source_stem"], "BIN_LOG_SOURCE_MISMATCH")
            runs.append(dict(stem=stem, scene=scene, run=run,
                             bin=binary, log=log, zip_sha256=selected_sha))
    return runs, selected_sha


def check_receipt(receipt, environment, mapping_sha, zip_sha, runs):
    """Require full S1 evidence identity; a Luna mechanical receipt cannot pass."""
    need(receipt.get("kind") == "FULL_S1_CAPTURE_VERIFICATION" and
         receipt.get("status") == "PASS_FULL_S1" and
         receipt.get("environment") == environment and
         receipt.get("mapping_sha256") == mapping_sha and
         receipt.get("source_zip_sha256") == zip_sha, "FULL_S1_RECEIPT_REQUIRED")
    for field in ("entry_commit", "entry_path", "entry_source_sha256",
                  "evidence_path", "evidence_sha256", "command"):
        need(bool(receipt.get(field)), "RECEIPT_FIELD_MISSING: " + field)
    need(COMMIT.fullmatch(receipt["entry_commit"]) and
         HASH.fullmatch(receipt["entry_source_sha256"]) and
         HASH.fullmatch(receipt["evidence_sha256"]) and
         isinstance(receipt["command"], list), "RECEIPT_ENTRY_IDENTITY_INVALID")
    rows = receipt.get("captures")
    need(isinstance(rows, list) and len(rows) == 8, "RECEIPT_RUN_COUNT_MISMATCH")
    by_stem = {}
    for row in rows:
        stem = row.get("canonical_stem")
        need(stem not in by_stem and row.get("status") == "PASS_FULL_S1",
             "RECEIPT_RUN_NOT_VERIFIED")
        by_stem[stem] = row
    need(set(by_stem) == {r["stem"] for r in runs}, "RECEIPT_RUN_SET_MISMATCH")
    for run in runs:
        row = by_stem[run["stem"]]
        need(row.get("raw_sha256") == run["bin"]["source_member_sha256"] and
             row.get("log_sha256") == run["log"]["source_member_sha256"],
             "RECEIPT_MEMBER_HASH_MISMATCH")


def read_pcm(zip_path, runs, expected_zip_sha):
    need(digest(zip_path) == expected_zip_sha, "ZIP_SHA256_MISMATCH")
    expected = {r[k]["source_member_path"] for r in runs for k in ("bin", "log")}
    data = {}
    with zipfile.ZipFile(zip_path) as archive:
        names = [i.filename for i in archive.infolist()]
        need(len(names) == len(set(names)), "DUPLICATE_ZIP_PATH")
        need(all(not pathlib.PurePosixPath(n).is_absolute() and
                 ".." not in pathlib.PurePosixPath(n).parts and "\\" not in n
                 for n in names), "UNSAFE_ZIP_PATH")
        need({n for n in names if n.endswith((".bin", ".log"))} == expected,
             "ZIP_MEMBER_SET_MISMATCH")
        for run in runs:
            for kind in ("bin", "log"):
                entry = run[kind]
                payload = archive.read(entry["source_member_path"])
                need(len(payload) == entry["source_bytes"] and
                     hashlib.sha256(payload).hexdigest() == entry["source_member_sha256"],
                     "ZIP_MEMBER_HASH_MISMATCH: " + run["stem"])
                if kind == "bin":
                    need(len(payload) % 32 == 0, "BIN_ROW_ALIGNMENT")
                    words = np.frombuffer(payload, "<u4").reshape(-1, 8)
                    data[run["stem"]] = words[:, 2:6].view("<i4").copy()
    need(digest(zip_path) == expected_zip_sha, "ZIP_CHANGED_DURING_RUN")
    return data


def bound_file(root, relative, expected_hash):
    need(isinstance(relative, str) and not pathlib.Path(relative).is_absolute(),
         "RECEIPT_PATH_INVALID")
    path = (root / relative).resolve()
    need(path.is_relative_to(root) and path.is_file() and digest(path) == expected_hash,
         "RECEIPT_FILE_IDENTITY_MISMATCH")
    return path


def analyze(runs, pcm, cfg, feature, locate, gate_factory, tracker_factory):
    """Process full runs; selection for formal scoring is deliberately absent."""
    need(cfg["frame_length"] == 1024 and cfg["hop"] == 512 and
         cfg["sample_rate_hz"] == 48000 and cfg["background_percentile"] == 95 and
         cfg["tracker_cone_half_angle_deg"] == 60 and
         cfg["band_bins_inclusive"] == [7, 72] and
         cfg["band_rms_floor_codes"] == 512 and
         cfg["on_power_ratio"] == 4 and cfg["off_power_ratio"] == 2 and
         cfg["attack_frames"] == 3 and cfg["release_frames"] == 3 and
         cfg["minimum_active_channels"] == 3, "REFERENCE_CONFIG_CHANGED")
    pre = [r for r in runs if r["scene"] == "bg_pre"]
    need(len(pre) == 1, "ONE_PRE_BACKGROUND_REQUIRED")
    pre_stem = pre[0]["stem"]
    pre_pcm = pcm[pre_stem]
    pre_powers = [feature(pre_pcm[start:start + 1024])["band_power"]
                  for start in range(0, len(pre_pcm) - 1023, 512)]
    need(bool(pre_powers), "NO_FULL_PRE_BACKGROUND_FRAME")
    noise = np.percentile(pre_powers, 95, axis=0)
    need(noise.shape == (4,) and np.isfinite(noise).all(), "INVALID_BACKGROUND_REFERENCE")
    frames, summaries = [], []
    for run in runs:
        stem = run["stem"]
        x = pcm[stem]
        gate = gate_factory(noise, cfg)
        trackers = {name: tracker_factory() for name in ("no_gate", "env_pre_background")}
        rows = []
        for start in range(0, len(x) - 1023, 512):
            f = feature(x[start:start + 1024])
            projection, pair_reasons, taus = locate(x[start:start + 1024])
            valid = bool(projection.get("advisory_consistent", False))
            angle = projection.get("advisory_azimuth_deg") if valid else None
            activity = {"no_gate": True,
                        "env_pre_background": bool(gate.update(f["band_power"], f["endpoint"]))}
            states = {}
            for name, tracker in trackers.items():
                if not activity[name]:
                    tracker.reset()
                direction = None if angle is None else [math.cos(math.radians(angle)),
                                                        math.sin(math.radians(angle)), 0]
                states[name] = tracker.update((start + 1024) / 48, direction,
                                              valid and activity[name])
            rows.append(dict(environment=run["bin"]["environment"], capture=stem,
                             start=start, stop=start + 1024,
                             timestamp_ms=(start + 1024) / 48,
                             valid=valid, angle=angle, projection=projection,
                             pair_reasons=pair_reasons, taus=taus,
                             activity=activity, trackers=states))
        modes = {name: dict(gate_frames=sum(r["activity"][name] for r in rows),
                            numeric_valid=sum(r["activity"][name] and r["valid"] for r in rows),
                            fresh=sum(bool(r["trackers"][name]["fresh_valid"]) for r in rows),
                            hold=sum(r["trackers"][name]["state"] == "HOLD" for r in rows),
                            rejected=sum(not r["trackers"][name]["fresh_valid"] for r in rows))
                 for name in trackers}
        summaries.append(dict(environment=run["bin"]["environment"], capture=stem,
                              scene=run["scene"], frames=len(rows), modes=modes))
        frames.extend(rows)
    return noise.tolist(), frames, summaries


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repo", "zip", "mapping", "environment", "receipt", "out"):
        parser.add_argument("--" + name, required=True)
    args = parser.parse_args(argv)
    root = pathlib.Path(args.repo).resolve()
    output = pathlib.Path(args.out).resolve()
    need(not output.exists(), "OUTPUT_ALREADY_EXISTS")
    mapping_path = pathlib.Path(args.mapping).resolve()
    receipt_path = pathlib.Path(args.receipt).resolve()
    zip_path = pathlib.Path(args.zip).resolve()
    mapping = read_json(mapping_path)
    runs, zip_sha = mapping_for_environment(mapping, args.environment, zip_path)
    mapping_sha = digest(mapping_path)
    receipt_sha = digest(receipt_path)
    receipt = read_json(receipt_path)
    check_receipt(receipt, args.environment, mapping_sha, zip_sha, runs)
    entry_path = bound_file(root, receipt["entry_path"], receipt["entry_source_sha256"])
    evidence_path = bound_file(root, receipt["evidence_path"], receipt["evidence_sha256"])
    pcm = read_pcm(zip_path, runs, zip_sha)
    package = root / "task-packages/PKG-B-ALG"
    checkpoint = package / "tasks/h3-interface-review-20260918/checkpoint-20260923"
    dependencies = [checkpoint / "config.json", checkpoint / "source/candidates.py",
                    package / "tasks/c-board-algorithm-01/run.py",
                    package / "payload/model/python/sector_tracker.py",
                    package / "tasks/phat-fixed-03/integration/chain.py"]
    hashes = {p.relative_to(root).as_posix(): digest(p) for p in dependencies}
    need(tuple(hashes.values()) == PINNED_DEPENDENCIES, "REFERENCE_DEPENDENCY_CHANGED")
    cfg = read_json(dependencies[0])
    act = module("two_env_activity", dependencies[1])
    diag = module("two_env_doa", dependencies[2])
    trk = module("two_env_tracker", dependencies[3])
    for loaded in tuple(sys.modules.values()):
        source = getattr(loaded, "__file__", None)
        if source and pathlib.Path(source).suffix == ".py":
            path = pathlib.Path(source).resolve()
            if path.is_relative_to(root) and path.is_file():
                hashes[path.relative_to(root).as_posix()] = digest(path)
    need(all(hashes.get("task-packages/PKG-B-ALG/" + path) == expected
             for path, expected in PINNED_IMPORTS.items()), "REFERENCE_IMPORT_CHANGED")
    positions = np.array([[0, 0, 0], [.04, 0, 0], [.04, .04, 0], [0, .04, 0]])
    bounds = [np.linalg.norm(positions[j] - positions[i]) * 48000 / 343
              for i, j in diag.PAIRS]

    def locate(frame):
        pairs, _ = diag.floating(frame, bounds)
        return (diag.projection(pairs, positions, 48000, 343),
                [p["reason"] for p in pairs], [p.get("tau_samples") for p in pairs])

    noise, frames, summaries = analyze(
        runs, pcm, cfg, act.features, locate, act.BandActivity,
        lambda: trk.Tracker(trk.Config(cone_half_angle_deg=60)))
    need(all(digest(root / p) == h for p, h in hashes.items()) and
         digest(mapping_path) == mapping_sha and
         digest(receipt_path) == receipt_sha, "INPUT_CHANGED_DURING_RUN")
    output.mkdir(parents=True, exist_ok=False)
    result = dict(status=STATUS, evidence_profile="DIAGNOSTIC_SMOKE",
                  claim_stage="SIM_SMOKE", environment=args.environment,
                  mapping_sha256=mapping_sha, receipt_sha256=receipt_sha,
                  source_zip_sha256=zip_sha,
                  full_s1_entry=str(entry_path), full_s1_evidence=str(evidence_path),
                  source_members={r["stem"]: {k: dict(path=r[k]["source_member_path"],
                                                    sha256=r[k]["source_member_sha256"])
                                              for k in ("bin", "log")} for r in runs},
                  reference_source=pre_stem_from_runs(runs),
                  pre_background_power=noise, captures=summaries,
                  frames=len(frames), dependency_sha256=hashes,
                  reference_commit=REFERENCE_COMMIT,
                  source_sha256=digest(pathlib.Path(__file__)),
                  command=[sys.executable, str(pathlib.Path(__file__).resolve())] +
                          (list(argv) if argv is not None else sys.argv[1:]),
                  cwd=str(pathlib.Path.cwd()),
                  tools=dict(python=platform.python_version(), numpy=np.__version__),
                  assumptions=dict(geometry="candidate 40 mm coplanar square; not measured for these recordings",
                                   positions_m=positions.tolist(), pair_bounds_samples=bounds,
                                   sample_rate_hz=48000, sound_speed_m_s=343,
                                   playback_identity="USER_REPORTED_NOT_BYTE_VERIFIED"),
                  limits="Full S1 receipt identity is required; this output is not formal direction or SNR scoring")
    for name, value in (("result.json", result), ("frames.json", frames)):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                            allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(dict(status=STATUS, environment=args.environment,
                          captures=len(summaries), frames=len(frames), out=str(output))))


def pre_stem_from_runs(runs):
    return next(r["stem"] for r in runs if r["scene"] == "bg_pre")


if __name__ == "__main__":
    main()
