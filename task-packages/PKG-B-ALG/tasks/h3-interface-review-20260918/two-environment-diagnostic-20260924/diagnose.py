"""Two-environment diagnostic requiring pinned native partial S1 raw-UART evidence.

PASS_RAW_UART_ONLY does not establish scene provenance or acoustic performance.
"""

import argparse
import hashlib
import importlib.util
import json
import math
import pathlib
import platform
import re
import subprocess
import sys
import zipfile

import numpy as np


SCENES = {"bg_pre": ("01",), "bg_post": ("01",),
          "000": ("01", "02"), "m045": ("01", "02"), "p045": ("01", "02")}
ENVIRONMENTS = ("indoor", "outdoor")
HASH = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-fA-F]{40}\Z")
DATE = "20260922"
ADAPTER_RELATIVE = ("task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/"
                    "two-environment-diagnostic-20260924/")
EXECUTION_FILES = ("diagnose.py", "accepted-inputs.json")
STATUS = "CONDITIONAL_DEVELOPMENT_DIAGNOSTIC_NOT_ACCEPTANCE"
PREFLIGHT_STATUS = "METADATA_PREFLIGHT_ONLY"
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


def git_bytes(repo, *arguments):
    completed = subprocess.run(["git", *arguments], cwd=repo, capture_output=True)
    need(completed.returncode == 0, "GIT_IDENTITY_COMMAND_FAILED: " +
         " ".join(arguments) + " (exit {})".format(completed.returncode))
    return completed.stdout


def execution_identity(repo, expected_commit, executing_script):
    """Bind this process and its input manifest to exact committed raw bytes."""
    need(isinstance(expected_commit, str) and COMMIT.fullmatch(expected_commit),
         "EXPECTED_COMMIT_MUST_BE_FULL_SHA")
    expected_commit = expected_commit.lower()
    repo = pathlib.Path(repo).resolve()
    script = pathlib.Path(executing_script).resolve()
    need(script == (repo / ADAPTER_RELATIVE / "diagnose.py").resolve(),
         "EXECUTING_SCRIPT_OUTSIDE_AUTHORITY")
    top = pathlib.Path(git_bytes(repo, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    need(top == repo, "REPO_IS_NOT_GIT_TOPLEVEL")
    need(git_bytes(repo, "cat-file", "-t", expected_commit).strip() == b"commit",
         "EXPECTED_OBJECT_NOT_COMMIT")
    head = git_bytes(repo, "rev-parse", "--verify", "HEAD^{commit}").decode().strip()
    need(head == expected_commit, "EXECUTION_HEAD_MISMATCH: observed " + head)
    files = {}
    for name in EXECUTION_FILES:
        relative = ADAPTER_RELATIVE + name
        entry = git_bytes(repo, "ls-tree", "--full-tree", expected_commit, "--", relative)
        prefix, separator, listed_path = entry.partition(b"\t")
        fields = prefix.split()
        need(separator == b"\t" and listed_path.rstrip(b"\n").decode() == relative and
             len(fields) == 3 and fields[1] == b"blob", "EXECUTION_BLOB_MISSING: " + name)
        blob = git_bytes(repo, "cat-file", "blob", fields[2].decode())
        path = script if name == "diagnose.py" else repo / relative
        committed_hash = hashlib.sha256(blob).hexdigest()
        actual_hash = digest(path)
        need(actual_hash == committed_hash, "EXECUTION_FILE_DRIFT: " + name)
        files[name] = dict(git_blob_oid=fields[2].decode(),
                           git_blob_sha256=committed_hash, actual_sha256=actual_hash)
    return dict(expected_commit=expected_commit, observed_head=head, files=files)


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    need(spec is not None and spec.loader is not None, "DEPENDENCY_IMPORT_FAILED: " + str(path))
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


def canonical(environment, scene, run):
    return "c_{}_{}_{}_{}".format(environment, scene, DATE, run)


def mapping_for_environment(mapping, environment, zip_path=None):
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
    if zip_path is not None:
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


def inside(root, path, label):
    """Resolve paths without following a link out of its separately owned root."""
    root = pathlib.Path(root).resolve()
    result = pathlib.Path(path).resolve()
    need(result == root or result.is_relative_to(root), label + "_OUTSIDE_ROOT")
    return result


def child(root, relative, label):
    need(isinstance(relative, str) and not pathlib.Path(relative).is_absolute(),
         label + "_NOT_RELATIVE")
    return inside(root, pathlib.Path(root) / relative, label)


def locked_file(root, relative, expected, label, observed):
    path = child(root, relative, label)
    need(path.is_file() and digest(path) == expected, label + "_HASH_MISMATCH")
    observed[str(path)] = expected
    return path


def equal_path(left, right, label):
    need(pathlib.Path(left).resolve() == pathlib.Path(right).resolve(), label + "_PATH_MISMATCH")


def check_native_semantics(result, command, runs, environment, snapshot, evidence,
                           repo, accepted, manifest):
    """Check the existing partial raw-UART result and its finished CLI record."""
    zip_id = accepted["zip"][environment]
    by_source = {r["bin"]["source_stem"]: r for r in runs}
    need(len(by_source) == 8, "NATIVE_SOURCE_NAMES_AMBIGUOUS")
    need(result.get("status") == "PARTIAL_RECEIPT_PENDING_POSITION_AND_PROVENANCE" and
         result.get("passed") == 8 and result.get("all_raw_unique") is True and
         result.get("zip_sha256") == zip_id["sha256"] and
         result.get("zip_bytes") == zip_id["bytes"], "NATIVE_TOP_STATUS_OR_ZIP_MISMATCH")
    source_rel = "task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/c-recording-receipt-20260922/verify_zip.py"
    dep_rel = (
        "task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/background-target-stop-20260917/finish_scene.py",
        "task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/source/export_four.py",
    )
    manifest_files = manifest["files"]
    need(result.get("source_sha256") == accepted["verify_zip_sha256"] ==
         manifest_files[source_rel]["sha256"] and
         result.get("dependencies") == {p: manifest_files[p]["sha256"] for p in dep_rel} and
         manifest_files[dep_rel[0]]["sha256"] == accepted["finish_scene_sha256"],
         "NATIVE_SOURCE_OR_DEPENDENCY_MISMATCH")
    missing, not_tested = result.get("missing"), result.get("not_tested")
    need(isinstance(missing, list) and len(missing) == 6 and all(isinstance(x, str) for x in missing)
         and isinstance(not_tested, list) and len(not_tested) == 5 and
         all(isinstance(x, str) for x in not_tested), "NATIVE_LIMITS_MISSING")
    expected_members = {r[k]["source_member_path"]: r[k] for r in runs for k in ("bin", "log")}
    need(result.get("input_sha256") == {p: row["source_member_sha256"]
                                            for p, row in expected_members.items()},
         "NATIVE_INPUT_HASH_MISMATCH")
    inventory = result.get("inventory")
    need(isinstance(inventory, list) and len(inventory) == 16 and
         {i.get("path") for i in inventory} == set(expected_members),
         "NATIVE_INVENTORY_MISMATCH")
    for item in inventory:
        need(item.get("bytes") == expected_members[item["path"]]["source_bytes"] and
             isinstance(item.get("crc32"), str) and
             re.fullmatch(r"[0-9A-F]{8}", item["crc32"]), "NATIVE_INVENTORY_SIZE_OR_CRC")
    captures = result.get("captures")
    need(isinstance(captures, list) and len(captures) == 8, "NATIVE_CAPTURE_COUNT_MISMATCH")
    seen = set()
    for row in captures:
        name = row.get("name")
        need(name in by_source and name not in seen, "NATIVE_CAPTURE_NAME_MISMATCH")
        seen.add(name)
        mapped = by_source[name]
        checked = row.get("checked")
        need(row.get("status") == "PASS_RAW_UART_ONLY" and not row.get("error") and
             isinstance(checked, dict) and checked.get("groups") == 288250 and
             checked.get("flagged_rows") == 0 and
             checked.get("bytes") == mapped["bin"]["source_bytes"] and
             row.get("raw_sha256") == mapped["bin"]["source_member_sha256"] and
             row.get("log_sha256") == mapped["log"]["source_member_sha256"],
             "NATIVE_CAPTURE_STATUS_OR_IDENTITY_MISMATCH")
    argv = command.get("argv")
    need(command.get("environment") == environment and command.get("returncode") == 0 and
         command.get("spawn_error") is None and isinstance(argv, list) and len(argv) == 9 and
         argv[1:2] == ["-B"] and argv[3::2] == ["--repo", "--zip", "--out"] and
         command.get("python_executable") == argv[0] and
         command.get("python_version") == result.get("python") and
         command.get("numpy_version") == result.get("numpy"), "NATIVE_COMMAND_NOT_COMPLETED")
    source_path = child(snapshot, "snapshot/" + source_rel, "NATIVE_SCRIPT")
    equal_path(argv[2], source_path, "NATIVE_SCRIPT")
    snap_tree = child(snapshot, "snapshot", "S1_SNAPSHOT")
    equal_path(argv[4], snap_tree, "NATIVE_REPO")
    equal_path(command.get("cwd"), snap_tree, "NATIVE_CWD")
    copy_path = child(repo, zip_id["receipt_copy_relative_path"], "NATIVE_ZIP_COPY")
    equal_path(argv[6], copy_path, "NATIVE_ZIP_COPY")
    need(result.get("zip_name") == copy_path.name, "NATIVE_ZIP_NAME_MISMATCH")
    run_root = child(evidence, environment + "-run", "NATIVE_RUN")
    output = child(run_root, "verifier-output", "NATIVE_OUTPUT")
    equal_path(argv[8], output, "NATIVE_OUTPUT")
    equal_path(command.get("result_path"), child(output, "result.json", "NATIVE_RESULT"),
               "NATIVE_RESULT")
    for stream in ("stdout", "stderr"):
        log_path = child(run_root, stream + ".log", "NATIVE_LOG")
        equal_path(command.get(stream + "_path"), log_path, "NATIVE_LOG")
        need(log_path.is_file(), "NATIVE_LOG_MISSING")
    need(command.get("started_utc") and command.get("finished_utc") and
         isinstance(command.get("elapsed_seconds"), (int, float)) and
         command["elapsed_seconds"] >= 0, "NATIVE_COMMAND_TIME_MISSING")
    return dict(environment=environment, top_status=result["status"], passed=result["passed"],
                capture_statuses={r["name"]: r["status"] for r in captures},
                missing=missing, not_tested=not_tested, native_command=command,
                native_result_sha256=accepted["native_result_sha256"][environment],
                native_command_sha256=accepted["native_command_sha256"][environment],
                source_sha256=result["source_sha256"], dependencies=result["dependencies"],
                zip_sha256=result["zip_sha256"], zip_bytes=result["zip_bytes"])


def algorithm_hashes(root, observed):
    package = root / "task-packages/PKG-B-ALG"
    checkpoint = package / "tasks/h3-interface-review-20260918/checkpoint-20260923"
    direct = [checkpoint / "config.json", checkpoint / "source/candidates.py",
              package / "tasks/c-board-algorithm-01/run.py",
              package / "payload/model/python/sector_tracker.py",
              package / "tasks/phat-fixed-03/integration/chain.py"]
    for path, expected in zip(direct, PINNED_DEPENDENCIES):
        relative = path.relative_to(root).as_posix()
        locked_file(root, relative, expected, "ALGORITHM_DEPENDENCY", observed)
    for relative, expected in PINNED_IMPORTS.items():
        locked_file(root, "task-packages/PKG-B-ALG/" + relative,
                    expected, "ALGORITHM_IMPORT", observed)
    return direct


def load_context(repo, snapshot, evidence, mapping_path):
    """Metadata-only check of all three read-only roots and both environments."""
    accepted_path = pathlib.Path(__file__).resolve().parent / "accepted-inputs.json"
    accepted = read_json(accepted_path)
    repo, snapshot, evidence = (pathlib.Path(x).resolve() for x in (repo, snapshot, evidence))
    for actual, expected, label in ((repo, accepted["algorithm_root"], "ALGORITHM_ROOT"),
                                    (snapshot, accepted["snapshot_root"], "SNAPSHOT_ROOT"),
                                    (evidence, accepted["s1_evidence_root"], "S1_EVIDENCE_ROOT")):
        equal_path(actual, expected, label)
    observed = {str(accepted_path): digest(accepted_path),
                str(pathlib.Path(__file__).resolve()): digest(pathlib.Path(__file__))}
    mapping = locked_file(repo, accepted["mapping_relative_path"],
                          accepted["mapping_sha256"], "MAPPING", observed)
    equal_path(mapping_path, mapping, "MAPPING")
    mapping_data = read_json(mapping)
    manifest_path = locked_file(snapshot, "snapshot-manifest.json",
                                accepted["snapshot_manifest_sha256"], "SNAPSHOT_MANIFEST", observed)
    manifest = read_json(manifest_path)
    need(manifest.get("candidate") == accepted["snapshot_candidate"] and
         manifest.get("main") == "28d58e908525d1de1c018eeb99fd607a07b6047c" and
         manifest.get("parent") == REFERENCE_COMMIT, "SNAPSHOT_COMMIT_MISMATCH")
    for relative, identity in manifest["files"].items():
        if relative.endswith(".zip"):
            continue  # Old recording is outside this metadata-only check.
        path = locked_file(snapshot, "snapshot/" + relative, identity["sha256"],
                           "SNAPSHOT_FILE", observed)
        need(path.stat().st_size == identity["bytes"], "SNAPSHOT_SIZE_MISMATCH")
    need(manifest["files"]["task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/"
                           "c-recording-receipt-20260922/verify_zip.py"]["sha256"] ==
         accepted["verify_zip_sha256"], "SNAPSHOT_VERIFIER_MISMATCH")
    native_indexes = {}
    for name, expected in accepted["native_index_sha256"].items():
        path = locked_file(evidence, name, expected, "NATIVE_INDEX", observed)
        native_indexes[name] = read_json(path)
    machine = native_indexes["machine-summary.json"]
    identity = native_indexes["identity.json"]
    comparison = native_indexes["mapping-comparison.json"]
    need(machine.get("candidate") == accepted["snapshot_candidate"] and
         machine.get("snapshot_manifest_sha256") == accepted["snapshot_manifest_sha256"] and
         machine.get("verify_zip_sha256") == accepted["verify_zip_sha256"] and
         machine.get("raw_uart_summary_status") == "PASS_RAW_UART_ONLY" and
         identity.get("pre_post_identity_errors") == [] and
         comparison.get("prior_mapping_sha256") == accepted["mapping_sha256"],
         "NATIVE_INDEX_IDENTITY_MISMATCH")
    direct = algorithm_hashes(repo, observed)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    ancestor = subprocess.run(["git", "merge-base", "--is-ancestor",
                               accepted["algorithm_parent_commit"], "HEAD"], cwd=repo,
                              capture_output=True, text=True)
    need(ancestor.returncode == 0, "ALGORITHM_PARENT_NOT_ANCESTOR")
    native, runs_by_environment = {}, {}
    for environment in ENVIRONMENTS:
        runs, zip_sha = mapping_for_environment(mapping_data, environment)
        zip_id = accepted["zip"][environment]
        need(zip_sha == zip_id["sha256"], "MAPPING_ZIP_HASH_MISMATCH")
        equal_path(runs[0]["bin"]["source_zip_path"], zip_id["original_path"],
                   "MAPPING_ORIGINAL_ZIP")
        result_rel = environment + "-run/verifier-output/result.json"
        command_rel = environment + "-run/command.json"
        result_path = locked_file(evidence, result_rel,
                                  accepted["native_result_sha256"][environment],
                                  "NATIVE_RESULT", observed)
        command_path = locked_file(evidence, command_rel,
                                   accepted["native_command_sha256"][environment],
                                   "NATIVE_COMMAND", observed)
        result, command = read_json(result_path), read_json(command_path)
        native[environment] = check_native_semantics(
            result, command, runs, environment, snapshot, evidence, repo, accepted, manifest)
        for stream in ("stdout", "stderr"):
            path = child(evidence, environment + "-run/" + stream + ".log", "NATIVE_LOG")
            observed[str(path)] = digest(path)
        runs_by_environment[environment] = runs
        index_row = machine["environment_statuses"][environment]
        compare_row = comparison["environments"][environment]
        need(index_row["capture_count"] == index_row["passed_capture_count"] == 8 and
             index_row["group_counts_288250"] == 8 and index_row["issues"] == [] and
             index_row["verifier_top_status"] == native[environment]["top_status"] and
             compare_row["issues"] == [] and
             compare_row["verifier_top_status"] == native[environment]["top_status"] and
             compare_row["zip_sha256"] == zip_sha and
             compare_row["input_inventory_exact_mapping_match"] is True,
             "NATIVE_INDEX_ENVIRONMENT_MISMATCH")
        for when in ("before", "after"):
            historical = identity["input_zips_" + when][environment]
            need(historical["sha256"] == zip_sha and historical["bytes"] == zip_id["bytes"],
                 "HISTORICAL_ZIP_IDENTITY_MISMATCH")
            equal_path(historical["path"], child(repo, zip_id["receipt_copy_relative_path"],
                                                 "HISTORICAL_ZIP_COPY"), "HISTORICAL_ZIP_COPY")
    return dict(accepted=accepted, roots=dict(algorithm=str(repo), snapshot=str(snapshot),
                                               s1_evidence=str(evidence)),
                mapping_sha256=accepted["mapping_sha256"], manifest_sha256=accepted["snapshot_manifest_sha256"],
                algorithm_head=head, algorithm_direct_files=[str(p) for p in direct],
                input_sha256=observed, native=native, runs=runs_by_environment)


def unchanged(observed):
    need(all(digest(pathlib.Path(path)) == expected for path, expected in observed.items()),
         "METADATA_CHANGED_DURING_RUN")


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
    for name in ("repo", "s1-snapshot-root", "s1-evidence-root", "mapping", "out"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--expected-commit", required=True,
                        help="exact 40-character reviewed B commit SHA; supplied externally")
    for name in ("zip", "environment", "receipt"):
        parser.add_argument("--" + name)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args(argv)
    root = pathlib.Path(args.repo).resolve()
    output = pathlib.Path(args.out).resolve()
    need(not output.exists(), "OUTPUT_ALREADY_EXISTS")
    pre_identity = execution_identity(root, args.expected_commit, pathlib.Path(__file__))
    mapping_path = pathlib.Path(args.mapping).resolve()
    context = load_context(root, args.s1_snapshot_root, args.s1_evidence_root, mapping_path)
    command = ([sys.executable, str(pathlib.Path(__file__).resolve())] +
               (list(argv) if argv is not None else sys.argv[1:]))
    common = dict(roots=context["roots"], algorithm_head=context["algorithm_head"],
                  algorithm_parent_commit=context["accepted"]["algorithm_parent_commit"],
                  snapshot_candidate=context["accepted"]["snapshot_candidate"],
                  mapping_sha256=context["mapping_sha256"],
                  snapshot_manifest_sha256=context["manifest_sha256"],
                  input_sha256=context["input_sha256"],
                  source_sha256=digest(pathlib.Path(__file__)),
                  command=command, cwd=str(pathlib.Path.cwd()),
                  tools=dict(python=platform.python_version(), numpy=np.__version__),
                  evidence_profile="DIAGNOSTIC_SMOKE", claim_stage="PREFLIGHT")
    if args.preflight_only:
        need(args.zip is None and args.receipt is None and args.environment is None,
             "PREFLIGHT_HAS_DIAGNOSTIC_ARGUMENTS")
        unchanged(context["input_sha256"])
        post_identity = execution_identity(root, args.expected_commit, pathlib.Path(__file__))
        common["execution_identity"] = dict(before=pre_identity, after=post_identity)
        output.mkdir(parents=True, exist_ok=False)
        result = dict(common, status=PREFLIGHT_STATUS, native_s1=context["native"],
                      not_run=["real ZIP/BIN/LOG read", "PCM extraction", "DOA/Tracker",
                               "audio", "formal scoring"],
                      limit="Metadata identity and partial raw-UART records only; ZIP bytes not reverified")
        (output / "result.json").write_text(json.dumps(result, ensure_ascii=False,
                                                        indent=2, allow_nan=False) + "\n",
                                            encoding="utf-8")
        print(json.dumps(dict(status=PREFLIGHT_STATUS, environments=list(context["native"]),
                              out=str(output))))
        return
    need(args.zip and args.receipt and args.environment in ENVIRONMENTS,
         "DIAGNOSTIC_ARGUMENTS_REQUIRED")
    environment = args.environment
    evidence = pathlib.Path(context["roots"]["s1_evidence"])
    receipt_path = child(evidence, environment + "-run/verifier-output/result.json", "NATIVE_RESULT")
    equal_path(args.receipt, receipt_path, "NATIVE_RESULT")
    zip_path = pathlib.Path(args.zip).resolve()
    equal_path(zip_path, context["accepted"]["zip"][environment]["original_path"],
               "ORIGINAL_ZIP")
    need(zip_path.stat().st_size == context["accepted"]["zip"][environment]["bytes"],
         "ORIGINAL_ZIP_SIZE_MISMATCH")
    runs = context["runs"][environment]
    pcm = read_pcm(zip_path, runs, context["accepted"]["zip"][environment]["sha256"])
    direct = [pathlib.Path(p) for p in context["algorithm_direct_files"]]
    cfg = read_json(direct[0])
    act = module("two_env_activity", direct[1])
    diag = module("two_env_doa", direct[2])
    trk = module("two_env_tracker", direct[3])
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
    unchanged(context["input_sha256"])
    post_identity = execution_identity(root, args.expected_commit, pathlib.Path(__file__))
    common["execution_identity"] = dict(before=pre_identity, after=post_identity)
    output.mkdir(parents=True, exist_ok=False)
    result = dict(common, status=STATUS, claim_stage="SIM_SMOKE",
                  environment=environment, native_s1=context["native"][environment],
                  native_result_path=str(receipt_path),
                  source_zip_sha256=context["accepted"]["zip"][environment]["sha256"],
                  source_members={r["stem"]: {k: dict(path=r[k]["source_member_path"],
                                                    sha256=r[k]["source_member_sha256"])
                                              for k in ("bin", "log")} for r in runs},
                  reference_source=pre_stem_from_runs(runs),
                  pre_background_power=noise, captures=summaries,
                  frames=len(frames),
                  reference_commit=REFERENCE_COMMIT,
                  assumptions=dict(geometry="candidate 40 mm coplanar square; not measured for these recordings",
                                   positions_m=positions.tolist(), pair_bounds_samples=bounds,
                                   sample_rate_hz=48000, sound_speed_m_s=343,
                                   playback_identity="USER_REPORTED_NOT_BYTE_VERIFIED"),
                  limits="Native S1 is partial raw-UART only; no formal direction or SNR acceptance")
    for name, value in (("result.json", result), ("frames.json", frames)):
        (output / name).write_text(json.dumps(value, ensure_ascii=False, indent=2,
                                            allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(dict(status=STATUS, environment=args.environment,
                          captures=len(summaries), frames=len(frames), out=str(output))))


def pre_stem_from_runs(runs):
    return next(r["stem"] for r in runs if r["scene"] == "bg_pre")


if __name__ == "__main__":
    main()
