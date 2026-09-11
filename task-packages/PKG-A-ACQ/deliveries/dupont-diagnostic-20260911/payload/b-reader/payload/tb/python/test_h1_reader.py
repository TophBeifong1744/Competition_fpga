import copy
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import numpy as np

PACKAGE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PACKAGE/'payload/model/python'))
from h1_reader import ReaderSession, DataError
FIXTURES = PACKAGE/'reference/h1-ss-data-draft-0.3/payload/examples/h1'


class FixtureCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ['code-pattern', 'restart']:
            shutil.copytree(FIXTURES/name, self.root/name)
        self.path = self.root/'code-pattern'

    def metadata(self, **changes):
        path = self.path/'metadata.json'
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        data.update(changes)
        path.write_text(json.dumps(data), encoding='utf-8')

    def row(self, index, column, value):
        path = self.path/'samples.csv'
        lines = path.read_text(encoding='utf-8-sig').splitlines()
        cells = lines[index].split(','); cells[column] = value
        lines[index] = ','.join(cells)
        path.write_text('\n'.join(lines)+'\n', encoding='utf-8')

    def load(self): return ReaderSession().load(self.path)

    def reject(self, code, field=None, line=None):
        before = {p.name: p.read_bytes() for p in self.path.iterdir()}
        with self.assertRaises(DataError) as context: self.load()
        self.assertEqual(context.exception.code, code)
        if field is not None: self.assertEqual(context.exception.field, field)
        if line is not None: self.assertEqual(context.exception.line, line)
        self.assertEqual(before, {p.name: p.read_bytes() for p in self.path.iterdir()})


class H1Required(FixtureCase):
    def test_exact_uint64(self):
        data = self.load()
        self.assertEqual(data.sample_ids.dtype, np.dtype('uint64'))
        self.assertEqual([int(v) for v in data.sample_ids[:2]], [9007199254740992,9007199254740993])

    def test_pcm_boundaries(self):
        data = self.load()
        self.assertEqual(data.samples.dtype, np.dtype('int32'))
        self.assertEqual(data.samples[1].tolist(), [8388607,-8388608,123,-456])

    def test_gap(self):
        data = self.load()
        self.assertEqual(data.missing_intervals, ({'first':9007199254740994,'last':9007199254740994,'count':1},))
        self.assertEqual(data.error_flags[2], ('drop','overflow'))
        self.assertEqual([(r['row_start'],r['row_stop']) for r in data.clean_intervals], [(0,2),(3,4),(5,6)])
        self.assertEqual(len(data.samples), 6)

    def test_restart(self):
        session = ReaderSession()
        a = session.load(self.path); b = session.load(self.root/'restart')
        self.assertNotEqual(a.metadata['acquisition_id'],b.metadata['acquisition_id'])
        self.assertEqual(b.sample_ids.tolist(),[0,1]); self.assertEqual(len(a.samples),6)

    def test_unknown_schema(self):
        self.metadata(schema_version='unsupported-99'); self.reject('unsupported_schema','schema_version')

    def test_swapped_header(self):
        self.row(0,1,'mic1'); self.row(0,2,'mic0'); self.reject('header','header',1)

    def test_duplicate_channel(self):
        self.metadata(channel_order=['mic0','mic0','mic2','mic3']); self.reject('channel_order','channel_order')

    def test_pcm_overflow(self):
        self.row(1,1,'8388608'); self.reject('integer_range','mic0',2)

    def test_duplicate_id(self):
        self.row(2,0,'9007199254740992'); self.reject('id_order','sample_id',3)

    def test_silent_gap(self):
        self.row(3,5,'0'); self.row(3,6,''); self.reject('silent_gap','error_flags',4)

    def test_error_inconsistency(self):
        self.row(1,6,'overflow'); self.reject('error_inconsistency','error_flags',2)

    def test_unknown_coordinates(self):
        self.metadata(coordinates_m=None,provisional_fields={'coordinates_m':'not measured'},source_kind='hardware-audio',evidence_level='diagnostic')
        data = self.load(); self.assertEqual(data.direction_policy(),'forbidden_unknown_coordinates')
        self.assertEqual(data.summary()['amplitude_all_rows']['minimum'][1],-8388608)

    def test_unknown_error_token(self):
        self.row(5,6,'mystery'); self.reject('unsupported_flags','error_flags',6)

    def test_uint64_overflow(self):
        self.path = self.root/'restart'; self.row(1,0,'18446744073709551616')
        self.reject('integer_range','sample_id',2)

    def test_uint64_maximum(self):
        self.path = self.root/'restart'
        self.row(1,0,'18446744073709551614'); self.row(2,0,'18446744073709551615')
        self.assertEqual(self.load().sample_ids.tolist(),[18446744073709551614,18446744073709551615])


class ReaderBoundaries(FixtureCase):
    def test_cli_reads_both_segments(self):
        result=subprocess.run([sys.executable,'-B',str(PACKAGE/'payload/model/python/h1_reader.py'),
                               str(self.path),str(self.root/'restart')],capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(result.returncode,0,result.stderr)
        report=json.loads(result.stdout)
        self.assertEqual(report['status'],'PASS_FORMAT_ONLY')
        self.assertEqual([r['samples'] for r in report['segments']],[6,2])

    def test_cli_failure_is_structured_and_nonzero(self):
        self.row(1,1,'8388608')
        result=subprocess.run([sys.executable,'-B',str(PACKAGE/'payload/model/python/h1_reader.py'),str(self.path)],
                              capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(result.returncode,2);self.assertEqual(result.stdout,'')
        report=json.loads(result.stderr);self.assertEqual(report['csv_line'],2);self.assertEqual(report['field'],'mic0')

    def test_bom_and_crlf(self):
        for p in self.path.iterdir():
            p.write_bytes(b'\xef\xbb\xbf'+p.read_bytes().replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))
        self.assertEqual(len(self.load().samples),6)

    def test_empty_line_rejected(self):
        p = self.path/'samples.csv'; p.write_bytes(p.read_bytes()+b'\n')
        self.reject('empty_row','samples.csv',8)

    def test_header_only(self):
        p = self.path/'samples.csv'; p.write_text(p.read_text().splitlines()[0]+'\n')
        self.reject('no_samples')

    def test_bad_integer_forms(self):
        for token in ['1.0','1e3',' 1','1 ','0x10','NaN','', '１']:
            with self.subTest(token=token):
                self.row(1,1,token); self.reject('integer_literal','mic0',2)

    def test_negative_pcm_overflow(self):
        self.row(1,1,'-8388609'); self.reject('integer_range','mic0',2)

    def test_negative_id(self):
        self.row(1,0,'-1'); self.reject('integer_range','sample_id',2)

    def test_wrap_rejected(self):
        self.path = self.root/'restart'; self.row(1,0,'18446744073709551615'); self.row(2,0,'0')
        self.reject('id_order','sample_id',3)

    def test_duplicate_json_key(self):
        p = self.path/'metadata.json'; original = p.read_text()
        p.write_text(original.replace('"sample_rate_hz": 48000','"sample_rate_hz": 48000, "sample_rate_hz": 1'))
        self.reject('duplicate_key','sample_rate_hz')

    def test_nonfinite_json(self):
        self.metadata(sample_rate_hz=float('nan')); self.reject('nonfinite_json')

    def test_bool_numeric_fields(self):
        self.metadata(sample_rate_hz=True); self.reject('numeric_range','sample_rate_hz')

    def test_bool_format_field(self):
        fmt = json.loads((self.path/'metadata.json').read_text())['sample_format']
        fmt['fractional_bits'] = False; self.metadata(sample_format=fmt); self.reject('sample_format')

    def test_coordinates_bad_shape_or_values(self):
        for coords in [[[0,0,0]]*3, [[0,0,0]]*3+[[0,True,0]], [[0,0,0]]*3+[[0,1]], [[0,0,0]]*3+[[0,'1',0]]]:
            with self.subTest(coords=coords):
                self.metadata(coordinates_m=coords); self.reject('coordinates')

    def test_unknown_coordinates_reason_required(self):
        self.metadata(coordinates_m=None,provisional_fields={}); self.reject('missing_reason')

    def test_unknown_capture_reason_required(self):
        self.metadata(capture_point='unknown'); self.reject('missing_reason','provisional_fields.capture_point')

    def test_error_flags_syntax(self):
        for token in ['drop;drop','drop; overflow','drop;','mystery']:
            with self.subTest(token=token):
                self.row(3,6,token); self.reject('unsupported_flags')

    def test_error_without_flags(self):
        self.row(5,6,''); self.reject('error_inconsistency')

    def test_overflow_alone_does_not_invent_missing_samples(self):
        self.path = self.root/'restart'; self.row(1,5,'1'); self.row(1,6,'overflow')
        data=self.load(); self.assertEqual(data.missing_intervals,())
        self.assertEqual(data.clean_intervals[0]['row_start'],1)

    def test_all_error_rows_preserved(self):
        self.path = self.root/'restart'
        for r in [1,2]: self.row(r,5,'1'); self.row(r,6,'unknown')
        data=self.load(); self.assertEqual(data.clean_intervals,()); self.assertEqual(len(data.samples),2)

    def test_config_conflict(self):
        session=ReaderSession(); session.load(self.path)
        self.path=self.root/'restart'; self.metadata(sample_rate_hz=16000)
        with self.assertRaises(DataError) as cm: session.load(self.path)
        self.assertEqual(cm.exception.code,'config_conflict')

    def test_new_config_is_supported_without_whitelist(self):
        session=ReaderSession(); session.load(self.path)
        self.path=self.root/'restart'; self.metadata(sample_rate_hz=16000,config_version='new-16k')
        self.assertEqual(session.load(self.path).metadata['sample_rate_hz'],16000)

    def test_geometry_conflict_across_configs(self):
        session=ReaderSession(); session.load(self.path)
        self.path=self.root/'restart'; self.metadata(config_version='new-geometry',coordinates_m=[[0,0,0]]*4)
        with self.assertRaises(DataError) as cm: session.load(self.path)
        self.assertEqual(cm.exception.code,'geometry_conflict')

    def test_failed_load_does_not_poison_registry(self):
        session=ReaderSession(); self.row(1,1,'8388608')
        with self.assertRaises(DataError): session.load(self.path)
        self.row(1,1,'0'); self.assertEqual(len(session.load(self.path).samples),6)

    def test_same_acquisition_reset_rejected(self):
        session=ReaderSession(); session.load(self.path)
        self.path=self.root/'restart'; self.metadata(acquisition_id='h1-code-001')
        with self.assertRaises(DataError) as cm: session.load(self.path)
        self.assertEqual(cm.exception.code,'acquisition_overlap')

    def test_missing_field(self):
        p=self.path/'metadata.json'; data=json.loads(p.read_text());del data['config_version'];p.write_text(json.dumps(data))
        self.reject('missing_field','config_version')

    def test_extra_description_preserved(self):
        self.metadata(comment={'description':'kept'});self.assertEqual(self.load().metadata['comment'],{'description':'kept'})

    def test_acceptance_reference_is_not_approval(self):
        self.metadata(source_kind='hardware-audio',evidence_level='accepted',acceptance_record='review/123')
        data=self.load();self.assertFalse(data.summary()['acceptance_verified'])

    def test_acceptance_requires_reference(self):
        self.metadata(source_kind='hardware-audio',evidence_level='accepted');self.reject('missing_record','acceptance_record')

    def test_calibration_requires_reference(self):
        self.metadata(calibration_status='calibrated');self.reject('missing_record','calibration_record')

    def test_synthetic_cannot_claim_hardware_acceptance(self):
        self.metadata(evidence_level='accepted',acceptance_record='fake');self.reject('evidence')

    def test_format_code_cannot_be_used_as_acoustic_data(self):
        self.assertEqual(self.load().direction_policy(),'forbidden_non_acoustic_input')


if __name__=='__main__':unittest.main()
