"""Analytic FFT scale/width checks without window or PHAT; no RTL claim."""
import argparse
import json
from pathlib import Path
import numpy as np
import scan

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dll',type=Path,required=True)
    ap.add_argument('--dependency-dir',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();args.out.mkdir(parents=True,exist_ok=False)
    assert scan.sha(args.dll)=='79ec8ccc56cd56c4277a3c8c46ed0fca8435f6e62107854414b1672eda5575ca'
    engine=scan.chain.FFT(args.dll,args.dependency_dir);records=[]
    protocol=json.loads((scan.HERE/'protocol.json').read_text())
    try:
        for key,config in protocol['candidates'].items():
            candidate=scan.Forward(engine,config)
            try:
                for kind in ('dc','impulse','zero'):
                    win=np.zeros((6,1024),dtype=np.int64);expected=np.zeros((6,1024,2),dtype=np.int64)
                    if kind=='dc':
                        win[:]=2**18
                        expected[:,0,0]=2**(18+10+config['width']-25-sum(config['shifts']))
                    if kind=='impulse':
                        win[:,0]=2**22
                        expected[:,:,0]=2**(22+config['width']-25-sum(config['shifts']))
                    raw,packed,flags,shift,epsilon=candidate.run(win)
                    assert np.array_equal(raw,expected),(key,kind)
                    assert not any(flags)
                    records.append(dict(candidate=key,input=kind,exact=True,overflow=flags,
                        common_right_shift=shift,epsilon_codes=epsilon))
            finally:candidate.close()
    finally:engine.close()
    scan.write(args.out/'checks.json',dict(checks=records,complex_components=12*6*1024*2,
        source_sha256=scan.sha(Path(__file__)),scan_sha256=scan.sha(Path(scan.__file__)),
        model_sha256=scan.sha(args.dll),status='PASS_ANALYTIC_CMODEL_SCALE_ONLY'))
    print('12 analytical cases, 147456 real/imaginary components exact; no overflow.')

if __name__=='__main__':main()
