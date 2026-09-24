"""Contract tests use synthetic ZIPs and PCM only; no received capture is opened."""

import hashlib
import importlib.util
import json
import pathlib
import tempfile
import unittest
import zipfile

import numpy as np


HERE = pathlib.Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("two_environment_diagnostic", HERE / "diagnose.py")
D = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(D)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def fixture(base):
    """Independent expectation: two 8-run environments, same legacy member names."""
    rows, archives, pcm = [], {}, {}
    for environment, base_value in (("indoor", 2), ("outdoor", 3)):
        archive = base / (environment + ".zip")
        members = {}
        for scene, runs in D.SCENES.items():
            for run in runs:
                stem = D.canonical(environment, scene, run)
                legacy = "same_names/{}_{}".format(scene, run)
                value = base_value if scene == "bg_pre" else 7
                sample = np.zeros((1536, 8), dtype="<u4")
                sample[:, 2:6] = value
                binary = sample.tobytes()
                log = ("synthetic " + stem).encode()
                members[legacy + ".bin"] = binary
                members[legacy + ".log"] = log
                pcm[stem] = np.full((1536, 4), value, dtype=np.int32)
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_STORED) as z:
            for name, payload in members.items():
                z.writestr(name, payload)
        archives[environment] = archive
        zip_sha = D.digest(archive)
        for scene, runs in D.SCENES.items():
            for run in runs:
                stem = D.canonical(environment, scene, run)
                legacy = "same_names/{}_{}".format(scene, run)
                for ext in (".bin", ".log"):
                    source = legacy + ext
                    payload = members[source]
                    rows.append(dict(environment=environment, scene=scene, run_tag=run,
                                     extension=ext, canonical_stem=stem, date=D.DATE,
                                     standard_name=stem + ext,
                                     standard_relative_path="normalized/{}/{}{}".format(
                                         environment, stem, ext),
                                     source_member_path=source, source_name=source,
                                     source_stem=legacy.rsplit("/", 1)[1],
                                     source_zip_path=str(archive), source_zip_sha256=zip_sha,
                                     source_member_sha256=sha(payload),
                                     target_sha256=sha(payload), source_bytes=len(payload),
                                     target_bytes=len(payload), byte_identical=True))
    return {"files": rows}, archives, pcm


def synthetic_native(base, environment, runs, archive):
    """Independent synthetic native-format record; no received result is copied."""
    repo, snapshot, evidence = (base / n for n in ("repo", "snapshot", "evidence"))
    for root in (repo, snapshot, evidence):
        root.mkdir()
    source = "task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/c-recording-receipt-20260922/verify_zip.py"
    finish = "task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/background-target-stop-20260917/finish_scene.py"
    export = "task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/source/export_four.py"
    manifest = {"files": {source: {"sha256": "a" * 64}, finish: {"sha256": "b" * 64},
                          export: {"sha256": "c" * 64}}}
    accepted = dict(verify_zip_sha256="a" * 64, finish_scene_sha256="b" * 64,
                    native_result_sha256={environment: "d" * 64},
                    native_command_sha256={environment: "e" * 64},
                    zip={environment: dict(sha256=D.digest(archive), bytes=archive.stat().st_size,
                                           receipt_copy_relative_path="copies/" + environment + ".zip")})
    result = dict(status="PARTIAL_RECEIPT_PENDING_POSITION_AND_PROVENANCE", passed=8,
                  all_raw_unique=True, zip_sha256=D.digest(archive),
                  zip_bytes=archive.stat().st_size, zip_name=environment + ".zip",
                  source_sha256="a" * 64,
                  dependencies={finish: "b" * 64, export: "c" * 64},
                  python="3.7.0", numpy="1.21.6",
                  missing=["missing"] * 6, not_tested=["not tested"] * 5,
                  input_sha256={r[k]["source_member_path"]: r[k]["source_member_sha256"]
                                for r in runs for k in ("bin", "log")},
                  inventory=[dict(path=r[k]["source_member_path"],
                                  bytes=r[k]["source_bytes"], crc32="1234ABCD")
                             for r in runs for k in ("bin", "log")],
                  captures=[dict(name=r["bin"]["source_stem"],
                                 raw_sha256=r["bin"]["source_member_sha256"],
                                 log_sha256=r["log"]["source_member_sha256"],
                                 status="PASS_RAW_UART_ONLY", checked=dict(groups=288250,
                                                                            flagged_rows=0,
                                                                            bytes=r["bin"]["source_bytes"]))
                            for r in runs])
    snap_tree = snapshot / "snapshot"
    run_root = evidence / (environment + "-run")
    run_root.mkdir()
    (run_root / "stdout.log").write_text("SYNTHETIC\n", encoding="utf-8")
    (run_root / "stderr.log").write_text("", encoding="utf-8")
    command = dict(argv=["synthetic-python", "-B", str(snap_tree / source),
                         "--repo", str(snap_tree), "--zip",
                         str(repo / accepted["zip"][environment]["receipt_copy_relative_path"]),
                         "--out", str(run_root / "verifier-output")],
                   cwd=str(snap_tree), environment=environment, returncode=0,
                   spawn_error=None, python_executable="synthetic-python",
                   python_version="3.7.0", numpy_version="1.21.6",
                   result_path=str(run_root / "verifier-output/result.json"),
                   stdout_path=str(run_root / "stdout.log"),
                   stderr_path=str(run_root / "stderr.log"),
                   started_utc="synthetic-start", finished_utc="synthetic-end",
                   elapsed_seconds=1.0)
    return result, command, manifest, accepted, repo, snapshot, evidence


class Gate:
    def __init__(self, noise, cfg):
        self.noise = np.asarray(noise)

    def update(self, power, invalid):
        return not invalid


class Tracker:
    created = []

    def __init__(self):
        self.times = []
        self.resets = 0
        self.created.append(self)

    def reset(self):
        self.resets += 1

    def update(self, time_ms, direction, accepted):
        self.times.append(time_ms)
        # The independent fixture expects one fresh sample followed by a held display.
        first = len(self.times) == 1 and accepted
        return dict(state="LOCKED" if first else "HOLD", fresh_valid=first,
                    reason="acquired" if first else "baseline_rejected")


def features(frame):
    return dict(band_power=(frame[0, :].astype(float) ** 2).tolist(), endpoint=False)


def locate(frame):
    return dict(advisory_consistent=True, advisory_azimuth_deg=0.0), ["VALID"] * 6, [0] * 6


CFG = dict(frame_length=1024, hop=512, sample_rate_hz=48000,
           background_percentile=95, tracker_cone_half_angle_deg=60,
           band_bins_inclusive=[7, 72], band_rms_floor_codes=512,
           on_power_ratio=4, off_power_ratio=2, attack_frames=3,
           release_frames=3, minimum_active_channels=3)


class TwoEnvironmentTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = pathlib.Path(self.tmp.name)
        self.mapping, self.archives, self.pcm = fixture(self.base)

    def selected(self, environment):
        return D.mapping_for_environment(self.mapping, environment,
                                         self.archives[environment])

    def test_same_member_names_bind_to_distinct_zip_and_environment(self):
        indoor, indoor_sha = self.selected("indoor")
        outdoor, outdoor_sha = self.selected("outdoor")
        self.assertEqual(8, len(indoor))
        self.assertEqual(8, len(outdoor))
        self.assertNotEqual(indoor_sha, outdoor_sha)
        self.assertEqual(indoor[0]["bin"]["source_member_path"],
                         outdoor[0]["bin"]["source_member_path"])
        self.assertNotEqual(indoor[0]["bin"]["source_member_sha256"],
                            outdoor[0]["bin"]["source_member_sha256"])
        self.assertEqual(8, len(D.read_pcm(self.archives["indoor"], indoor, indoor_sha)))

    def test_only_local_pre_background_builds_reference(self):
        indoor, _ = self.selected("indoor")
        outdoor, _ = self.selected("outdoor")
        noise_in, _, _ = D.analyze(indoor, self.pcm, CFG, features, locate, Gate, Tracker)
        noise_out, _, _ = D.analyze(outdoor, self.pcm, CFG, features, locate, Gate, Tracker)
        self.assertEqual([4.0] * 4, noise_in)
        self.assertEqual([9.0] * 4, noise_out)
        changed = dict(self.pcm)
        for run in indoor:
            if run["scene"] != "bg_pre":
                changed[run["stem"]] = np.full((1536, 4), 1000, dtype=np.int32)
        after, _, _ = D.analyze(indoor, changed, CFG, features, locate, Gate, Tracker)
        self.assertEqual([4.0] * 4, after)

    def test_full_windows_fresh_hold_and_time_restart_per_run(self):
        Tracker.created.clear()
        indoor, _ = self.selected("indoor")
        _, frames, summaries = D.analyze(indoor, self.pcm, CFG, features, locate,
                                          Gate, Tracker)
        self.assertEqual(16, len(frames))  # eight independent runs, two full windows each
        self.assertEqual(16, len(Tracker.created))  # two independent modes per run
        for run in indoor:
            rows = [f for f in frames if f["capture"] == run["stem"]]
            self.assertEqual([(0, 1024), (512, 1536)],
                             [(r["start"], r["stop"]) for r in rows])
            self.assertAlmostEqual(1024 / 48, rows[0]["timestamp_ms"])
            self.assertAlmostEqual(1536 / 48, rows[1]["timestamp_ms"])
            self.assertEqual(["LOCKED", "HOLD"],
                             [r["trackers"]["no_gate"]["state"] for r in rows])
        for summary in summaries:
            self.assertEqual(2, summary["frames"])
            self.assertEqual(1, summary["modes"]["env_pre_background"]["fresh"])
            self.assertEqual(1, summary["modes"]["env_pre_background"]["hold"])
            self.assertEqual(1, summary["modes"]["env_pre_background"]["rejected"])

    def test_nonactivity_preserves_old_tracker_reset_path(self):
        class ClosesOnSecondFrame(Gate):
            def __init__(self, noise, cfg):
                super().__init__(noise, cfg)
                self.calls = 0

            def update(self, power, invalid):
                self.calls += 1
                return self.calls == 1

        Tracker.created.clear()
        indoor, _ = self.selected("indoor")
        _, frames, _ = D.analyze(indoor, self.pcm, CFG, features, locate,
                                  ClosesOnSecondFrame, Tracker)
        self.assertEqual(8, sum(not f["activity"]["env_pre_background"] for f in frames))
        self.assertEqual(0, sum(t.resets for t in Tracker.created[::2]))
        self.assertEqual(8, sum(t.resets for t in Tracker.created[1::2]))

    def test_mapping_identity_rejections(self):
        with self.assertRaisesRegex(ValueError, "ZIP_PATH_MISMATCH"):
            D.mapping_for_environment(self.mapping, "indoor", self.archives["outdoor"])
        for field, value in (("environment", "outdoor"),
                             ("source_member_sha256", "0" * 64),
                             ("standard_name", "wrong.bin")):
            altered = json.loads(json.dumps(self.mapping))
            altered["files"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                D.mapping_for_environment(altered, "indoor", self.archives["indoor"])
        altered = json.loads(json.dumps(self.mapping))
        altered["files"].pop()
        with self.assertRaisesRegex(ValueError, "MAPPING_NEEDS_32_FILES"):
            D.mapping_for_environment(altered, "indoor", self.archives["indoor"])

    def test_partial_native_result_and_finished_command_bind_by_source_name(self):
        runs, _ = self.selected("indoor")
        result, command, manifest, accepted, repo, snapshot, evidence = synthetic_native(
            self.base, "indoor", runs, self.archives["indoor"])
        result["captures"].reverse()  # order is not a binding key
        checked = D.check_native_semantics(result, command, runs, "indoor", snapshot,
                                           evidence, repo, accepted, manifest)
        self.assertEqual("PARTIAL_RECEIPT_PENDING_POSITION_AND_PROVENANCE",
                         checked["top_status"])
        self.assertEqual({"PASS_RAW_UART_ONLY"}, set(checked["capture_statuses"].values()))
        self.assertEqual(6, len(checked["missing"]))
        self.assertEqual(5, len(checked["not_tested"]))

    def test_native_semantic_negative_cases_after_synthetic_identity_gate(self):
        runs, _ = self.selected("indoor")
        result, command, manifest, accepted, repo, snapshot, evidence = synthetic_native(
            self.base, "indoor", runs, self.archives["indoor"])
        cases = [
            ("top status", "result", "status", "PASS_FULL_S1"),
            ("missing run", "result", "captures", result["captures"][:-1]),
            ("wrong member", "result", "input_sha256", {}),
            ("wrong source", "result", "source_sha256", "0" * 64),
            ("wrong environment", "command", "environment", "outdoor"),
            ("failed command", "command", "returncode", 1),
        ]
        for label, which, key, value in cases:
            changed_result = json.loads(json.dumps(result))
            changed_command = json.loads(json.dumps(command))
            (changed_result if which == "result" else changed_command)[key] = value
            with self.subTest(label=label), self.assertRaises(ValueError):
                D.check_native_semantics(changed_result, changed_command, runs, "indoor",
                                         snapshot, evidence, repo, accepted, manifest)
        wrong_command = json.loads(json.dumps(command))
        wrong_command["argv"][8] = str(repo / "outside-output")
        with self.assertRaises(ValueError):
            D.check_native_semantics(result, wrong_command, runs, "indoor", snapshot,
                                     evidence, repo, accepted, manifest)
        wrong_command = json.loads(json.dumps(command))
        wrong_command["argv"][6] = str(self.archives["outdoor"])
        with self.assertRaises(ValueError):
            D.check_native_semantics(result, wrong_command, runs, "indoor", snapshot,
                                     evidence, repo, accepted, manifest)

    def test_fixed_hash_and_cross_root_rejections_are_separate_from_semantics(self):
        root = self.base / "root"
        root.mkdir()
        path = root / "metadata.json"
        path.write_text("synthetic", encoding="utf-8")
        observed = {}
        self.assertEqual(path.resolve(), D.locked_file(root, "metadata.json", D.digest(path),
                                                       "SYNTHETIC", observed))
        with self.assertRaisesRegex(ValueError, "SYNTHETIC_HASH_MISMATCH"):
            D.locked_file(root, "metadata.json", "0" * 64, "SYNTHETIC", observed)
        with self.assertRaisesRegex(ValueError, "SYNTHETIC_OUTSIDE_ROOT"):
            D.child(root, "../out-of-root.json", "SYNTHETIC")

    def test_zip_member_hash_and_existing_output_rejected(self):
        runs, zip_sha = self.selected("indoor")
        altered = json.loads(json.dumps(runs))
        altered[0]["bin"]["source_member_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "ZIP_MEMBER_HASH_MISMATCH"):
            D.read_pcm(self.archives["indoor"], altered, zip_sha)
        occupied = self.base / "occupied"
        occupied.mkdir()
        with self.assertRaisesRegex(ValueError, "OUTPUT_ALREADY_EXISTS"):
            D.main(["--repo", str(self.base), "--zip", str(self.archives["indoor"]),
                    "--mapping", str(self.base / "absent.json"),
                    "--environment", "indoor", "--receipt", str(self.base / "absent.json"),
                    "--s1-snapshot-root", str(self.base),
                    "--s1-evidence-root", str(self.base), "--out", str(occupied)])

    def test_real_locked_tracker_synthetic_hold_is_not_fresh(self):
        tracker_path = (next(p for p in HERE.parents if (p / "AGENTS.md").is_file()) /
                        "task-packages/PKG-B-ALG/payload/model/python/sector_tracker.py")
        tracker = D.module("locked_real_tracker_synthetic", tracker_path)
        self.assertEqual("2297aa7f94058e3e4faf3da792c6f1beef6c68fa72121100ec672d60ade5ec50",
                         D.digest(tracker_path))
        stem = "synthetic_indoor_bg_pre"
        run = dict(stem=stem, scene="bg_pre", bin={"environment": "indoor"})
        pcm = {stem: np.ones((4096, 4), dtype=np.int32)}  # seven complete windows
        angles = iter([0, 0, 0, 0, 0, 45, 45])

        def controlled_locate(_):
            return dict(advisory_consistent=True,
                        advisory_azimuth_deg=next(angles)), ["VALID"] * 6, [0] * 6

        _, frames, summary = D.analyze([run], pcm, CFG, features, controlled_locate,
                                       Gate, lambda: tracker.Tracker(
                                           tracker.Config(cone_half_angle_deg=60)))
        self.assertEqual(7, len(frames))
        self.assertEqual(["ACQUIRE", "ACQUIRE", "ACQUIRE", "ACQUIRE", "LOCKED", "HOLD", "HOLD"],
                         [f["trackers"]["env_pre_background"]["state"] for f in frames])
        self.assertEqual({"fresh": 1, "hold": 2, "rejected": 6},
                         {k: summary[0]["modes"]["env_pre_background"][k]
                          for k in ("fresh", "hold", "rejected")})


if __name__ == "__main__":
    unittest.main()
