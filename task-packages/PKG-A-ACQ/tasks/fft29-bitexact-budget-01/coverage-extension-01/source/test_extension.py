"""Reuse the nine approved comparator tests; add four bounded extension checks."""
import argparse
import importlib.util
import io
from pathlib import Path
import sys
import unittest

EXT = Path(__file__).resolve().parent.parent
TASK = EXT.parent
sys.path.insert(0, str(TASK / "source"))
import test_checker as shared_tests

spec = importlib.util.spec_from_file_location("extension_checker", EXT / "source/check.py")
extended = importlib.util.module_from_spec(spec)
spec.loader.exec_module(extended)
shared_tests.compare = extended.compare


class ExtensionTests(unittest.TestCase):
    def test_tb_only_capacity_count_timeout_changed(self):
        old = (TASK / "source/tb_fft29.sv").read_text()
        wanted = old.replace("mem [0:369663]; // 361 jobs * 1024, predeclared 60 cases + repeat.",
                             "mem [0:836607]; // 817 jobs * 1024: remaining 136 cases + first-job repeat.")
        wanted = wanted.replace("cycle>6000000", "cycle>12000000").replace("njobs!=361", "njobs!=817")
        self.assertEqual(wanted, (EXT / "source/tb_fft29.sv").read_text())

    def test_checker_only_pass_count_changed(self):
        old = (TASK / "source/check.py").read_text()
        wanted = old.replace("PASS FFT29 archive replay: 361 jobs;", "PASS FFT29 archive replay: 817 jobs;")
        self.assertEqual(wanted, (EXT / "source/check.py").read_text())

    def test_ip_configuration_reused_without_synthesis(self):
        original = (TASK / "source/build.tcl").read_text()
        block = original[original.index("create_ip -name xfft"):original.index("set f [open")]
        actual = (EXT / "source/create_sim.tcl").read_text()
        dedented = "\n".join(line[4:] if line.startswith("    ") else line for line in actual.splitlines())
        self.assertIn(block.rstrip(), dedented)
        for command in ("launch_runs", "synth_design", "place_design", "route_design", "write_bitstream"):
            self.assertNotRegex(actual, r"(?m)^\s*" + command + r"\b")

    def test_817_jobs_fit_memory_and_timeout(self):
        self.assertEqual(136 * 6 + 1, 817)
        self.assertEqual(817 * 1024 - 1, 836607)
        self.assertLess(817 * 7366 + 10000, 12000000)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    if args.log and args.log.exists():
        raise SystemExit("Refusing to overwrite test log")
    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(shared_tests),
                                unittest.defaultTestLoader.loadTestsFromTestCase(ExtensionTests)])
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    output = stream.getvalue()
    print(output, end="")
    if args.log:
        args.log.parent.mkdir(parents=True, exist_ok=True)
        with args.log.open("x", encoding="utf-8", newline="\n") as f:
            f.write(output)
    raise SystemExit(0 if result.wasSuccessful() else 1)


if __name__ == "__main__":
    main()
