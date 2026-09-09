"""Export only after strict historical input verification in the source environment."""
import argparse, sys
from pathlib import Path
import numpy as np
import reference_inputs as r

def export(out):
    out.mkdir(parents=True,exist_ok=False)
    r.common.verify_package()
    coverage=r.required();records={};checks=[]
    # Preserve the exporting environment even if an input later fails validation.
    r.write(out/'environment.json',r.common.environment())
    for row in coverage:
        m=r.historical(row);plan=row['plan']
        _,meta=r.study.generate(plan,m['noise'],m['direction'],m['room'],m['seed'])
        try:r.common.DIFF.input(m,meta)
        finally:r.write(out/'export-input-checks.json',r.common.DIFF.inputs)
        key=r.signature(plan,m['direction'],m['room'],m['seed'])
        if key not in records:
            rir,rir_meta=r.s.make_rir(plan,m['direction'],m['room'],m['seed'])
            assert r.s.array_hash(rir)==m['rir_sha256']
            filename=m['rir_sha256']+'.npz';path=out/filename
            if not path.exists():np.savez_compressed(path,rir=np.asarray(rir,dtype='<f8'))
            records[key]=dict(signature=key,file=filename,file_sha256=r.sha(path),array_sha256=m['rir_sha256'],shape=list(rir.shape),meta=rir_meta)
        checks.append(dict(use=row['use'],condition=m['condition'],seed=m['seed'],four_historical_hashes_exact=True))
        print(row['use'],m['condition'],m['seed'],flush=True)
    origins={row['manifest']:r.sha(r.ROOT/row['manifest']) for row in coverage}
    origins['research/stable-wrong-01/cohort.json']=r.sha(r.ROOT/'research/stable-wrong-01/cohort.json')
    r.write(out/'index.json',dict(schema=1,source_commit='df4146af6aab3263209f54bb36ded8693d2d9d90',coverage=coverage,historical_manifests=origins,rirs=list(records.values()),checks=checks,
        command=[sys.executable,'-B',str(Path(__file__).resolve()),'--out',str(out)],
        sources={p.relative_to(r.ROOT).as_posix():r.sha(p) for p in [Path(__file__),r.HERE/'reference_inputs.py',Path(r.study.__file__),Path(r.s.__file__),Path(r.s.batch.__file__),Path(r.s.batch.b.__file__)]},
        environment_sha256=r.sha(out/'environment.json'),storage='Only lossless float64 RIR arrays. Target, noise and input rebuilt, each checked against immutable historical hashes.'))
    print('COMPLETE',len(coverage),'bindings',len(records),'RIR keys',sum(p.stat().st_size for p in out.glob('*.npz')),'bytes',flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);export(p.parse_args().out.resolve())
