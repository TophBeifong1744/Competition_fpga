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


def receipt(environment, mapping_sha, zip_sha, runs):
    return dict(kind="FULL_S1_CAPTURE_VERIFICATION", status="PASS_FULL_S1",
                environment=environment, mapping_sha256=mapping_sha,
                source_zip_sha256=zip_sha, entry_commit="a" * 40,
                entry_path="synthetic/entry.py", entry_source_sha256="b" * 64,
                evidence_path="synthetic/result.json", evidence_sha256="d" * 64,
                command=["synthetic", "full-s1"], captures=[
                    dict(canonical_stem=r["stem"], status="PASS_FULL_S1",
                         raw_sha256=r["bin"]["source_member_sha256"],
                         log_sha256=r["log"]["source_member_sha256"])
                    for r in runs])


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

    def test_receipt_must_be_full_s1_and_match_all_hashes(self):
        runs, zip_sha = self.selected("indoor")
        good = receipt("indoor", "c" * 64, zip_sha, runs)
        D.check_receipt(good, "indoor", "c" * 64, zip_sha, runs)
        for field, value in (("kind", "LUNA_MECHANICAL_RECEIPT"),
                             ("environment", "outdoor"),
                             ("mapping_sha256", "0" * 64),
                             ("source_zip_sha256", "0" * 64)):
            bad = json.loads(json.dumps(good))
            bad[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                D.check_receipt(bad, "indoor", "c" * 64, zip_sha, runs)
        bad = json.loads(json.dumps(good))
        bad["captures"][0]["raw_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "RECEIPT_MEMBER_HASH_MISMATCH"):
            D.check_receipt(bad, "indoor", "c" * 64, zip_sha, runs)

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
                    "--out", str(occupied)])

    def test_synthetic_end_to_end_with_pinned_algorithm_dependencies(self):
        repo = next(p for p in HERE.parents if (p / "AGENTS.md").is_file())
        runs, zip_sha = self.selected("indoor")
        mapping_path = self.base / "mapping.json"
        mapping_path.write_text(json.dumps(self.mapping), encoding="utf-8")
        gate = receipt("indoor", D.digest(mapping_path), zip_sha, runs)
        gate["entry_path"] = (HERE / "test_diagnose.py").relative_to(repo).as_posix()
        gate["evidence_path"] = gate["entry_path"]
        gate["entry_source_sha256"] = D.digest(HERE / "test_diagnose.py")
        gate["evidence_sha256"] = gate["entry_source_sha256"]
        receipt_path = self.base / "full-s1-synthetic.json"
        receipt_path.write_text(json.dumps(gate), encoding="utf-8")
        output = self.base / "diagnostic"
        D.main(["--repo", str(repo), "--zip", str(self.archives["indoor"]),
                "--mapping", str(mapping_path), "--environment", "indoor",
                "--receipt", str(receipt_path), "--out", str(output)])
        result = D.read_json(output / "result.json")
        frames = D.read_json(output / "frames.json")
        self.assertEqual(D.STATUS, result["status"])
        self.assertEqual(8, len(result["captures"]))
        self.assertEqual(16, len(frames))
        self.assertEqual(0, sum(r["modes"]["env_pre_background"]["fresh"]
                                for r in result["captures"]))


if __name__ == "__main__":
    unittest.main()
