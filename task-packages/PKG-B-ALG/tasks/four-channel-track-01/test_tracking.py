"""Contract tests using algebraic directions and zeros, not acoustic simulation."""
import copy
from dataclasses import asdict
import json
import math
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from tracking import Config, DiagnosticSession, horizontal_candidate
from run import diagnostic, replay
from h1_reader import ReaderSession


def candidate(az=0):
    return dict(advisory_consistent=True, advisory_azimuth_deg=az, direction_accepted=False)


class TrackingContract(unittest.TestCase):
    def lock(self, session=None, az=0):
        session = session or DiagnosticSession()
        for t in (20, 30, 40, 50, 60):
            result = session.update(t, candidate(az), interval_index=0)
        self.assertEqual(result['tracker']['state'], 'LOCKED')
        return session, result

    def test_default_contract_unchanged(self):
        self.assertEqual(asdict(Config()), dict(cone_center=(1.,0.,0.), cone_half_angle_deg=30.,
            acquire_frames=5, acquire_spread_deg=8., track_step_deg=20., hold_ms=200., max_input_gap_ms=30.))

    def test_horizontal_assumption_and_no_production_acceptance(self):
        v, _ = horizontal_candidate(candidate(90))
        np.testing.assert_allclose(v, [0,1,0], atol=1e-15)
        _, result = self.lock()
        self.assertFalse(result['direction_accepted'])
        self.assertEqual(result['target_presence'], 'unknown')
        self.assertFalse(result['diagnostic_route']['direction_accepted'])

    def test_invalid_candidates_fail_closed(self):
        for p in ({}, dict(advisory_consistent=False, advisory_azimuth_deg=0),
                  candidate(float('nan')), candidate(float('inf')), candidate(None), candidate(True)):
            with self.subTest(p=p):
                session = DiagnosticSession()
                result = session.update(20, p, interval_index=0)
                self.assertEqual(result['tracker']['state'], 'SEARCH')
                self.assertEqual(result['diagnostic_route']['mode'], 'single')

    def test_acquisition_uses_five_frames(self):
        s = DiagnosticSession()
        for t in (20,30,40,50):
            self.assertEqual(s.update(t, candidate(), interval_index=0)['diagnostic_route']['mode'], 'single')
        self.assertEqual(s.update(60, candidate(), interval_index=0)['diagnostic_route']['mode'], 'tracked')

    def test_rejection_breaks_acquisition(self):
        s = DiagnosticSession()
        for t in (20,30,40,50): s.update(t, candidate(), interval_index=0)
        s.update(60, {}, interval_index=0)
        self.assertEqual(s.update(70, candidate(), interval_index=0)['tracker']['acquire_count'], 1)

    def test_cone_inclusive_and_outside(self):
        for az in (-30,30): self.lock(az=az)
        for az in (-30.01,30.01,180):
            s = DiagnosticSession()
            for t in (20,30,40,50,60): r = s.update(t, candidate(az), interval_index=0)
            self.assertEqual(r['tracker']['reason'], 'outside_cone')
            self.assertEqual(r['diagnostic_route']['mode'], 'single')

    def test_acquisition_drift_not_stable(self):
        s = DiagnosticSession()
        for t, az in zip((20,30,40,50,60), (0,4,8,12,16)):
            r = s.update(t, candidate(az), interval_index=0)
        self.assertEqual(r['tracker']['state'], 'ACQUIRE')

    def test_hold_is_not_fresh_and_preserves_old_direction(self):
        s, initial = self.lock()
        r = s.update(70, {}, interval_index=0)
        self.assertEqual(r['tracker']['state'], 'HOLD')
        self.assertIsNone(r['tracker']['direction'])
        self.assertFalse(r['tracker']['fresh_valid'])
        self.assertEqual(r['diagnostic_route']['direction'], initial['candidate_direction'])
        self.assertEqual(r['diagnostic_route']['valid_through_ms'], 260)

    def test_jump_holds_without_chasing(self):
        s, _ = self.lock(az=-20)
        r = s.update(70, candidate(20), interval_index=0)
        self.assertEqual(r['tracker']['reason'], 'track_jump')
        self.assertEqual(r['diagnostic_route']['mode'], 'hold')

    def test_expiry_without_new_frames_for_locked_and_hold(self):
        for hold in (False, True):
            s, _ = self.lock()
            if hold: s.update(70, {}, interval_index=0)
            self.assertNotEqual(s.route_at(260, interval_index=0)['mode'], 'single')
            self.assertEqual(s.route_at(260.0001, interval_index=0)['mode'], 'single')
            self.assertEqual(s.tracker.last_fresh_ms, 60)

    def test_direction_cannot_be_used_before_frame_ready(self):
        s, _ = self.lock()
        self.assertEqual(s.route_at(59.9, interval_index=0)['reason'], 'FRAME_NOT_READY')
        self.assertTrue(s.route_at(60, interval_index=0)['fresh_at_query'])
        self.assertFalse(s.route_at(61, interval_index=0)['fresh_at_query'])

    def test_interval_reset_before_first_complete_frame(self):
        s, _ = self.lock()
        s.begin_interval(1)
        self.assertEqual(s.route_at(61, interval_index=1)['mode'], 'single')
        self.assertEqual(s.update(80, candidate(), interval_index=1)['tracker']['state'], 'ACQUIRE')

    def test_wrong_interval_and_explicit_reset(self):
        s, _ = self.lock()
        self.assertEqual(s.route_at(61, interval_index=1)['mode'], 'single')
        self.assertEqual(s.update(70, candidate(), interval_index=0, reset_before=True)['tracker']['state'], 'ACQUIRE')

    def test_gap_resets_tracker(self):
        s, _ = self.lock()
        r = s.update(91, candidate(), interval_index=0)
        self.assertEqual(r['tracker']['reason'], 'gap_reset_acquire')
        self.assertEqual(r['diagnostic_route']['mode'], 'single')

    def test_invalid_clock_does_not_reset_good_state(self):
        s, _ = self.lock()
        for t in (60,59,-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError): s.update(t, candidate(), interval_index=1, reset_before=True)
            self.assertEqual(s.tracker.state, 'LOCKED')
        with self.assertRaises(ValueError): s.route_at(-1, interval_index=0)

    def test_returned_route_cannot_mutate_tracker(self):
        s, result = self.lock()
        result['tracker']['display_direction'][0] = -1
        route = s.route_at(61, interval_index=0)
        route['direction'][0] = -1
        self.assertEqual(s.route_at(62, interval_index=0)['direction'], [1.,0.,0.])

    def test_zero_pcm_rejected_before_tracker(self):
        bounds = [8.]*6
        pairs, corr = diagnostic.floating(np.zeros((1024,4), dtype=np.int32), bounds)
        self.assertTrue(all(not p['valid'] for p in pairs))
        self.assertTrue(np.all(corr == 0))
        p = diagnostic.projection(pairs, np.zeros((4,3)), 48000, 343)
        r = DiagnosticSession().update(22, p, interval_index=0)
        self.assertEqual(r['tracker']['state'], 'SEARCH')

    def test_delay_sign_algebra_no_waveform_simulation(self):
        positions = np.array([[0,0,0],[.04,0,0],[.04,.04,0],[0,.04,0]])
        for az in (-90,0,90,180):
            a = math.radians(az)
            unit = np.array([math.cos(a),math.sin(a),0])
            pairs = [dict(valid=True, tau_samples=float((positions[j]-positions[i])@unit*48000/343))
                     for i,j in diagnostic.PAIRS]
            p = diagnostic.projection(pairs, positions, 48000, 343)
            v, _ = horizontal_candidate(p)
            np.testing.assert_allclose(v, unit, atol=1e-15)
            self.assertFalse(p['direction_accepted'])


class RealInputContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        here = Path(__file__).resolve().parent
        cls.config = json.loads((here/'config.json').read_text(encoding='utf-8'))
        cls.rec = ReaderSession().load(here.parents[3]/cls.config['recordings'][0]['directory'])

    def test_actual_frames_and_ready_time(self):
        frames, summary = replay(self.rec, self.config)
        self.assertEqual(len(frames), 61)
        self.assertEqual(summary['framing']['unused_clean_rows'], 256)
        for f in frames:
            end = (int(f['last_sample_id'])-int(self.rec.sample_ids[0])+1)/48
            self.assertAlmostEqual(f['frame_ready_ms'], end, places=10)
            self.assertGreater(f['frame_ready_ms'], f['frame_start_ms'])
            self.assertFalse(f['direction_accepted'])

    def test_gap_and_large_ids_on_copy_of_real_pcm(self):
        rec = copy.deepcopy(self.rec)
        rec.sample_ids = np.arange(len(rec.samples), dtype=np.uint64)+np.uint64(2**63+17)
        rec.clean_intervals = (dict(row_start=0,row_stop=4096), dict(row_start=5120,row_stop=12000),
                               dict(row_start=31900,row_stop=32000))
        frames, summary = replay(rec, self.config)
        self.assertEqual(frames[0]['first_sample_id'], str(2**63+17))
        for f in frames:
            self.assertFalse(f['row_start'] < 5120 and f['row_stop'] > 4096)
            if f['reset_before']:
                self.assertNotIn(f['tracker']['state'], ('LOCKED','HOLD'))
        self.assertEqual(summary['framing']['intervals'][-1]['frames'], 0)

    def test_non_acoustic_input_rejected(self):
        rec = copy.deepcopy(self.rec)
        rec.metadata['source_kind'] = 'hardware-test-pattern'
        with self.assertRaisesRegex(ValueError, 'DIRECTION_FORBIDDEN'):
            replay(rec, self.config)


if __name__ == '__main__':
    unittest.main()
