import csv
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import numpy as np
import diagnose as d

FIXTURES=d.HERE.parents[1]/'reference/h1-ss-data-draft-0.3/payload/examples/h1'

class Diagnostics(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.input=self.root/'input'
        shutil.copytree(FIXTURES/'restart',self.input)
        self.meta=json.loads((self.input/'metadata.json').read_text(encoding='utf-8-sig'))

    def write(self, rows, **meta):
        self.meta.update(meta)
        (self.input/'metadata.json').write_text(json.dumps(self.meta),encoding='utf-8')
        with (self.input/'samples.csv').open('w',newline='') as f:
            writer=csv.writer(f);writer.writerow(d.reader.HEADER);writer.writerows(rows)

    def run_input(self, **kwargs):
        return d.run([self.input],self.root/'output',**kwargs)['segments'][0]

    def test_gap_flags_and_uint64_precision(self):
        self.input=self.root/'code';shutil.copytree(FIXTURES/'code-pattern',self.input)
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.input.iterdir()}
        r=self.run_input()
        self.assertEqual(r['first_sample_id'],'9007199254740992')
        self.assertEqual(r['missing_intervals'][0]['first'],'9007199254740994')
        self.assertEqual([e['csv_line'] for e in r['flagged_rows']],[4,6])
        self.assertEqual([i['row_stop']-i['row_start'] for i in r['clean_intervals']],[2,1,1])
        self.assertEqual(len(r['amplitude_format_clean_rows']),4)
        self.assertEqual(before,{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in self.input.iterdir()})

    def test_uint64_maximum_is_string(self):
        self.write([[2**64-2,1,2,3,4,0,''],[2**64-1,1,2,3,4,0,'']])
        self.assertEqual(self.run_input()['last_sample_id'],str(2**64-1))

    def test_amplitude_rms_does_not_overflow_int32(self):
        self.write([[0,-2**23,3,0,1,0,''],[1,2**23-1,4,0,-1,0,'']])
        a=self.run_input()['amplitude_all_rows']
        self.assertAlmostEqual(a[0]['rms_pcm'],np.sqrt(((2**23)**2+(2**23-1)**2)/2))
        self.assertEqual(a[0]['full_scale_code_count'],2)
        self.assertAlmostEqual(a[1]['rms_pcm'],np.sqrt(12.5))
        self.assertEqual(a[2]['ac_rms_pcm'],0)

    def test_all_error_rows_retained_but_not_used_for_pairs(self):
        self.write([[n,1,2,3,4,1,'overflow'] for n in range(40)])
        r=self.run_input()
        self.assertEqual(len(r['flagged_rows']),40)
        self.assertEqual(r['amplitude_format_clean_rows'],[])
        self.assertEqual(r['pair_intervals'],[])

    def test_similar_and_inverted_hints(self):
        self.write([[n,n,n,-n,3*n+7,0,''] for n in range(64)])
        r=self.run_input()
        self.assertTrue(r['pair_intervals'][0]['exact_equal'])
        self.assertTrue(r['pair_intervals'][1]['exact_inverted'])
        self.assertAlmostEqual(r['pair_intervals'][2]['pearson'],1)
        self.assertFalse(r['h2_acceptance'])
        self.assertIn('NOT_REAL_AUDIO_RECEIPT',[x['code'] for x in r['observations']])

    def test_correlation_never_bridges_error_boundary(self):
        self.write([[n,n,n,n,n,int(n==20),'relock' if n==20 else ''] for n in range(41)])
        r=self.run_input()
        self.assertEqual(r['pair_intervals'],[])
        self.assertEqual(r['relock_flag_rows'],1)
        self.assertFalse(r['reset_events_verified'])

    def test_unknown_geometry_still_diagnosable(self):
        self.write([[0,1,2,3,4,0,'']],coordinates_m=None,
                   provisional_fields={'coordinates_m':'unmeasured'},source_kind='hardware-audio',evidence_level='diagnostic')
        r=self.run_input()
        self.assertEqual(r['direction_policy'],'forbidden_unknown_coordinates')
        self.assertFalse(r['acceptance_verified'])

    def test_restart_keeps_separate_segments(self):
        code=self.root/'code';shutil.copytree(FIXTURES/'code-pattern',code)
        r=d.run([code,self.input],self.root/'output')
        self.assertEqual(r['readable'],2)
        self.assertTrue(r['segments'][1]['acquisition_change_from_previous_readable'])
        self.assertEqual(r['segments'][1]['first_sample_id'],'0')

    def test_config_conflict_is_reported(self):
        another=self.root/'another';shutil.copytree(self.input,another)
        meta=json.loads((another/'metadata.json').read_text(encoding='utf-8-sig'))
        meta['sample_rate_hz']=44100
        (another/'metadata.json').write_text(json.dumps(meta))
        r=d.run([self.input,another],self.root/'output')
        self.assertEqual(r['rejected'],1)
        self.assertEqual(r['segments'][1]['error']['code'],'config_conflict')

    def test_invalid_record_does_not_stop_other_directories(self):
        self.write([[0,2**23,2,3,4,0,'']])
        r=d.run([self.input,FIXTURES/'restart'],self.root/'output')
        self.assertEqual((r['readable'],r['rejected']),(1,1))
        self.assertEqual(r['segments'][0]['error']['csv_line'],2)
        self.assertEqual(r['segments'][0]['error']['code'],'integer_range')

    def test_silent_gap_rejected_without_salvage(self):
        self.write([[0,1,2,3,4,0,''],[2,1,2,3,4,0,'']])
        r=self.run_input()
        self.assertEqual(r['error']['code'],'silent_gap')
        self.assertNotIn('amplitude_all_rows',r)

    def test_duplicate_id_rejected(self):
        self.write([[1,1,2,3,4,0,''],[1,1,2,3,4,0,'']])
        self.assertEqual(self.run_input()['error']['code'],'id_order')

    def test_mono_schema_rejected(self):
        self.write([[0,1,2,3,4,0,'']],schema_version='ss-mono-diagnostic-0.2')
        self.assertEqual(self.run_input()['error']['code'],'unsupported_schema')

    def test_source_output_and_existing_output_protected(self):
        with self.assertRaises(ValueError):d.run([self.input],self.input/'output')
        self.run_input()
        before=(self.root/'output/summary.json').read_bytes()
        with self.assertRaises(FileExistsError):self.run_input()
        self.assertEqual(before,(self.root/'output/summary.json').read_bytes())

    def test_cli_outputs_and_exit_codes(self):
        cmd=[sys.executable,'-B',str(d.HERE/'diagnose.py'),str(self.input),'--out',str(self.root/'cli')]
        r=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertTrue((self.root/'cli/receipt.md').is_file())
        self.write([[0,1,2,3,4,0,'bad']])
        cmd[-1]=str(self.root/'bad')
        r=subprocess.run(cmd,capture_output=True,text=True)
        self.assertEqual(r.returncode,2)
        errors=json.loads((self.root/'bad/errors.json').read_text(encoding='utf-8'))
        self.assertEqual(errors[0]['code'],'error_inconsistency')

if __name__=='__main__':unittest.main(verbosity=2)
