"""Historical-hash-bound RIR references. No numerical acceptance fallback."""
import copy, hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OLD=HERE.parent/'pr3-repro-01'
sys.path.insert(0,str(OLD))
import common
sys.path.insert(0,str(ROOT/'research/narrowband-guard-01'))
import study
s=study.s
read=common.read;write=common.write;sha=common.sha

def signature(plan,direction,room,seed):
    return hashlib.sha256(json.dumps([plan,direction,room,seed],sort_keys=True,separators=(',',':')).encode()).hexdigest()

def required():
    """Derive coverage from frozen protocols and actual live audit selectors."""
    rows=[]
    for name in ['narrowband-guard-01','subband-confidence-01','leave-band-out-01','effective-perturbation-01']:
        folder=ROOT/'research'/name;p=read(folder/'protocol.json')
        for phase in (['development','validation'] if name=='narrowband-guard-01' else ['evidence']):
            path=folder/phase;plan=read(path/'plan.json')['acoustic_plan' if phase!='evidence' else 'acoustic']
            seed=p[phase+'_seeds'][0] if phase!='evidence' else p['seeds'][0]
            for i,m in enumerate(read(path/'inputs.json')):
                if m['seed']==seed and m['direction']['name']=='front' and (phase=='evidence' or m['room']['name']=='dry'):
                    rows.append(dict(use='audit-'+name,manifest=(path/'inputs.json').relative_to(ROOT).as_posix(),index=i,plan=plan))
    folder=ROOT/'research/effective-perturbation-01/evidence';inputs=read(folder/'inputs.json');plan=read(folder/'plan.json')['acoustic']
    ix={(m['condition'],m['seed']):i for i,m in enumerate(inputs)}
    pairs=sorted({(m['condition'],m['seed']) for m in read(ROOT/'research/stable-wrong-01/cohort.json')})
    assert len(pairs)==26
    for condition,seed in pairs:
        for use,key in [('stable-original',(condition,seed)),('stable-dry',(condition.rsplit('__',1)[0]+'__dry',seed))]:
            rows.append(dict(use=use,manifest=(folder/'inputs.json').relative_to(ROOT).as_posix(),index=ix[key],plan=plan))
    return rows

def historical(row):return read(ROOT/row['manifest'])[row['index']]

class References:
    def __init__(self,directory=None):
        self.directory=Path(directory or HERE/'reference')
        self.index=read(self.directory/'index.json')
        self.uses=[]
        assert self.index['coverage']==required(), 'reference coverage differs from frozen requirements'
        for path,digest in self.index['historical_manifests'].items():
            assert sha(ROOT/path)==digest, ('historical manifest changed',path)
        self.records={r['signature']:r for r in self.index['rirs']}
        for row in self.index['coverage']:
            m=historical(row);key=signature(row['plan'],m['direction'],m['room'],m['seed'])
            r=self.records[key]
            assert r['array_sha256']==m['rir_sha256'], 'RIR unbound to historical input'
        for r in self.records.values():self.load(r)
    def load(self,r):
        path=self.directory/r['file']
        assert sha(path)==r['file_sha256'], ('reference file bytes',r['file'])
        with np.load(path,allow_pickle=False) as z:
            assert z.files==['rir']
            a=z['rir']
        assert a.dtype==np.dtype('<f8') and list(a.shape)==r['shape'] and np.isfinite(a).all()
        assert s.array_hash(a)==r['array_sha256'], 'reference array hash'
        assert r['meta']['rir_sha256']==r['array_sha256']
        return a
    def make_rir(self,plan,direction,room,seed):
        key=signature(plan,direction,room,seed)
        assert key in self.records, ('UNDECLARED_REFERENCE_INPUT',direction,room,seed)
        r=self.records[key];a=self.load(r)
        self.uses.append(dict(signature=key,rir_sha256=s.array_hash(a),file_sha256=r['file_sha256']))
        return a,copy.deepcopy(r['meta'])
    def install(self):
        s.make_rir=self.make_rir

def preflight(out):
    refs=References();refs.install();rows=[]
    for row in refs.index['coverage']:
        m=historical(row)
        _,meta=study.generate(row['plan'],m['noise'],m['direction'],m['room'],m['seed'])
        common.DIFF.input(m,meta) # unchanged exact historical input policy
        rows.append(dict(use=row['use'],condition=m['condition'],seed=m['seed'],hashes={k:meta[k] for k in ['input_sha256','target_sha256','noise_sha256','rir_sha256']}))
    write(out/'reference-reconstruction.json',dict(status='PASS_EXACT_HISTORICAL_INPUTS',coverage=len(rows),rows=rows,rir_loads=refs.uses))
    return dict(status='PASS',covered_inputs=len(rows),policy='All four historical hashes exact; no tolerance or hash bypass')
