"""Verify RTL accepted words through binary and H1 export; synthetic only."""
import argparse
import csv
import json
import struct
from pathlib import Path
from export_four import export

parser=argparse.ArgumentParser()
parser.add_argument('words',type=Path)
parser.add_argument('output',type=Path)
args=parser.parse_args()
if args.output.exists(): raise FileExistsError('use new output')
with args.words.open(newline='') as f: records=list(csv.DictReader(f))
assert len(records)==456
args.output.mkdir(parents=True)
bases=[0xfffffff8,0x200000000,0]
for run,base in enumerate(bases):
    group=[r for r in records if int(r['run'])==run]
    assert [int(r['word']) for r in group]==list(range(152))
    raw=b''.join(struct.pack('<I',int(r['data_hex'],16)) for r in group)
    path=args.output/f'run-{run}.bin';path.write_bytes(raw)
    dst=args.output/f'run-{run}'
    meta=export(path,dst,acquisition_id=f'xsim-{run}',config_version='four-record-0.1-test',
                source_kind='synthetic-code',provenance='Vivado XSim accepted AXIS words, not real microphones',
                capture_point='pcm4_capture_axis testbench handshake monitor')
    with (dst/'samples.csv').open(newline='') as f: rows=list(csv.DictReader(f))
    assert len(rows)==19 and meta['sample_count']==19
    for n,row in enumerate(rows):
        assert int(row['sample_id'])==base+n
        for ch in range(4):
            choice=(n+ch)%4
            expected=[-8388608,8388607,0,-513-n*4-ch][choice]
            assert int(row[f'mic{ch}'])==expected
        assert row['stream_error']=='1' and row['error_flags']=='unknown'
    assert meta['evidence_level']=='synthetic'
result={'result':'PASS','rtl_words':456,'groups':57,'runs':3,
        'scope':'RTL handshake -> BIN -> H1 CSV exact values; synthetic only, not B approval'}
(args.output/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
