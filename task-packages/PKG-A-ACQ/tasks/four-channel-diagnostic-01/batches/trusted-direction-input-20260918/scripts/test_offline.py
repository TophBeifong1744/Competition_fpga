"""Synthetic tool checks and a read-only OLD S1 regression, not new board evidence."""
import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
from prepare import HERE, PREVIOUS, load_module
from process_capture import align, marker_peak, read_wav, PLAY, dump

class Offline(unittest.TestCase):
    def setUp(self):
        self.mark=read_wav(PLAY/'marker-start.wav')

    def test_exact_offset(self):
        x=np.zeros(22000);x[4567:4567+len(self.mark)]=self.mark
        hit=marker_peak(x,self.mark)
        self.assertEqual(hit['index'],4567);self.assertGreater(hit['absolute_correlation'],0.999)

    def test_polarity_gain_dc(self):
        x=np.full(22000,300.);x[3000:3000+len(self.mark)]-=self.mark*2
        hit=marker_peak(x,self.mark)
        self.assertEqual(hit['index'],3000);self.assertGreater(hit['absolute_correlation'],0.999)

    def test_silence_unresolved(self):
        r=align(np.zeros((288000,4)))
        self.assertTrue(all(v['status']=='UNRESOLVED' for v in r['channels']))

    def test_noisy_playback_fits(self):
        x=np.random.default_rng(178).normal(0,50,(288250,4))
        source=read_wav(PLAY/'soundsight-target-v1.wav')
        for c in range(4):x[24000+c:24000+c+len(source),c]+=source*(c+1)
        r=align(x)
        for c,v in enumerate(r['channels']):
            self.assertEqual(v['start_marker']['index'],33600+c)
            self.assertEqual(v['end_marker']['index'],237600+c)
            self.assertTrue(v['source_file_fits_capture'])
            self.assertEqual(v['status'],'CANDIDATE_ALIGNMENT_REVIEW_REQUIRED')
        self.assertFalse(r['exact_activity_labels']);self.assertIsNone(r['activity_uncertainty_seconds'])

    def test_missing_tail_unresolved(self):
        x=np.zeros((288000,4));x[20000:20000+len(self.mark),:]=self.mark[:,None]
        self.assertTrue(all(v['status']=='UNRESOLVED' for v in align(x)['channels']))

    def test_ambiguous_duplicate(self):
        x=np.zeros(40000)
        for at in (1000,21000):x[at:at+len(self.mark)]=self.mark
        hit=marker_peak(x,self.mark)
        self.assertGreater(hit['runner_up_outside_marker_width'],0.999)

    def test_short_signal_rejected(self):
        with self.assertRaisesRegex(ValueError,'shorter'):marker_peak(np.zeros(20),self.mark)

    def test_source_length_and_silence(self):
        pcm=read_wav(PLAY/'soundsight-target-v1.wav');self.assertEqual(len(pcm),230400)
        timeline=json.loads((PLAY/'timeline.json').read_text(encoding='utf-8'))
        self.assertTrue(np.all(pcm[16800:48000]==0))
        self.assertTrue(np.all(pcm[timeline['speech_source_interval'][1]:213600]==0))
        self.assertLess(np.abs(pcm).max(),32767)

    def test_existing_bin_destination_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'already.bin';p.touch()
            with self.assertRaisesRegex(ValueError,'already exists'):dump(Path('unused.log'),p)

    def test_old_capture_regression_not_new_acquisition(self):
        old=load_module('existing_scene_test',PREVIOUS/'finish_scene.py')
        fixture=PREVIOUS/'delivery-01/c-scene-20260917-01'
        raw=(fixture/'raw.bin').read_bytes();log=(fixture/'serial.log').read_text(encoding='utf-8-sig')
        got=old.verify(raw,log)
        self.assertEqual((got['groups'],got['fnv1a32']),(288250,'9494D645'))
        with self.assertRaisesRegex(ValueError,'PASS count/guard mismatch'):
            old.verify(raw,log.replace('guard_ok=1','guard_ok=0'))
        with self.assertRaisesRegex(ValueError,'Truncated/empty'):
            old.verify(raw[:-1],log)

if __name__=='__main__':unittest.main(verbosity=2)
