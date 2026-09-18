import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / "source"))
from fixed_golden import (FixedTracker, TrackerConfig, causal_audio, control_timeline,
                          das_block, doa_q20, lag_q12,
                          physical_limit_q12, physical_tau_legal_q12,
                          rne_div, rne_shift, saturate, window_pcm)
from check_golden import compare_frozen_chain
from run_golden import deterministic_pcm
from presence import evaluate as presence
from budget import calculate


class ArithmeticTests(unittest.TestCase):
    def test_rne_half_even_positive(self): self.assertEqual(rne_div(5, 2), 2)
    def test_rne_half_odd_positive(self): self.assertEqual(rne_div(7, 2), 4)
    def test_rne_half_even_negative(self): self.assertEqual(rne_div(-5, 2), -2)
    def test_rne_half_odd_negative(self): self.assertEqual(rne_div(-7, 2), -4)
    def test_shift_exact(self): self.assertEqual(rne_shift(32, 4), 2)
    def test_positive_saturation(self): self.assertEqual(saturate(1 << 23, 24), ((1 << 23) - 1, True))
    def test_negative_saturation(self): self.assertEqual(saturate(-(1 << 23) - 1, 24), (-(1 << 23), True))
    def test_signed24_endpoints_window(self):
        x = np.zeros((4, 1024), dtype=np.int64)
        x[0, 512], x[1, 512] = (1 << 23) - 1, -(1 << 23)
        out, overflow = window_pcm(x)
        self.assertEqual(overflow, 0)
        self.assertTrue(np.all(out <= (1 << 23) - 1))
        self.assertTrue(np.all(out >= -(1 << 23)))


class PresenceTests(unittest.TestCase):
    def test_zero_rejected(self): self.assertEqual(presence(np.zeros((1024, 4), dtype=np.int64))["reason"], "LOW_ENERGY")
    def test_low_energy_rejected(self): self.assertFalse(presence(np.full((1024, 4), 2047, dtype=np.int64))["present"])
    def test_three_channels_accept(self):
        x = np.zeros((1024, 4), dtype=np.int64); x[:, :3] = 5000
        self.assertTrue(presence(x)["present"])
    def test_allowed_sector_is_not_presence(self):
        self.assertFalse(presence(np.zeros((1024, 4), dtype=np.int64))["present"])
    def test_error_rejected(self):
        self.assertEqual(presence(np.full((1024, 4), 5000, dtype=np.int64), stream_error=True)["reason"], "STREAM_ERROR")
    def test_clip_rejected(self):
        self.assertEqual(presence(np.full((1024, 4), 5000, dtype=np.int64), clip_flag=True)["reason"], "CLIP_FLAG")


class LagDoaTests(unittest.TestCase):
    def test_lag_positive(self):
        corr = np.zeros(1024, dtype=np.int64); corr[3] = 100; corr[2] = corr[4] = 50
        self.assertEqual(lag_q12(corr, 1)["tau_q12"], 3 << 12)
    def test_lag_negative(self):
        corr = np.zeros(1024, dtype=np.int64); corr[-3] = 100; corr[-2] = corr[-4] = 50
        self.assertEqual(lag_q12(corr, 1)["tau_q12"], -3 << 12)
    def test_range_boundary_reject(self):
        corr = np.zeros(1024, dtype=np.int64); corr[8] = 100
        self.assertFalse(lag_q12(corr, 1)["valid"])
    def test_physical_q12_edge_and_diagonal_boundaries(self):
        for length_sq in (1, 2):
            edge = physical_limit_q12(length_sq)
            self.assertGreater(edge, 0)
            for sign in (-1, 1):
                self.assertTrue(physical_tau_legal_q12(sign * (edge - 1), length_sq))
                self.assertTrue(physical_tau_legal_q12(sign * edge, length_sq))
                self.assertFalse(physical_tau_legal_q12(sign * (edge + 1), length_sq))
    def test_pair_specific_limits_are_different(self):
        self.assertLess(physical_limit_q12(1), physical_limit_q12(2))
    def test_interpolated_edge_and_diagonal_both_signs(self):
        for length_sq, peak, inside_left, outside_left in ((1, 6, 90000, 89000),
                                                            (2, 8, 40000, 20000)):
            for sign in (-1, 1):
                for left, accepted in ((inside_left, True), (outside_left, False)):
                    corr = np.zeros(1024, dtype=np.int64)
                    corr[(sign * peak) % 1024] = 100000
                    corr[(sign * (peak - 1)) % 1024] = left
                    row = lag_q12(corr, length_sq)
                    self.assertEqual(row["valid"], accepted)
                    self.assertEqual(row["physical_limit_q12"], physical_limit_q12(length_sq))
    def test_rank_deficient(self):
        rows = [{"valid": True, "tau_q12": 0} for _ in range(3)]
        geometry = ((1, 0), (2, 0), (3, 0))
        self.assertEqual(doa_q20(rows, geometry)["reason"], "RANK_DEFICIENT")
    def test_invalid_pairs(self):
        rows = [{"valid": i < 2, "tau_q12": 0} for i in range(6)]
        self.assertEqual(doa_q20(rows)["reason"], "INSUFFICIENT_PAIRS")
    def test_positive_x_geometry(self):
        a = round((0.04 * 48000 / 343) * (1 << 12))
        rows = [{"valid": True, "tau_q12": dx * a} for dx, _dy in ((1, 0), (1, 1), (0, 1), (0, 1), (-1, 1), (-1, 0))]
        result = doa_q20(rows)
        self.assertTrue(result["valid"])
        self.assertGreater(result["ux_q20"], 0)
        self.assertLess(abs(result["azimuth_q8_deg"]), 2)


class TrackerAndAudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.controls, cls.dropout = control_timeline(0)
        cls.audio, cls.detail = causal_audio(np.tile(deterministic_pcm(), (1, 16)), cls.controls)

    def test_five_frame_acquisition(self):
        tracker = FixedTracker()
        rows = [tracker.update(1024 + i * 512, 0, True) for i in range(5)]
        self.assertEqual(rows[-1]["state"], "LOCKED")
        self.assertTrue(rows[-1]["fresh_valid"])
    def test_hold_expiry(self):
        tracker = FixedTracker()
        for i in range(5): tracker.update(1024 + i * 512, 0, True)
        result = tracker.update(1024 + 4 * 512 + 9601, None, False)
        self.assertEqual(result["state"], "SEARCH")
    def test_direction_switch_within_step(self):
        tracker = FixedTracker()
        for i in range(5): tracker.update(1024 + i * 512, 0, True)
        result = tracker.update(1024 + 5 * 512, 19 << 8, True)
        self.assertTrue(result["fresh_valid"])
    def test_direction_jump_holds(self):
        tracker = FixedTracker()
        for i in range(5): tracker.update(1024 + i * 512, 0, True)
        result = tracker.update(1024 + 5 * 512, 29 << 8, True)
        self.assertEqual(result["state"], "HOLD")
    def test_dropout_resets(self):
        tracker = FixedTracker()
        tracker.update(1024, 0, True)
        result = tracker.update(1024 + 1441, 0, True)
        self.assertEqual(result["reason"], "gap_reset_acquire")
    def test_das_zero(self):
        output, info = das_block(np.zeros((4, 32), dtype=np.int64), [0, 0, 0, 0])
        self.assertTrue(np.array_equal(output, np.zeros(32, dtype=np.int64)))
        self.assertEqual(info["saturation_count"], 0)
    def test_das_constant(self):
        output, _ = das_block(np.full((4, 32), 4000, dtype=np.int64), [0, 0, 0, 0])
        self.assertTrue(np.array_equal(output, np.full(32, 4000, dtype=np.int64)))
    def test_no_future_direction_backfilled(self):
        self.assertEqual(self.detail["first_fresh_ready_sample"], 3072)
        self.assertEqual(self.detail["first_fresh_available_emit_sample"], 3080)
        self.assertEqual(self.detail["first_nonzero_beam_weight_sample"], 3081)
        np.testing.assert_array_equal(self.audio["automatic"][:3081], self.audio["single"][:3081])
        self.assertTrue(np.all(self.audio["auto_weights_q12"][:3081, 1:] == 0))
        self.assertFalse(np.array_equal(self.audio["manual"], self.audio["automatic"]))
    def test_fresh_switch_has_finite_fade(self):
        selected = [row for row in self.detail["events"] if row["kind"] == "FRESH_SELECT"]
        self.assertEqual([(row["ready_sample"], row["target"]) for row in selected],
                         [(3072, 1), (3584, 2)])
        weights = self.audio["auto_weights_q12"]
        self.assertEqual(int(weights[3592, 2]), 0)
        self.assertGreater(int(weights[3593, 2]), 0)
        self.assertEqual(int(weights[3592].sum()), 4096)
        self.assertLessEqual(int(np.max(np.abs(np.diff(weights.astype(np.int64), axis=0)))), 20)
    def test_hold_expiry_and_discontinuity(self):
        hold = [row for row in self.controls if row["state"] == "HOLD"]
        self.assertGreater(len(hold), 1)
        self.assertTrue(all(row["last_fresh_sample"] == 3584 for row in hold))
        expiry = [row for row in self.detail["events"] if row["kind"] == "EXPIRE_TO_SINGLE"]
        self.assertEqual(expiry[0]["emit_sample"], 13193)
        self.assertEqual(int(self.audio["auto_weights_q12"][13193, 0]), 0)
        self.assertEqual(int(self.audio["auto_weights_q12"][13193 + 480, 0]), 4096)
        self.assertEqual(self.dropout[0]["reason"], "gap_reset_acquire")
        self.assertFalse(self.dropout[0]["fresh_valid"])
        self.assertIsNone(self.dropout[0]["display_angle_q8_deg"])
    def test_manual_auto_identity_guard(self):
        with self.assertRaisesRegex(RuntimeError, "MANUAL_AUTO_IDENTICAL"):
            causal_audio(np.zeros((4, 16384), dtype=np.int64), self.controls)


class FrozenCheckerTests(unittest.TestCase):
    def test_lag_doa_tracker_event_mutations_are_rejected(self):
        root = HERE / "evidence/run04/golden/golden-summary.json"
        frozen = json.loads(root.read_text(encoding="utf-8"))["chain"]
        for field, edit in (("pairs", lambda x: x[0].update(reason="MUTATED")),
                            ("doa", lambda x: x.update(azimuth_q8_deg=123)),
                            ("tracker", lambda x: x[4].update(state="SEARCH")),
                            ("audio_timeline", lambda x: x.update(first_fresh_ready_sample=0))):
            changed = copy.deepcopy(frozen)
            edit(changed[field])
            with self.subTest(field=field), self.assertRaisesRegex(AssertionError, field):
                compare_frozen_chain(frozen, changed)


class ContractBudgetTests(unittest.TestCase):
    def test_config_contract(self):
        config = json.loads((HERE / "config.json").read_text(encoding="utf-8"))
        self.assertEqual((config["channels"], config["sample_rate_hz"]), (4, 48000))
        self.assertEqual(config["channel_order"], ["mic0", "mic1", "mic2", "mic3"])
        self.assertTrue(config["presence_gate"]["frozen_before_label_scoring"])
    def test_budget_is_four_channel(self):
        result = calculate()
        self.assertEqual(result["transforms"]["forward_per_frame"], 4)
        self.assertEqual(result["transforms"]["inverse_max_per_frame"], 6)
        self.assertGreater(result["buffers_bytes"]["listed_total_no_lifetime_reuse"], 0)


if __name__ == "__main__":
    unittest.main()
