from dataclasses import asdict,replace
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import numpy as np

PACKAGE=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PACKAGE/'payload/model/python'))
import six_mic_track as tracking
import six_mic_localize as entry
from sector_tracker import Config,Tracker


def row(t,az=0,valid=True,reset=False):
    return dict(end_seconds_exclusive=t/1000,unit_vector=entry.baseline.unit(az,0).tolist() if valid else None,
                valid=valid,reset_before=reset)


class TrackingIntegration(unittest.TestCase):
    def lock(self,session):
        for i in range(5): result=session.update(row(20+i*10,reset=i==0))
        self.assertTrue(result['fresh_valid'])

    def test_old_tracker_is_byte_identical(self):
        self.assertEqual((PACKAGE/'payload/model/python/sector_tracker.py').read_bytes(),
                         (PACKAGE/'reference/sector-lock-v0.1/tracker.py').read_bytes())

    def test_500_updates_match_legacy_tracker(self):
        spec=importlib.util.spec_from_file_location('legacy_sector_tracker',PACKAGE/'reference/sector-lock-v0.1/tracker.py')
        old=importlib.util.module_from_spec(spec);sys.modules[spec.name]=old;spec.loader.exec_module(old)
        a,b=Tracker(),old.Tracker()
        rng=np.random.default_rng(42);t=0
        for i in range(500):
            t+=float(rng.choice([10,10,10,40]))
            if i%95==0: a.reset();b.reset()
            if i%111==0:
                a.configure(Config(cone_half_angle_deg=40));b.configure(old.Config(cone_half_angle_deg=40))
            az=float(rng.choice([0,0,0,5,30,80]));valid=bool(rng.random()>.15)
            direction=entry.baseline.unit(az,0)
            self.assertEqual(a.update(t,direction,valid),b.update(t,direction,valid))

    def test_framing_reset_releases_existing_lock(self):
        session=tracking.TrackingSession();self.lock(session)
        result=session.update(row(70,reset=True))
        self.assertEqual(result['state'],'ACQUIRE');self.assertEqual(result['acquire_count'],1)
        self.assertTrue(result['input_reset']);self.assertIsNone(result['display_direction'])

    def test_gap_resets_before_hold(self):
        session=tracking.TrackingSession();self.lock(session)
        result=session.update(row(100))
        self.assertEqual(result['reason'],'gap_reset_acquire')
        self.assertFalse(result['fresh_valid'])

    def test_hold_expiry_and_full_reacquisition(self):
        session=tracking.TrackingSession();self.lock(session)
        for t in range(70,261,10): result=session.update(row(t,valid=False))
        self.assertEqual(result['state'],'HOLD')
        self.assertEqual(result['display_expires_at_ms'],260)
        self.assertFalse(result['fresh_valid']);self.assertIsNone(result['direction'])
        result=session.update(row(270,valid=False))
        self.assertEqual(result['state'],'SEARCH');self.assertIsNone(result['display_direction'])
        for t in range(280,321,10): result=session.update(row(t))
        self.assertEqual(result['reason'],'acquired')

    def test_release_and_configure_require_new_acquisition(self):
        session=tracking.TrackingSession();self.lock(session);session.release()
        self.assertEqual(session.update(row(70))['acquire_count'],1)
        session.configure(Config(cone_center=(0,1,0)))
        self.assertEqual(session.update(row(80))['reason'],'outside_cone')
        for t in range(90,131,10): result=session.update(row(t,az=90))
        self.assertTrue(result['fresh_valid'])

    def test_invalid_clock_cannot_reset_active_lock(self):
        session=tracking.TrackingSession();self.lock(session)
        for t in [60,50,float('nan')]:
            with self.assertRaises(ValueError):session.update(row(t,reset=True))
            self.assertEqual(session.tracker.state,'LOCKED')

    def test_strict_configuration_boundary(self):
        for change in [dict(hold_ms=True),dict(cone_center=['1',0,0]),dict(cone_center=[True,0,0]),
                       dict(acquire_frames=1),dict(max_input_gap_ms=0),dict(cone_half_angle_deg=100),
                       dict(hold_ms=float('nan')),dict(extra=1)]:
            with self.subTest(change=change),self.assertRaises(ValueError):
                tracking.config_from_dict(asdict(Config())|change)

    def test_same_cone_competitor_is_not_identity_protected(self):
        session=tracking.TrackingSession();self.lock(session)
        result=session.update(row(70,az=10))
        self.assertTrue(result['fresh_valid'])
        self.assertEqual(result['reason'],'track_update')

    def test_fresh_stream_no_truth_input(self):
        a,b=tracking.TrackingSession(),tracking.TrackingSession()
        for i in range(6):
            original=row(20+i*10)
            extra=original|dict(truth_unit_vector=[0,1,0],target_present=False,scenario='adversarial')
            self.assertEqual(a.update(original),b.update(extra))


class AcousticTracking(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);self.root=Path(tmp.name)

    def make(self,scenario):
        path=self.root/scenario;tracking.write_demo(path,scenario)
        return entry.load_input(path)

    def test_stable_fifth_frame_lock_and_baseline_unchanged(self):
        segment,truth=self.make('stable')
        original,summary=entry.run_segment(segment,truth)
        rows,report=tracking.run_tracking(segment,truth)
        self.assertEqual([r['baseline'] for r in rows],original)
        self.assertEqual(report['baseline'],summary)
        self.assertEqual(len(rows),89)
        self.assertTrue(all(not r['tracking']['fresh_valid'] for r in rows[:4]))
        self.assertEqual(rows[4]['tracking']['reason'],'acquired')
        self.assertAlmostEqual(report['tracking']['first_lock_ready_ms'],64)
        self.assertEqual(report['tracking']['valid_frames'],85)

    def test_dropout_hold_search_and_reacquisition(self):
        segment,truth=self.make('drop-return')
        self.assertIsNone(truth)
        rows,report=tracking.run_tracking(segment,truth)
        self.assertEqual(set(report['tracking']['state_counts']),{'SEARCH','ACQUIRE','LOCKED','HOLD'})
        self.assertEqual(report['tracking']['acquisitions'],2)
        self.assertIsNone(report['tracking']['p95_error_deg'])
        hold=[r['tracking'] for r in rows if r['tracking']['state']=='HOLD']
        self.assertTrue(hold)
        self.assertTrue(all(r['stale'] and not r['fresh_valid'] and r['direction'] is None for r in hold))
        self.assertTrue(all(r['timestamp_ms']<=r['display_expires_at_ms'] for r in hold))

    def test_outside_never_locks_and_config_can_select_it(self):
        segment,truth=self.make('outside')
        rows,summary=tracking.run_tracking(segment,truth)
        self.assertGreater(summary['baseline']['valid_frames'],0)
        self.assertEqual(summary['tracking']['valid_frames'],0)
        self.assertIsNone(summary['tracking']['p95_error_deg'])
        _,changed=tracking.run_tracking(segment,truth,Config(cone_center=(0,1,0)))
        self.assertEqual(changed['tracking']['valid_frames'],85)

    def test_independent_runs_do_not_carry_state(self):
        segment,truth=self.make('stable')
        a=tracking.run_tracking(segment,truth);b=tracking.run_tracking(segment,truth)
        self.assertEqual(a,b)

    def test_short_previous_baseline_demo_cannot_lock(self):
        path=self.root/'short';entry.write_demo(path,'clean',0,0,0)
        segment,truth=entry.load_input(path)
        rows,summary=tracking.run_tracking(segment,truth)
        self.assertEqual(len(rows),2);self.assertEqual(summary['tracking']['valid_frames'],0)

    def test_cli_replay_no_overwrite_and_config_recorded(self):
        def call(*args):
            return subprocess.run([sys.executable,'-B',tracking.__file__,*map(str,args)],capture_output=True,text=True)
        output=self.root/'run'; replay=self.root/'replay'
        config=PACKAGE/'payload/config/sector-tracking.json'
        result=call('--demo','stable','--config',config,'--out',output)
        self.assertEqual(result.returncode,0,result.stderr)
        result=call('--input',output/'input','--config',config,'--out',replay)
        self.assertEqual(result.returncode,0,result.stderr)
        for name in ['frames.json','summary.json','run.json','tracking-config.json']:
            self.assertEqual((output/name).read_bytes(),(replay/name).read_bytes())
        before=(output/'frames.json').read_bytes()
        result=call('--demo','stable','--out',output)
        self.assertEqual(result.returncode,2)
        self.assertEqual((output/'frames.json').read_bytes(),before)


if __name__=='__main__':unittest.main()
