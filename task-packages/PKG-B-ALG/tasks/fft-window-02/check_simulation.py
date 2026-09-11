"""Exact integer comparison for new window/FFT vectors; no error tolerance."""
import argparse
import csv
import hashlib
import json
from pathlib import Path

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
    with p.open(newline='') as f:return [tuple(map(int,row)) for row in csv.reader(f)]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--vectors',type=Path,required=True)
    parser.add_argument('--sim',type=Path,required=True)
    parser.add_argument('--log',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    assert sha(args.vectors/'inputs.mem') == sha(args.sim/'inputs.mem'), 'simulator input differs from model input'
    expected=read(args.vectors/'model-outputs.csv');actual=read(args.sim/'outputs.csv')
    assert len(expected)==len(actual)==22528, 'wrong output count'
    differences=[]
    for j,(e,a) in enumerate(zip(expected,actual)):
        assert e[:2]==a[:2]==(j//1024,j%1024), 'missing/reordered/duplicate output'
        if e!=a:differences.append(dict(job=a[0],index=a[1],expected=e[2:],actual=a[2:]))
    log=args.log.read_text(errors='replace')
    assert 'PASS FFT probe: 22 jobs, 22528 outputs, TLAST/index/status/backpressure checked' in log
    assert 'Fatal:' not in log and 'ERROR:' not in log, 'simulation error'
    cycles=read(args.sim/'cycles.csv');assert len(cycles)==22
    assert [row[0] for row in cycles]==list(range(22))
    report=dict(status='PASS_NEW_VECTORS_CMODEL_XSIM_BIT_EXACT' if not differences else 'FAIL',
        jobs=22,complex_outputs=len(actual),components=2*len(actual),mismatch_samples=len(differences),
        first_mismatches=differences[:20],config_to_last_output_cycles=[r[5]-r[1]+1 for r in cycles],
        protocol='testbench TLAST/natural index/status/event/backpressure checks passed',
        output_bytes_equal=sha(args.vectors/'model-outputs.csv')==sha(args.sim/'outputs.csv'),
        equal_after_crlf_normalization=(args.vectors/'model-outputs.csv').read_bytes().replace(b'\r\n',b'\n')==(args.sim/'outputs.csv').read_bytes().replace(b'\r\n',b'\n'),
        hashes={str(p):sha(p) for p in [args.vectors/'inputs.mem',args.vectors/'model-outputs.csv',args.sim/'inputs.mem',args.sim/'outputs.csv',args.sim/'cycles.csv',args.log]},
        limitation='Python integer window then new FFT RTL vs AMD model. No window RTL, actual PHAT computation, overflow recovery, full localization or hardware acceptance.')
    with args.out.open('x',encoding='utf-8') as f:json.dump(report,f,indent=2)
    print(json.dumps(report,indent=2))
    return bool(differences)

if __name__=='__main__':raise SystemExit(main())
