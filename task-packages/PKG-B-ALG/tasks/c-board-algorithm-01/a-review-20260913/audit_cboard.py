import sys,json,hashlib
from pathlib import Path
import numpy as np
root=Path(sys.argv[1]); out=Path(sys.argv[2])
pkg=root/'task-packages/PKG-B-ALG/tasks/c-board-algorithm-01'
sys.path.insert(0,str(pkg)); import run as m
checks=[]
for integer in (False,True):
    for sign in (-1,1):
        c=np.zeros(1024,dtype=np.int64); c[(sign*6)%1024]=100; c[(sign*5)%1024]=99; c[(sign*7)%1024]=1
        p=m.quality(c,5.597667638,integer)
        assert p['valid'] and p['edge_peak'] and abs(p['tau_samples'])<5.65
        c[(sign*5)%1024]=1
        assert not m.quality(c,5.597667638,integer)['valid']
checks.append('positive/negative interpolated edge acceptance and rejection in both chains')
class Engine:
    def __init__(self,overflow=False): self.calls=[]; self.overflow=overflow
    def transform(self,codes,forward):
        self.calls.append(forward)
        return np.zeros((1024,2),dtype=np.int64), self.overflow and forward
for overflow in (False,True):
    e=Engine(overflow); rows,_,_=m.fixed(np.zeros((1024,4),dtype=np.int64),[5.6]*6,e)
    assert all(not r['valid'] for r in rows) and e.calls==[True]*4
checks.append('full scheduler zero/forward-overflow rejection with no IFFT calls')
disagreements=[]; counts=[]
for f in sorted(out.glob('*-frames.json')):
    frames=json.loads(f.read_text()); assert len(frames)==61
    for idx,frame in enumerate(frames):
        assert frame['row_start']==idx*512
        assert int(frame['last_sample_id'])-int(frame['first_sample_id'])==1023
        for k,(a,b) in enumerate(zip(frame['floating'],frame['reference25'])):
            for r in (a,b):
                if 'tau_samples' in r: assert r['valid']==(abs(r['tau_samples'])<=r['bound_samples']+.05)
            if a['valid']!=b['valid']: disagreements.append(dict(file=f.name,frame=idx,pair=m.PAIRS[k],floating=a,reference25=b))
    pairs=[(a,b) for frame in frames for a,b in zip(frame['floating'],frame['reference25'])]
    both=[(a,b) for a,b in pairs if a['valid'] and b['valid']]
    counts.append(dict(file=f.name,both=len(both),changes=sum(a['peak']!=b['peak'] for a,b in both),max_delta=max(abs(a['tau_samples']-b['tau_samples']) for a,b in both)))
assert len(disagreements)==2 and [c['both'] for c in counts]==[366,343]
checks.append('122 frame identities, continuous validity and 732 pair comparisons')
result=dict(status='PASS',checks=checks,counts=counts,disagreements=disagreements)
print(json.dumps(result,indent=2))
