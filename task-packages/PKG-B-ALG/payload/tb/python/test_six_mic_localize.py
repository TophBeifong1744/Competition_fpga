import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np

PACKAGE = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(PACKAGE/'payload/model/python'))
import six_mic_baseline_core as core
import six_mic_localize as entry
from audio_frames import adapt_six_mic_baseline, adapt_h1, iter_frames, FrameSpec
from h1_reader import ReaderSession

SNAPSHOT = PACKAGE/'reference/six-mic-baseline/six_mic_acoustic_review.py'


def original_nodes():
    """Read numerical definitions from the independent full source snapshot.

    The old plotting/audio CLI and Pillow import are outside this test oracle.
    """
    tree = ast.parse(SNAPSHOT.read_text(encoding='utf-8'))
    nodes = []
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name == 'das':
            break
        if isinstance(node,(ast.Assign,ast.FunctionDef)):
            nodes.append(node)
    return nodes


def original_namespace():
    namespace = {'np':np}
    exec(compile(ast.Module(body=original_nodes(),type_ignores=[]),str(SNAPSHOT),'exec'),namespace)
    return namespace


def segment(samples):
    return adapt_six_mic_baseline(samples,sample_rate_hz=48000,positions_m=core.POS,
                                  source_id='integration-test',source_sha256=entry.BASELINE_SOURCE_SHA256,
                                  first_sample_id=1536)


class BaselineTests(unittest.TestCase):
    def test_original_snapshot_and_numeric_excerpt_unchanged(self):
        self.assertEqual(hashlib.sha256(SNAPSHOT.read_bytes()).hexdigest(),entry.BASELINE_SOURCE_SHA256)
        old = original_nodes()
        new = [n for n in ast.parse(Path(core.__file__).read_text(encoding='utf-8')).body
               if isinstance(n,(ast.Assign,ast.FunctionDef))]
        self.assertEqual([ast.dump(n) for n in old],[ast.dump(n) for n in new])

    def test_differential_162_frames_all_nine_scenarios(self):
        original = original_namespace()
        count = 0
        for scenario in original['SCENARIOS']:
            for az,el in [(0,0),(35,25),(180,-35)]:
                for repeat in range(3):
                    truth,target,other = original['make_trial'](az,el,repeat,scenario)
                    source = target+other
                    frames = list(iter_frames(segment(source[:,1536:3072])))
                    for frame in frames:
                        with self.subTest(scenario=scenario,az=az,el=el,repeat=repeat,frame=frame.index):
                            direct = source[:,1536+frame.row_start:1536+frame.row_stop]
                            delays = original['gcc'](direct)
                            direction,valid,residual,norm = original['solve'](delays)
                            result = entry.localize_frame(frame,truth)
                            actual = np.array([np.nan if d is None else d for d in result['pair_delays_samples']])
                            np.testing.assert_allclose(actual,delays,rtol=0,atol=1e-12,equal_nan=True)
                            self.assertEqual(result['valid'],valid)
                            for actual_value,expected in [(result['residual_samples'],residual),(result['raw_vector_norm'],norm)]:
                                if np.isfinite(expected): self.assertAlmostEqual(actual_value,expected,places=12)
                                else: self.assertIsNone(actual_value)
                            if valid:
                                np.testing.assert_allclose(result['unit_vector'],direction,rtol=0,atol=1e-12)
                                self.assertEqual(result['rejection_reasons'],[])
                            else:
                                self.assertIsNone(result['unit_vector'])
                                self.assertTrue(result['rejection_reasons'])
                            json.dumps(result,allow_nan=False)
                            count += 1
        self.assertEqual(count,162)

    def test_six_axes_exact_delays_and_angles(self):
        positions = np.array([[-.02,-.02,0],[.02,-.02,0],[.02,.02,0],[-.02,.02,0],
                              [0,0,2**.5*.02],[0,0,-2**.5*.02]])
        for vector,az,el in [([1,0,0],0,0),([-1,0,0],180,0),([0,1,0],90,0),
                             ([0,-1,0],-90,0),([0,0,1],None,90),([0,0,-1],None,-90)]:
            with self.subTest(vector=vector):
                arrival = -positions@np.array(vector)*48000/343
                delays = [arrival[i]-arrival[j] for i in range(6) for j in range(i+1,6)]
                result = entry.solve_delays(delays)
                self.assertTrue(result['valid'])
                np.testing.assert_allclose(result['unit_vector'],vector,rtol=0,atol=1e-12)
                self.assertAlmostEqual(result['elevation_deg'],el,places=10)
                if az is None: self.assertIsNone(result['azimuth_deg'])
                else: self.assertAlmostEqual((result['azimuth_deg']-az+180)%360-180,0,places=10)

    def test_waveform_axes_and_oblique_sign(self):
        original = original_namespace()
        for az,el in [(0,0),(90,0),(180,0),(270,0),(0,90),(0,-90),(35,25)]:
            with self.subTest(az=az,el=el):
                truth = original['unit'](az,el)
                source = original['render'](original['source'](np.random.default_rng(20260907)),truth)
                frame = next(iter_frames(segment(source[:,1536:2560])))
                result = entry.localize_frame(frame,truth)
                self.assertTrue(result['valid'])
                self.assertLess(result['angular_error_deg'],3)

    def test_silence_never_outputs_fallback_direction(self):
        rows,summary = entry.run_segment(segment(np.zeros((6,1536))))
        self.assertEqual(summary['valid_frames'],0)
        self.assertIsNone(summary['p95_error_deg'])
        self.assertIsNone(summary['wrong_rate_valid_frames'])
        for row in rows:
            self.assertIsNone(row['unit_vector'])
            self.assertIsNone(row['azimuth_deg'])
            self.assertIsNone(row['elevation_deg'])
            self.assertEqual(row['finite_pairs'],0)
            self.assertEqual(row['rejection_reasons'],['insufficient_pairs','rank_deficient'])
            self.assertEqual(row['pair_delays_samples'],[None]*15)
        json.dumps(rows,allow_nan=False)

    def test_rejection_reasons_match_original_conditions(self):
        only_four = np.full(15,np.nan); only_four[:4] = 0
        self.assertIn('insufficient_pairs',entry.solve_delays(only_four)['rejection_reasons'])
        planar = np.full(15,np.nan)
        for k,(i,j) in enumerate(core.PAIRS):
            if i<4 and j<4: planar[k] = 0
        self.assertEqual(entry.solve_delays(planar)['rejection_reasons'],['rank_deficient'])
        self.assertEqual(entry.solve_delays(np.zeros(15))['rejection_reasons'],['norm_out_of_range'])
        ideal = -core.B@np.array([1.,0,0])*48000/343
        self.assertEqual(entry.solve_delays(ideal*2)['rejection_reasons'],['norm_out_of_range'])
        q,_ = np.linalg.qr(core.B,mode='complete')
        residual = q[:,3]*4
        self.assertEqual(entry.solve_delays(ideal+residual)['rejection_reasons'],['residual_too_large'])
        self.assertEqual(entry.solve_delays(ideal*2+residual)['rejection_reasons'],
                         ['norm_out_of_range','residual_too_large'])

    def test_traceability_no_mutation_and_reset_passthrough(self):
        data = segment(np.zeros((6,1536)))
        before = data.samples.copy()
        rows,_ = entry.run_segment(data)
        self.assertEqual([r['first_sample_id'] for r in rows],[1536,2048])
        self.assertEqual([r['reset_before'] for r in rows],[True,False])
        self.assertEqual(rows[1]['start_seconds'],512/48000)
        np.testing.assert_array_equal(data.samples,before)

    def test_wrong_profile_is_rejected_even_if_zero_frames(self):
        fixture = PACKAGE/'reference/h1-ss-data-draft-0.3/payload/examples/h1/code-pattern'
        with self.assertRaises(ValueError): entry.run_segment(adapt_h1(ReaderSession().load(fixture)))

    def test_short_input_has_undefined_rates(self):
        rows,summary = entry.run_segment(segment(np.zeros((6,1023))),[1,0,0])
        self.assertEqual(rows,[])
        self.assertIsNone(summary['valid_rate'])
        self.assertIsNone(summary['p95_error_deg'])
        self.assertIsNone(summary['wrong_rate_all_frames'])

    def test_no_truth_has_no_accuracy_claim(self):
        truth,target,other = core.make_trial(35,25,0,'clean')
        rows,summary = entry.run_segment(segment((target+other)[:,1536:3072]))
        self.assertEqual(summary['valid_frames'],2)
        self.assertIsNone(summary['accepted_wrong_over_30deg'])
        self.assertIsNone(summary['p95_error_deg'])
        self.assertTrue(all(r['angular_error_deg'] is None for r in rows))

    def test_metric_denominators_and_strict_wrong_threshold(self):
        rows = [dict(valid=True,angular_error_deg=e,rejection_reasons=[]) for e in [0.,30.,60.]]
        rows += [dict(valid=False,angular_error_deg=None,rejection_reasons=['rank_deficient'])]
        result = entry.summarize_results(rows,truth_available=True)
        self.assertEqual(result['valid_rate'],.75)
        self.assertEqual(result['accepted_wrong_over_30deg'],1)
        self.assertEqual(result['wrong_rate_all_frames'],.25)
        self.assertEqual(result['wrong_rate_valid_frames'],1/3)
        self.assertEqual(result['p50_error_deg'],30)
        self.assertAlmostEqual(result['p95_error_deg'],57)

    def test_invalid_truth_and_delays(self):
        for value in [[True,0,0],[0,0,0],[2,0,0],[float('nan'),0,0],[1,0],'x']:
            with self.subTest(value=value),self.assertRaises(ValueError): entry.truth_vector(value)
        for tau in [np.zeros(14),np.full(15,np.inf)]:
            with self.assertRaises(ValueError): entry.solve_delays(tau)

    def test_numeric_overflow_is_an_error_not_a_valid_direction(self):
        frame = next(iter_frames(segment(np.full((6,1024),1e308))))
        with self.assertRaises(ValueError): entry.localize_frame(frame)


class InputAndCliTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.input = self.root/'input'
        entry.write_demo(self.input,'clean',35.,25.,0)

    def modify(self,**updates):
        path = self.input/'metadata.json'
        meta = json.loads(path.read_text(encoding='utf-8'))
        meta.update(updates)
        entry.write_json(path,meta)

    def cli(self,*arguments):
        return subprocess.run([sys.executable,'-B',str(Path(entry.__file__)),*map(str,arguments)],
                              capture_output=True,text=True)

    def test_input_keeps_crop_amplitude_and_provenance(self):
        data,truth = entry.load_input(self.input)
        np.testing.assert_array_equal(data.samples.T,np.load(self.input/'samples.npy'))
        np.testing.assert_allclose(truth,core.unit(35,25),atol=1e-15)
        self.assertEqual(data.provenance['crop']['start'],1536)
        self.assertEqual(data.provenance['input_file_sha256']['samples.npy'],entry.sha256(self.input/'samples.npy'))

    def test_metadata_rejects_h1_hardware_order_rate_truth_and_crop(self):
        original = (self.input/'metadata.json').read_bytes()
        for updates in [dict(schema_version='ss-data-draft-0.3'),dict(source_kind='hardware-audio'),
                        dict(evidence_level='accepted'),dict(channel_order=['mic1','mic0','mic2','mic3','mic4','mic5']),
                        dict(sample_rate_hz=44100),dict(truth_unit_vector=[0,0,0]),
                        dict(crop=dict(start=0,stop=2,reason='bad')),dict(first_sample_id=True),
                        dict(coordinates_m=None),dict(source_sha256='bad')]:
            (self.input/'metadata.json').write_bytes(original)
            self.modify(**updates)
            with self.subTest(updates=updates),self.assertRaises(ValueError): entry.load_input(self.input)

    def test_duplicate_json_and_nonfinite_rejected(self):
        path = self.input/'metadata.json'
        text = path.read_text(encoding='utf-8')
        for invalid in ['{"schema_version":"x",'+text.lstrip()[1:],text.replace('35.0','NaN')]:
            path.write_text(invalid,encoding='utf-8')
            with self.assertRaises(ValueError): entry.load_input(self.input)

    def test_bad_arrays_rejected_without_pickle(self):
        for array in [np.zeros((4,1536)),np.zeros((1536,6)),np.zeros((6,1536),dtype=int),
                      np.full((6,1536),np.nan),np.array([object()],dtype=object)]:
            np.save(self.input/'samples.npy',array)
            with self.subTest(shape=array.shape),self.assertRaises(ValueError): entry.load_input(self.input)

    def test_absent_truth_allowed(self):
        path = self.input/'metadata.json'
        meta = json.loads(path.read_text(encoding='utf-8')); del meta['truth_unit_vector']
        entry.write_json(path,meta)
        data,truth = entry.load_input(self.input)
        self.assertIsNone(truth)
        self.assertIsNone(entry.run_segment(data,truth)[1]['p95_error_deg'])

    def test_cli_demo_replay_and_strict_json(self):
        demo,replay = self.root/'demo',self.root/'replay'
        result = self.cli('--demo','clean','--out',demo)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['valid_frames'],2)
        result = self.cli('--input',demo/'input','--out',replay)
        self.assertEqual(result.returncode,0,result.stderr)
        for name in ['frames.json','summary.json','run.json']:
            self.assertEqual((demo/name).read_bytes(),(replay/name).read_bytes())
            json.loads((demo/name).read_text(encoding='utf-8'),parse_constant=lambda x:self.fail(x))

    def test_cli_rejects_invalid_input_and_keeps_source(self):
        self.modify(sample_rate_hz=44100)
        before = {p.name:p.read_bytes() for p in self.input.iterdir()}
        result = self.cli('--input',self.input,'--out',self.root/'bad')
        self.assertEqual(result.returncode,2)
        self.assertEqual(json.loads(result.stderr)['status'],'ERROR')
        self.assertFalse((self.root/'bad').exists())
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.input.iterdir()})

    def test_cli_refuses_existing_directory(self):
        before = {p.name:p.read_bytes() for p in self.input.iterdir()}
        result = self.cli('--demo','clean','--out',self.input)
        self.assertEqual(result.returncode,2)
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.input.iterdir()})

    def test_cli_empty_npy_is_structured_error(self):
        (self.input/'samples.npy').write_bytes(b'')
        result = self.cli('--input',self.input,'--out',self.root/'empty')
        self.assertEqual(result.returncode,2)
        self.assertEqual(json.loads(result.stderr)['status'],'ERROR')
        self.assertFalse((self.root/'empty').exists())

    def test_silence_and_bad_demo_parameters(self):
        result = self.cli('--demo','silence','--out',self.root/'silence')
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)['valid_frames'],0)
        result = self.cli('--demo','clean','--az','nan','--out',self.root/'invalid-demo')
        self.assertEqual(result.returncode,2)
        self.assertFalse((self.root/'invalid-demo'/'run.json').exists())


if __name__ == '__main__': unittest.main()
