"""Algebraic check on measured delays, not a new acoustic simulation or calibration."""
import argparse
import json
from pathlib import Path
import numpy as np

def execute(inputs,out):
    out.mkdir(parents=True,exist_ok=False)
    rows=json.loads((inputs/'frames.json').read_text(encoding='utf-8'))
    pos=np.array([[0,0],[.04,0],[.04,.04],[0,.04]])
    pairs=[(i,j) for i in range(4) for j in range(i+1,4)]
    matrix=np.array([(pos[j]-pos[i])*48000/343 for i,j in pairs])
    checks=[]
    for row in rows:
        valid=[i for i,p in enumerate(row['pairs']) if p['valid']]
        if len(valid)<3:continue
        a=matrix[valid];d=np.array([row['pairs'][i]['tau_samples'] for i in valid])
        u,_,rank,_=np.linalg.lstsq(a,d,rcond=None)
        if rank<2:continue
        residual=float(np.sqrt(np.mean((a@u-d)**2)))
        # Global delay sign inversion and coordinate reflections preserve fit and norm.
        errors=[]
        for aa,dd in [(a,-d),(a@np.diag([-1,1]),d),(a@np.diag([1,-1]),d)]:
            v=np.linalg.lstsq(aa,dd,rcond=None)[0]
            errors.extend([abs(float(np.sqrt(np.mean((aa@v-dd)**2)))-residual),abs(float(np.linalg.norm(v)-np.linalg.norm(u)))])
        assert max(errors)<1e-12
        checks.append(dict(capture=row['capture'],index=row['index'],max_invariance_error=max(errors)))
    report=dict(status='MEASURED_DELAY_ALGEBRA_PASS',checked_frames=len(checks),max_error=max(x['max_invariance_error'] for x in checks),
                conclusion='Global sign/axis reflection cannot repair residual/norm rejection. No claim of physical channel order calibration.',checks=checks)
    (out/'result.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('INVARIANCE_PASS',len(checks),report['max_error'])

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    a=p.parse_args();execute(a.input,a.out)
