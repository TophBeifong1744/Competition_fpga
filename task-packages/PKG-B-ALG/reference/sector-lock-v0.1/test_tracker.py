import dataclasses
import sys
import unittest
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from tracker import Config, Tracker, angle


def direction(az, el=0):
    a, e = np.deg2rad([az, el])
    return np.array([np.cos(e)*np.cos(a), np.cos(e)*np.sin(a), np.sin(e)])


class TrackerContract(unittest.TestCase):
    def lock(self, tracker, az=0):
        for t in range(0, 50, 10):
            result = tracker.update(t, direction(az), True)
        self.assertTrue(result['fresh_valid'])
        return result

    def test_requires_five_consecutive_frames(self):
        tr = Tracker()
        for t in range(4):
            r = tr.update(t*10, direction(0), True)
            self.assertFalse(r['fresh_valid'])
        self.assertTrue(tr.update(40, direction(0), True)['fresh_valid'])

    def test_rejection_breaks_acquisition(self):
        tr = Tracker()
        for t in range(4): tr.update(t*10, direction(0), True)
        tr.update(40, None, False)
        self.assertEqual(tr.update(50, direction(0), True)['acquire_count'], 1)

    def test_stable_outside_cone_never_locks(self):
        tr = Tracker()
        for t in range(20): self.assertFalse(tr.update(t*10, direction(90), True)['fresh_valid'])

    def test_cone_boundary_inclusive(self):
        self.lock(Tracker(), az=30)

    def test_hold_is_not_fresh_or_scoreable(self):
        tr = Tracker(); self.lock(tr)
        r = tr.update(50, None, False)
        self.assertTrue(r['stale']); self.assertFalse(r['fresh_valid'])
        self.assertIsNone(r['direction']); self.assertIsNotNone(r['display_direction'])

    def test_hold_expires_then_full_reacquisition(self):
        tr = Tracker(); self.lock(tr)
        for t in range(50, 241, 10): tr.update(t, None, False)
        r = tr.update(250, direction(0), True)
        self.assertEqual(r['state'], 'ACQUIRE'); self.assertEqual(r['acquire_count'], 1)

    def test_hold_boundary(self):
        tr = Tracker(); self.lock(tr)
        for t in range(50, 241, 10): r = tr.update(t, None, False)
        self.assertEqual(r['state'], 'HOLD')
        self.assertEqual(tr.update(250, None, False)['state'], 'SEARCH')

    def test_fresh_recovery_within_hold(self):
        tr = Tracker(); self.lock(tr)
        tr.update(50, None, False)
        self.assertTrue(tr.update(60, direction(2), True)['fresh_valid'])

    def test_jump_inside_cone_is_rejected(self):
        tr = Tracker(); self.lock(tr, -20)
        self.assertEqual(tr.update(50, direction(20), True)['reason'], 'track_jump')

    def test_stale_input_gap_forces_reacquisition(self):
        tr = Tracker(); self.lock(tr)
        r = tr.update(100, direction(0), True)
        self.assertFalse(r['fresh_valid']); self.assertEqual(r['acquire_count'], 1)

    def test_manual_release(self):
        tr = Tracker(); self.lock(tr); tr.reset()
        self.assertFalse(tr.update(50, direction(0), True)['fresh_valid'])

    def test_config_change_releases_lock(self):
        tr = Tracker(); self.lock(tr)
        tr.configure(Config(cone_center=(0,1,0)))
        self.assertEqual(tr.update(50, direction(0), True)['state'], 'SEARCH')

    def test_invalid_vectors_never_lock(self):
        tr = Tracker()
        for t, v in enumerate([[0,0,0], [np.nan,0,1], [1,2], [np.inf,0,0], None]):
            self.assertFalse(tr.update(t*10, v, True)['fresh_valid'])

    def test_bad_timestamp_does_not_change_state(self):
        tr = Tracker(); self.lock(tr)
        for t in [40, 30, -1, np.nan, np.inf]:
            with self.assertRaises(ValueError): tr.update(t, direction(0), True)
            self.assertEqual(tr.state, 'LOCKED'); self.assertEqual(tr.last_input_ms, 40)

    def test_angles_wrap_without_discontinuity(self):
        tr = Tracker(Config(cone_center=(-1,0,0)))
        for t, az in enumerate([179,-179,179,-179,180]): r = tr.update(t*10, direction(az), True)
        self.assertTrue(r['fresh_valid']); self.assertLess(angle(r['direction'], direction(180)), 1)

    def test_pole_direction(self):
        tr = Tracker(Config(cone_center=(0,0,1)))
        for t in range(5): r = tr.update(t*10, direction(70*t,90), True)
        self.assertTrue(r['fresh_valid'])

    def test_acquisition_does_not_accumulate_drift(self):
        tr = Tracker()
        for t, az in enumerate([-12,-6,0,6,12]): r = tr.update(t*10, direction(az), True)
        self.assertFalse(r['fresh_valid'])

    def test_invalid_config(self):
        for key, value in [('cone_center',(0,0,0)), ('acquire_frames',1), ('acquire_frames',2.5),
                           ('hold_ms',-1), ('hold_ms',np.nan), ('max_input_gap_ms',0),
                           ('cone_half_angle_deg',180), ('track_step_deg',0)]:
            with self.assertRaises(ValueError): dataclasses.replace(Config(), **{key:value})


if __name__ == '__main__': unittest.main()
