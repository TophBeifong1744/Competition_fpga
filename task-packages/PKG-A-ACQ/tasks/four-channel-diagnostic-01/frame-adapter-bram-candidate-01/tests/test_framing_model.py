import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "model"))
from framing_model import Framer, Group, HOP, N, PACKET_GROUPS


def group(i, **kwargs):
    return Group(i, (i % 101 - 50, 1000 + i % 137,
                     -2000 - i % 103, 3000 + i % 89), **kwargs)


def normalized(framer):
    frames = []
    for f in framer.frames:
        frames.append((f.session_id, f.frame_index, f.interval_index,
                       f.reset_before,
                       tuple((x.sample_id, x.pcm, x.flags) for x in f.samples)))
    events = [(e.code, e.session_id, e.sample_id, e.prev_id, e.raw_flags,
               e.source_flags, e.unused_tail, e.interval_index)
              for e in framer.events]
    return frames, events


class FramingModelTests(unittest.TestCase):
    def capture(self, count, base=0):
        f = Framer()
        f.start(77)
        for i in range(base, base + count):
            f.push(group(i))
        f.stop()
        return f

    def test_exact_boundaries_and_no_padding(self):
        for count, frames, tail in [(0, 0, 0), (1023, 0, 1023),
                                    (1024, 1, 0), (1535, 1, 511),
                                    (1536, 2, 0), (2048, 3, 0)]:
            with self.subTest(count=count):
                result = self.capture(count)
                self.assertEqual(len(result.frames), frames)
                self.assertEqual(result.events[-1].unused_tail, tail)

    def test_packet_crossing_channels_ids_clip_and_metadata(self):
        base = 2**53 + 41
        f = Framer()
        f.start(19)
        frame_counts = []
        for packet in range(10):
            for lane in range(PACKET_GROUPS):
                i = base + packet * PACKET_GROUPS + lane
                f.push(group(i, flags=i & 0xF))
            frame_counts.append(len(f.frames))
        f.stop()
        self.assertEqual(frame_counts, [0, 0, 0, 0, 1, 1, 2, 2, 3, 3])
        for k, frame in enumerate(f.frames):
            self.assertEqual((frame.session_id, frame.frame_index,
                              frame.interval_index, frame.reset_before),
                             (19, k, 0, k == 0))
            self.assertEqual((frame.first_id, frame.last_id),
                             (base + k * HOP, base + k * HOP + N - 1))
            for j, sample in enumerate(frame.samples):
                expected = group(base + k * HOP + j,
                                 flags=(base + k * HOP + j) & 0xF)
                self.assertEqual(sample, expected)
        self.assertEqual(f.frames[0].samples[HOP:], f.frames[1].samples[:HOP])

    def test_all_error_classes_recover_without_old_content(self):
        bads = [
            Group(10, (0, 0, 0, 0), integrity_error=True, source_flags=1),
            Group(21, (0, 0, 0, 0), source_flags=4),
            group(33),                         # expected 32: ID gap
            group(44, flags=0x10),
            group(55, reserved=1),
            Group(66, (1 << 23, 0, 0, 0)),
        ]
        f = Framer()
        f.start(8)
        next_id = 0
        for bad in bads:
            for _ in range(10):
                f.push(group(next_id))
                next_id += 1
            f.push(bad)
            next_id = bad.sample_id + 1
        for i in range(10000, 10000 + N):
            f.push(group(i))
        f.stop()
        self.assertEqual([e.code for e in f.events[:-1]],
                         ["upstream", "upstream", "id", "flags", "flags", "range"])
        self.assertEqual(len(f.frames), 1)
        self.assertEqual((f.frames[0].first_id, f.frames[0].last_id),
                         (10000, 11023))
        self.assertEqual(f.frames[0].interval_index, 6)
        self.assertTrue(f.frames[0].reset_before)

    def test_stop_restart_isolation(self):
        f = Framer()
        f.start(1)
        for i in range(N):
            f.push(group(i))
        f.stop()
        f.start(2)
        for i in range(50000, 50000 + N):
            f.push(group(i))
        f.stop()
        self.assertEqual([(x.session_id, x.frame_index, x.first_id, x.last_id)
                          for x in f.frames],
                         [(1, 0, 0, 1023), (2, 0, 50000, 51023)])

    def test_equivalent_to_frozen_original_model(self):
        old_path = ROOT.parent / "frame-adapter-candidate-01" / "model" / "framing_model.py"
        spec = importlib.util.spec_from_file_location("frozen_original_model", old_path)
        old = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = old
        spec.loader.exec_module(old)
        new_f, old_f = Framer(), old.Framer()
        new_f.start(123)
        old_f.start(123)
        for i in range(2500):
            kwargs = {"flags": i & 0xF}
            new_f.push(group(i, **kwargs))
            old_f.push(old.Group(i, group(i).pcm, **kwargs))
        new_f.stop()
        old_f.stop()
        self.assertEqual(normalized(new_f), normalized(old_f))


if __name__ == "__main__":
    unittest.main(verbosity=2)
