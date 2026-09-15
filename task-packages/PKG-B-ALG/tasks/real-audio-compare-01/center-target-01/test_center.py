"""New entry gain bounds and preservation guards; no acoustic simulation."""
import unittest
import render_center as center

class CenterTests(unittest.TestCase):
    def test_gain_headroom_and_no_zero_division(self):
        self.assertEqual(center.preview_gain(0),1.)
        for peak in [1e-9,.003,.007843017578125,.5,1.,2.]:
            gain=center.preview_gain(peak)
            self.assertGreater(gain,0)
            self.assertLessEqual(gain,128)
            self.assertLessEqual(peak*gain,.5)
        self.assertEqual(center.preview_gain(.007843017578125),32.)

    def test_gain_invalid_input(self):
        for value in [-1,float('nan'),float('inf')]:
            with self.assertRaises(ValueError): center.preview_gain(value)

    def test_existing_audio_not_overwritten(self):
        out=center.HERE/'evidence/audio-run01'
        before={p.name:center.base.sha(p) for p in out.iterdir() if p.is_file()}
        self.assertEqual(len(before),5)
        with self.assertRaises(ValueError): center.run(out)
        after={p.name:center.base.sha(p) for p in out.iterdir() if p.is_file()}
        self.assertEqual(before,after)

    def test_output_outside_revision_rejected(self):
        with self.assertRaises(ValueError): center.run(center.base.ROOT/'rejected-center-audio-output')

if __name__=='__main__': unittest.main(verbosity=2)
