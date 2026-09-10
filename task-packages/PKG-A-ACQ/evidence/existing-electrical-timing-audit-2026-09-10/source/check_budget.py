"""Reproduce nominal DC/phase checks. This is not HDL simulation or board STA."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import unittest


def margins(vdd=3.3, vcco=3.3):
    # DS187 v1.21 Table 10 (PL, not PS MIO); IM73D122V01 v1.00 Tables 5/6.
    # Mic Table 6 test conditions remain an applicability limitation.
    return {
        "clock_high_v": vcco - 0.4 - 0.65 * vdd,
        "clock_low_v": 0.35 * vdd - 0.4,
        "data_high_v": 0.7 * vdd - 2.0,
        "data_low_v": 0.8 - 0.3 * vdd,
    }


def phase_trace(cycles=160):
    """Track sample identity using old-state/nonblocking update semantics."""
    phase, clock, meta, sync = 0, 0, None, None
    last_fall = None
    consumed = []
    for tick in range(cycles):
        if phase == 9 and last_fall is not None:
            consumed.append({"consume_tick": tick, "pin_sample_tick": sync,
                             "fall_tick": last_fall,
                             "sample_after_fall_cycles": sync - last_fall,
                             "sample_before_rise_cycles": tick - sync})
        meta, sync = tick, meta
        if phase == 19:
            phase, clock, last_fall = 0, 0, tick
        else:
            if phase == 9:
                clock = 1
            phase += 1
    return consumed


def evaluate(extra_setup_ns=None, hold_budget_ns=None, mic_timing_applicable=False):
    # extra_setup_ns must bound FPGA output+input, both board legs, setup,
    # clock skew/uncertainty; it is not a cable-only delay.
    for value in (extra_setup_ns, hold_budget_ns):
        if value is not None and (not math.isfinite(value) or value < 0):
            raise ValueError("Budgets must be finite and nonnegative")
    period = 1e9 / 61_440_000
    nominal = 8 * period - 100
    return {
        "model": "nominal-analysis-not-hardware-acceptance",
        "pl_period_ns": period,
        "pdm_frequency_hz": 61_440_000 / 20,
        "nominal_duty_percent": 50,
        "pin_sample_after_fall_ns": 8 * period,
        "pin_sample_before_rise_ns": 2 * period,
        "mic_tdv_reference_ns": 100,
        "residual_before_fpga_board_setup_skew_ns": nominal,
        "dc_margins_at_nominal_3v3_v": margins(),
        "dc_envelope": "NOT_PROVEN_NEGATIVE_DATA_LOW_MARGIN",
        "phase_trace": phase_trace(),
        "extra_setup_ns": extra_setup_ns,
        "hold_budget_ns": hold_budget_ns,
        "mic_timing_condition_confirmed": mic_timing_applicable,
        "conditional_setup_margin_ns": None if extra_setup_ns is None else nominal - extra_setup_ns,
        # Never emit hardware PASS just because this arithmetic runs successfully.
        "external_interface_acceptance": "NOT_CLOSED",
        "missing": ["DC output guarantee applicable to actual module/load/VDD",
                    "actual supply and wiring evidence",
                    "bounded max/min external path and edge/phase constraints",
                    "clock slew/duty at microphone under actual load",
                    "loaded artifact identity"],
    }


class BudgetTests(unittest.TestCase):
    def test_phase(self):
        trace = phase_trace()
        self.assertEqual(len(trace), 7)
        self.assertTrue(all(x["sample_after_fall_cycles"] == 8 for x in trace))
        self.assertTrue(all(x["sample_before_rise_cycles"] == 2 for x in trace))

    def test_nominal_dc(self):
        for key, expected in zip(margins(), (0.755, 0.755, 0.31, -0.19)):
            self.assertAlmostEqual(margins()[key], expected)

    def test_no_voltage_only_fix_for_lvcmos33(self):
        self.assertGreater(2.0 / 0.7, 0.8 / 0.3)

    def test_budget(self):
        self.assertAlmostEqual(evaluate()["residual_before_fpga_board_setup_skew_ns"], 30.2083333333)

    def test_unknown_not_pass(self):
        self.assertEqual(evaluate()["external_interface_acceptance"], "NOT_CLOSED")
        self.assertIsNone(evaluate()["conditional_setup_margin_ns"])

    def test_optimistic_arithmetic_not_acceptance(self):
        result = evaluate(0, 0, True)
        self.assertGreater(result["conditional_setup_margin_ns"], 0)
        self.assertEqual(result["external_interface_acceptance"], "NOT_CLOSED")

    def test_excess_delay(self):
        self.assertLess(evaluate(31)["conditional_setup_margin_ns"], 0)

    def test_invalid(self):
        for bad in (-1, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                evaluate(bad)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.out.exists():
        raise SystemExit("Refusing to overwrite previous evidence")
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(BudgetTests))
    if not result.wasSuccessful():
        raise SystemExit(1)
    data = evaluate()
    data["self_tests"] = {"run": result.testsRun, "passed": result.testsRun}
    data["script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Arithmetic/phase model PASS; external hardware NOT_CLOSED")


if __name__ == "__main__":
    main()
