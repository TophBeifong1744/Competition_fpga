from dataclasses import replace
from pathlib import Path
import sys
import unittest
import numpy as np

PACKAGE=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PACKAGE/'payload/model/python'))
from quorum_tracker import QuorumTracker,CaptureConfig,QuorumSession
from sector_tracker import Config,Tracker
from six_mic_baseline_core import unit


class QuorumTests(unittest.TestCase):
    def lock(self,tr):
        for i in range(5):result=tr.update(i*10,unit(0,0),True)
        self.assertTrue(result['fresh_valid'])

    def test_five_valid_may_be_separated_by_rejections(self):
        old,new=Tracker(),QuorumTracker()
        for i in range(9):
            valid=i%2==0
            a=old.update(i*10,unit(0,0),valid);b=new.update(i*10,unit(0,0),valid)
        self.assertFalse(a['fresh_valid']);self.assertTrue(b['fresh_valid'])
        self.assertEqual(b['reason'],'acquired')

    def test_current_frame_must_be_valid(self):
        tr=QuorumTracker()
        for i in range(4):tr.update(i*10,unit(0,0),True)
        r=tr.update(40,unit(0,0),False)
        self.assertFalse(r['fresh_valid']);self.assertIsNone(r['direction'])

    def test_window_counts_rejected_frames(self):
        tr=QuorumTracker(capture=CaptureConfig(5,5,120))
        for i in range(9):r=tr.update(i*10,unit(0,0),i%2==0)
        self.assertFalse(r['fresh_valid']);self.assertEqual(r['acquire_count'],3)

    def test_age_limit_prevents_old_votes(self):
        tr=QuorumTracker(capture=CaptureConfig(5,12,35))
        for i in range(10):r=tr.update(i*10,unit(0,0),True)
        self.assertFalse(r['fresh_valid']);self.assertEqual(r['acquire_count'],4)

    def test_outside_cone_votes_never_count(self):
        tr=QuorumTracker()
        for i in range(20):r=tr.update(i*10,unit(90,0),True)
        self.assertEqual(r['state'],'SEARCH');self.assertFalse(r['fresh_valid'])

    def test_pairwise_constraint_prevents_accumulated_drift(self):
        tr=QuorumTracker()
        for i,az in enumerate([-12,-6,0,6,12]):r=tr.update(i*10,unit(az,0),True)
        self.assertFalse(r['fresh_valid']);self.assertLess(r['acquire_count'],5)

    def test_one_outlier_does_not_destroy_other_compatible_votes(self):
        tr=QuorumTracker()
        for i,az in enumerate([0,1,25,2,3,0]):r=tr.update(i*10,unit(az,0),True)
        self.assertTrue(r['fresh_valid'])

    def test_locked_hold_and_expiry_match_legacy(self):
        a,b=Tracker(),QuorumTracker();self.lock(a);self.lock(b)
        for t in range(50,281,10):
            valid=t in [50,60,280]
            x,y=a.update(t,unit(2,0),valid),b.update(t,unit(2,0),valid)
            for key in ['state','fresh_valid','stale','display_expires_at_ms']:
                self.assertEqual(x[key],y[key])
            if x['direction'] is not None:np.testing.assert_allclose(x['direction'],y['direction'],atol=1e-14)

    def test_gap_reset_clears_all_votes(self):
        tr=QuorumTracker()
        for i in range(4):tr.update(i*10,unit(0,0),True)
        r=tr.update(100,unit(0,0),True)
        self.assertEqual(r['acquire_count'],1);self.assertFalse(r['fresh_valid'])

    def test_release_and_config_reset_votes(self):
        tr=QuorumTracker();self.lock(tr);tr.reset()
        self.assertEqual(tr.update(50,unit(0,0),True)['acquire_count'],1)
        tr.configure(Config(cone_center=(0,1,0)))
        self.assertEqual(tr.update(60,unit(90,0),True)['acquire_count'],1)

    def test_session_consumes_reset_before(self):
        session=QuorumSession()
        for i in range(6):
            r=session.update(dict(end_seconds_exclusive=(20+i*10)/1000,unit_vector=[1,0,0],valid=True,reset_before=i==5))
        self.assertFalse(r['fresh_valid']);self.assertEqual(r['acquire_count'],1)

    def test_bad_config_and_clock(self):
        for args in [(True,12,120),(5,4,120),(5,65,120),(5,12,True),(5,12,float('nan'))]:
            with self.assertRaises(ValueError):CaptureConfig(*args)
        tr=QuorumTracker();self.lock(tr)
        for t in [40,-1,float('nan')]:
            with self.assertRaises(ValueError):tr.update(t,unit(0,0),True)
            self.assertEqual(tr.state,'LOCKED')


if __name__=='__main__':unittest.main()
