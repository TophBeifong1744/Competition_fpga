"""Preserve raw simulator records; gzip CSV losslessly, never overwrite evidence."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--simulation',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args()
    if a.out.exists():
        raise SystemExit('Refusing to overwrite simulation archive')
    names=['outputs.csv','cycles.csv','status.csv','simulate.log','compile.log','elaborate.log',
           'xvlog.log','xvhdl.log','tb_fft29.tcl','tb_fft29_vlog.prj','tb_fft29_vhdl.prj']
    assert all((a.simulation/n).is_file() for n in names)
    log=(a.simulation/'simulate.log').read_text(errors='replace')
    assert 'PASS FFT29 archive replay: 361 jobs;' in log
    a.out.mkdir(parents=True)
    records=[]
    for name in names:
        original=(a.simulation/name).read_bytes()
        sha=hashlib.sha256(original).hexdigest()
        stored_name=name+'.gz' if name.endswith('.csv') else name
        if name.endswith('.csv'):
            stored=gzip.compress(original,mtime=0)
            assert gzip.decompress(stored)==original
            (a.out/stored_name).write_bytes(stored)
        else:
            shutil.copyfile(a.simulation/name,a.out/name)
        records.append({'original_name':name,'original_sha256':sha,'original_bytes':len(original),
                        'stored_name':stored_name,'stored_sha256':hashlib.sha256((a.out/stored_name).read_bytes()).hexdigest()})
    (a.out/'packing.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
    print(f'Preserved {len(records)} raw simulation records; CSV losslessly compressed')


if __name__=='__main__':
    main()
