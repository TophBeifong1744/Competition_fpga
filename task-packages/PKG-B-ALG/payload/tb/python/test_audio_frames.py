import copy
import json
from pathlib import Path
import sys
import subprocess
import tempfile
import unittest

import numpy as np

PACKAGE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PACKAGE/'payload/model/python'))
from h1_reader import ReaderSession, HEADER
from audio_frames import (FrameSpec, adapt_h1, adapt_six_mic_baseline,
                          framing_summary, iter_frames, to_six_mic_baseline)

FIXTURE = PACKAGE/'reference/h1-ss-data-draft-0.3/payload/examples/h1/code-pattern'
# Independent expected geometry; do not read the implementation's constant.
POSITIONS = [[-.02,-.02,0],[.02,-.02,0],[.02,.02,0],[-.02,.02,0],
             [0,0,2**.5*.02],[0,0,-2**.5*.02]]


class FramingTests(unittest.TestCase):
    def recording(self, count, *, errors=(), gaps=(), first=0, acquisition='frame-test'):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        meta = json.loads((FIXTURE/'metadata.json').read_text(encoding='utf-8-sig'))
        meta['acquisition_id'] = acquisition
        (root/'metadata.json').write_text(json.dumps(meta), encoding='utf-8')
        rows = [','.join(HEADER)]
        offset = 0
        for i in range(count):
            if i in gaps: offset += 1
            flag = 'drop' if i in gaps else 'overflow' if i in errors else ''
            rows.append(f'{first+i+offset},{i},{-i},8388607,-8388608,{int(bool(flag))},{flag}')
        (root/'samples.csv').write_text('\n'.join(rows)+'\n', encoding='utf-8')
        return ReaderSession().load(root)

    def six(self, count=1024, **overrides):
        args = dict(sample_rate_hz=48000, positions_m=POSITIONS,
                    source_id='unit-test-pattern; not acoustic performance evidence',
                    source_sha256='0'*64)
        args.update(overrides)
        x = np.arange(6*count, dtype=np.float64).reshape(6,count)
        return adapt_six_mic_baseline(x, **args)

    def test_boundary_counts_and_unused_rows(self):
        for length, expected, unused in [(1,0,1),(1023,0,1023),(1024,1,0),
                                          (1535,1,511),(1536,2,0),(1537,2,1),(2048,3,0)]:
            with self.subTest(length=length):
                segment = adapt_h1(self.recording(length))
                self.assertEqual(len(list(iter_frames(segment))), expected)
                summary = framing_summary(segment)
                self.assertEqual(summary['frames'], expected)
                self.assertEqual(summary['unused_clean_rows'], unused)

    def test_overlap_has_exact_shared_samples(self):
        a,b = list(iter_frames(adapt_h1(self.recording(1536))))
        np.testing.assert_array_equal(a.samples[:,512:], b.samples[:,:512])
        self.assertEqual((a.row_start,a.row_stop,b.row_start,b.row_stop),(0,1024,512,1536))
        self.assertTrue(a.reset_before)
        self.assertFalse(b.reset_before)

    def test_gap_and_error_split_and_reset(self):
        segment = adapt_h1(self.recording(3073, gaps=(1536,)))
        frames = list(iter_frames(segment))
        self.assertEqual([f.row_start for f in frames], [0,512,1537,2049])
        self.assertEqual([f.reset_before for f in frames], [True,False,True,False])
        self.assertEqual([f.interval_index for f in frames], [0,0,1,1])
        self.assertEqual([f.first_sample_id for f in frames], [0,512,1538,2050])
        self.assertTrue(all(not f.row_start <= 1536 < f.row_stop for f in frames))
        report = framing_summary(segment)
        self.assertEqual((report['error_rows'],report['missing_samples'],report['unused_clean_rows']),(1,1,0))

    def test_overflow_without_gap_cuts_interval(self):
        frames = list(iter_frames(adapt_h1(self.recording(2049,errors=(1024,)))))
        self.assertEqual([f.row_start for f in frames],[0,1025])
        self.assertTrue(all(f.reset_before for f in frames))

    def test_first_last_and_consecutive_errors(self):
        segment = adapt_h1(self.recording(1028,errors=(0,1,1026,1027)))
        frames = list(iter_frames(segment))
        self.assertEqual(len(frames),1)
        self.assertEqual((frames[0].row_start,frames[0].row_stop),(2,1026))
        self.assertEqual(framing_summary(segment)['error_rows'],4)

    def test_all_error_rows_no_frames(self):
        segment = adapt_h1(self.recording(4,errors=(0,1,2,3)))
        self.assertEqual(list(iter_frames(segment)),[])
        self.assertEqual(framing_summary(segment)['unused_clean_rows'],0)

    def test_no_stitching_separate_segments(self):
        a = adapt_h1(self.recording(600))
        b = adapt_h1(self.recording(600,first=600))
        self.assertEqual(list(iter_frames(a))+list(iter_frames(b)),[])

    def test_restart_resets_time_and_state(self):
        for first, acquisition in [(2**53+1,'one'),(0,'restart')]:
            frame = next(iter_frames(adapt_h1(self.recording(1024,first=first,acquisition=acquisition))))
            self.assertEqual(frame.start_seconds,0)
            self.assertTrue(frame.reset_before)
            self.assertEqual(frame.first_sample_id,first)

    def test_large_ids_time_subtraction_before_float(self):
        first = 2**64-1536
        frames = list(iter_frames(adapt_h1(self.recording(1536,first=first))))
        self.assertEqual(frames[-1].last_sample_id,2**64-1)
        self.assertEqual(frames[1].first_sample_id,first+512)
        self.assertEqual(frames[1].start_seconds,512/48000)
        self.assertEqual(frames[1].end_seconds_exclusive,1536/48000)

    def test_gap_time_remains_visible(self):
        segment = adapt_h1(self.recording(2049,gaps=(1024,)))
        frame = list(iter_frames(segment))[1]
        self.assertEqual(frame.start_seconds,1026/48000)

    def test_h1_fixed_scale_channel_order_no_window(self):
        recording = self.recording(1024)
        frame = next(iter_frames(adapt_h1(recording)))
        self.assertEqual(frame.samples.shape,(4,1024))
        self.assertEqual(frame.samples.dtype,np.dtype('float64'))
        np.testing.assert_array_equal(frame.samples, recording.samples.T.astype(float)/8388608)
        self.assertEqual(frame.samples[3,0],-1)
        self.assertEqual(frame.samples[2,-1],8388607/8388608)

    def test_input_copy_and_frame_copy(self):
        recording = self.recording(1536)
        segment = adapt_h1(recording)
        saved = segment.samples.copy()
        recording.samples[:] = 42
        recording.metadata['acquisition_id'] = 'changed'
        np.testing.assert_array_equal(saved,segment.samples)
        self.assertNotEqual(recording.metadata['acquisition_id'],segment.metadata['acquisition_id'])
        frames = list(iter_frames(segment))
        self.assertFalse(np.shares_memory(frames[0].samples, segment.samples))
        self.assertFalse(np.shares_memory(frames[0].samples, frames[1].samples))
        with self.assertRaises(ValueError): frames[0].samples[0,0] = 9

    def test_original_short_fixtures_zero_frames(self):
        for name in ['code-pattern','restart']:
            recording = ReaderSession().load(FIXTURE.parent/name)
            segment = adapt_h1(recording)
            self.assertEqual(list(iter_frames(segment)),[])
            self.assertEqual(segment.direction_policy,'forbidden_non_acoustic_input')

    def test_unknown_geometry_policy_preserved(self):
        recording = self.recording(1024)
        recording.metadata['source_kind'] = 'hardware-audio'
        recording.metadata['coordinates_m'] = None
        frame = next(iter_frames(adapt_h1(recording)))
        self.assertEqual(frame.direction_policy,'forbidden_unknown_coordinates')
        with self.assertRaises(ValueError): to_six_mic_baseline(frame)

    def test_invalid_specs(self):
        for length,hop in [(0,1),(1024,0),(1024,1025),(True,1),(1024,1.0),(-1,1)]:
            with self.subTest(length=length,hop=hop),self.assertRaises(ValueError): FrameSpec(length,hop)

    def test_custom_spec(self):
        segment = adapt_h1(self.recording(9))
        frames = list(iter_frames(segment,FrameSpec(4,2)))
        self.assertEqual([f.row_start for f in frames],[0,2,4])
        self.assertEqual(framing_summary(segment,FrameSpec(4,2))['unused_clean_rows'],1)

    def test_six_round_trip_layout_and_amplitude(self):
        x = np.arange(6*1536,dtype=float).reshape(6,1536)/10
        segment = adapt_six_mic_baseline(x,sample_rate_hz=48000,positions_m=POSITIONS,
                                       source_id='axis-pattern',source_sha256='1'*64)
        frames = list(iter_frames(segment))
        np.testing.assert_array_equal(to_six_mic_baseline(frames[0]),x[:,:1024])
        np.testing.assert_array_equal(to_six_mic_baseline(frames[1]),x[:,512:1536])
        x[:] = -7
        self.assertNotEqual(segment.samples[0,0],-7)
        self.assertNotIn('schema_version',segment.metadata)

    def test_six_bad_shape_type_or_values(self):
        for x in [np.zeros((4,1024)),np.zeros((1024,6)),np.zeros((6,0)),
                  np.zeros((6,1024),dtype=int),np.full((6,1024),np.nan),
                  np.full((6,1024),np.inf),np.zeros((6,1024),dtype=complex)]:
            with self.subTest(shape=x.shape,dtype=x.dtype),self.assertRaises(ValueError):
                adapt_six_mic_baseline(x,sample_rate_hz=48000,positions_m=POSITIONS,
                                       source_id='invalid',source_sha256='0'*64)

    def test_six_rejects_wrong_geometry_rate_and_provenance(self):
        swapped = copy.deepcopy(POSITIONS)
        swapped[0],swapped[1] = swapped[1],swapped[0]
        for override in [dict(positions_m=swapped),dict(positions_m=None),
                         dict(sample_rate_hz=44100),dict(sample_rate_hz=True),
                         dict(source_id=''),dict(source_sha256='bad'),
                         dict(first_sample_id=-1),dict(first_sample_id=True),
                         dict(first_sample_id=2**64-1023)]:
            with self.subTest(override=override),self.assertRaises(ValueError): self.six(**override)

    def test_six_uint64_boundary(self):
        frame = next(iter_frames(self.six(first_sample_id=2**64-1024)))
        self.assertEqual(frame.last_sample_id,2**64-1)
        self.assertEqual(frame.end_seconds_exclusive,1024/48000)

    def test_baseline_guard_rejects_wrong_profile_and_length(self):
        frame = next(iter_frames(adapt_h1(self.recording(1024))))
        with self.assertRaises(ValueError): to_six_mic_baseline(frame)
        frame = next(iter_frames(self.six(),FrameSpec(512,256)))
        with self.assertRaises(ValueError): to_six_mic_baseline(frame)

    def test_json_report_strict_and_coverage_accounting(self):
        segment = adapt_h1(self.recording(3074,gaps=(1536,)))
        report = framing_summary(segment)
        encoded = json.dumps(report,allow_nan=False)
        self.assertIn('file_sha256',encoded)
        covered = sum(i['covered_unique_rows'] for i in report['intervals'])
        self.assertEqual(covered+report['unused_clean_rows']+report['error_rows'],report['input_rows'])
        for frame in iter_frames(segment): json.dumps(frame.summary(),allow_nan=False)

    def test_demo_cli_and_retained_input(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)/'demo'
            result = subprocess.run([sys.executable,'-B',str(PACKAGE/'run_framing_demo.py'),
                                     '--out',str(output)],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            report = json.loads((output/'framing.json').read_text(encoding='utf-8'))
            self.assertEqual(report['status'],'PASS_FRAMING_ONLY')
            self.assertEqual([r['row_start'] for r in report['frames']],[0,512,1537,2049])
            self.assertEqual(report['frames'][0]['first_sample_id'],2**53+1)
            segment = adapt_h1(ReaderSession().load(output/'input'))
            self.assertEqual(report['summary'],framing_summary(segment))

    def test_demo_cli_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            marker = output/'existing.txt'
            marker.write_text('keep',encoding='utf-8')
            result = subprocess.run([sys.executable,'-B',str(PACKAGE/'run_framing_demo.py'),
                                     '--out',str(output)],capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
            self.assertEqual(marker.read_text(encoding='utf-8'),'keep')
            self.assertEqual(list(output.iterdir()),[marker])


if __name__ == '__main__': unittest.main()
