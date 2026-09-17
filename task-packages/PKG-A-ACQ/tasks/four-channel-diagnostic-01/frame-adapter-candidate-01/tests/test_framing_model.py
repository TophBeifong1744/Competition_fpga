import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "model"))
from framing_model import Framer, Group, HOP, N, PACKET_GROUPS


def group(i, **kwargs):
    return Group(i, (i % 101 - 50, 1000 + i % 137,
                     -2000 - i % 103, 3000 + i % 89), **kwargs)


class FramingModelTests(unittest.TestCase):
    def capture(self, count, base=0):
        f = Framer()
        f.start(77)
        for i in range(base, base + count):
            f.push(group(i))
        f.stop()
        return f

    def test_lengths_and_unpadded_tail(self):
        for count, expected_frames, tail in [(0, 0, 0), (1023, 0, 1023),
                                             (1024, 1, 0), (1535, 1, 511),
                                             (1536, 2, 0), (2048, 3, 0)]:
            with self.subTest(count=count):
                f = self.capture(count)
                self.assertEqual(len(f.frames), expected_frames)
                self.assertEqual(f.events[-1].unused_tail, tail)

    def test_packet_boundary_and_exact_channels(self):
        base = 2**53 + 19
        f = Framer()
        f.start(77)
        # Feed ten real 250-group packet-sized chunks, without resetting the framer.
        per_packet_frames = []
        for packet in range(10):
            for lane in range(PACKET_GROUPS):
                f.push(group(base + packet * PACKET_GROUPS + lane))
            per_packet_frames.append(len(f.frames))
        f.stop()
        self.assertEqual(per_packet_frames, [0, 0, 0, 0, 1, 1, 2, 2, 3, 3])
        self.assertEqual(len(f.frames), 3)
        for k, frame in enumerate(f.frames):
            self.assertEqual((frame.first_id, frame.last_id),
                             (base + k * HOP, base + k * HOP + N - 1))
            self.assertEqual(len(frame.samples), N)
            for j, sample in enumerate(frame.samples):
                self.assertEqual(sample, group(base + k * HOP + j))
            self.assertTrue((k * HOP) // PACKET_GROUPS !=
                            (k * HOP + N - 1) // PACKET_GROUPS)
        self.assertEqual(f.frames[0].samples[HOP:], f.frames[1].samples[:HOP])

    def test_clip_preserved_not_reclassified(self):
        f = Framer()
        f.start(1)
        for i in range(N):
            f.push(group(i, flags=(i % 16)))
        f.stop()
        self.assertEqual(f.frames[0].samples[13].flags, 13)
        self.assertEqual([e.code for e in f.events], ["stop"])

    def test_bad_id_discards_partial_interval(self):
        f = Framer()
        f.start(2)
        for i in range(700):
            f.push(group(i))
        f.push(group(702))
        for i in range(703, 1727):
            f.push(group(i))
        f.stop()
        self.assertEqual(f.events[0].code, "id")
        self.assertEqual(f.events[0].unused_tail, 700)
        self.assertEqual(len(f.frames), 1)
        self.assertEqual(f.frames[0].first_id, 703)
        self.assertEqual(f.frames[0].interval_index, 1)
        self.assertTrue(f.frames[0].reset_before)

    def test_error_codes_and_recovery(self):
        for issue, bad, want in [
            ("upstream", Group(20, (0, 0, 0, 0), integrity_error=True, source_flags=9), "upstream"),
            ("source_flags_only", Group(20, (0, 0, 0, 0), source_flags=4), "upstream"),
            ("flags", group(20, flags=0x10), "flags"),
            ("reserved", group(20, reserved=1), "flags"),
            ("range", Group(20, (1 << 23, 0, 0, 0)), "range"),
        ]:
            with self.subTest(issue=issue):
                f = Framer()
                f.start(3)
                for i in range(20):
                    f.push(group(i))
                f.push(bad)
                for i in range(21, 21 + N):
                    f.push(group(i))
                f.stop()
                self.assertEqual(f.events[0].code, want)
                self.assertEqual(f.events[0].unused_tail, 20)
                self.assertEqual(f.frames[0].first_id, 21)
                self.assertTrue(f.frames[0].reset_before)

    def test_restart_is_new_session_without_splice(self):
        f = Framer()
        f.start(1)
        for i in range(1200):
            f.push(group(i))
        f.stop()
        f.start(2)
        for i in range(N):
            f.push(group(i))
        f.stop()
        self.assertEqual([(x.session_id, x.frame_index, x.first_id, x.reset_before)
                          for x in f.frames], [(1, 0, 0, True), (2, 0, 0, True)])
        self.assertEqual([e.unused_tail for e in f.events], [176, 0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
