"""Log-parser tests only; mutations are not hardware fault-injection tests."""
from pathlib import Path
import unittest
from verify_log import analyze

RAW = (Path(__file__).parent / "endurance_300s_10x10s_20260916_01.log").read_text(encoding="utf-8")


class LogTests(unittest.TestCase):
    def test_actual_log(self):
        result = analyze(RAW)
        self.assertEqual(result["totals"], {"groups": 19202750, "packets": 76811, "bytes_checked": 614488000})
        self.assertEqual(result["clip_flags_total"], 0)

    def test_truncated(self):
        with self.assertRaises(ValueError):
            analyze(RAW[:RAW.index("SUMMARY started=")])

    def test_mutations_rejected(self):
        changes = [
            ("capture_command_us=300000125", "capture_command_us=299999999"),
            ("groups=14400250 packets=57601", "groups=14400251 packets=57601"),
            ("last=0000000000DBFF21", "last=0000000000DBFF22"),
            ("DMA_SR=00001002", "DMA_SR=00005002"),
            ("SOURCE=C100000A", "SOURCE=C100002A"),
            ("owners=0,0", "owners=1,0"),
            ("first_failure=OK", "first_failure=GUARD_ERROR"),
            ("guard_checked_per_verified_packet=1", "guard_checked_per_verified_packet=0"),
            ("TRACE packet=57585 slot=1", "TRACE packet=57585 slot=0"),
            ("START session=1 ", "START session=0 "),
            ("normal_between_session_resets=0", "normal_between_session_resets=1"),
            ("first=0000000000DCD6FC", "first=0000000000004428"),
        ]
        for old, new in changes:
            with self.subTest(mutation=old):
                self.assertIn(old, RAW)
                with self.assertRaises(ValueError):
                    analyze(RAW.replace(old, new, 1))

    def test_duplicate_execution(self):
        with self.assertRaises(ValueError):
            analyze(RAW + RAW)


if __name__ == "__main__":
    unittest.main(verbosity=2)
