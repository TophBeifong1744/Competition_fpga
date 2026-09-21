"""Independent run segmentation oracle for accepted-row adapter, not RTL."""
from pathlib import Path
import importlib.util, sys, random, json
ROOT=Path('F:/NUEC/review-worktrees/review-h3-logic-f879a54/task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/algorithm-interface-review-20260918/increment-20260923')
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
a=load('adapter_oracle_test',ROOT/'source/logic_adapter.py')
c=load('core_oracle_test',ROOT/'evidence/run02/frozen_framing_model.py')
out=[]
for seed in range(30):
    rng=random.Random(seed);rows=[];ident=(1<<53)+seed*100000
    for j in range(6000):
        ident+=1+(rng.randrange(1,6) if rng.random()<0.0008 else 0)
        flags=rng.choice((1,2,4,8)) if rng.random()<0.0008 else 0
        rows.append(c.Group(ident,(j,-j,j+10,-j-10),flags=flags))
    segments=[];current=[];prev=None;errors=[]
    for row,g in enumerate(rows):
        bad=bool(g.flags) or (prev is not None and g.sample_id!=prev+1)
        prev=g.sample_id
        if bad:
            errors.append(row)
            if current: segments.append(current);current=[]
        else: current.append((row,g))
    if current:segments.append(current)
    expected=[]
    for interval,segment in enumerate(segments):
        for start in range(0,len(segment)-1024+1,512):
            part=segment[start:start+1024]
            expected.append(dict(interval=interval,row_start=part[0][0],row_stop=part[-1][0]+1,ids=(str(part[0][1].sample_id),str(part[-1][1].sample_id)),pcm=tuple(g.pcm for _,g in part)))
    adapter=a.Adapter(c,session=f'seed{seed}')
    for row in rows:adapter.push(row)
    adapter.stop()
    assert len(adapter.frames)==len(expected),(seed,len(adapter.frames),len(expected))
    assert [v['row'] for v in adapter.events]==errors
    for frame,ex in zip(adapter.frames,expected):
        assert (frame['interval_id'],frame['row_start'],frame['row_stop'])==(ex['interval'],ex['row_start'],ex['row_stop'])
        assert (frame['first_id'],frame['last_id'])==ex['ids']
        assert frame['pcm']==ex['pcm']
    out.append(dict(seed=seed,accepted_rows=len(rows),errors=len(errors),nonempty_segments=len(segments),frames=len(expected),result='PASS'))
dest=Path(__file__).with_name('framing-oracle-results.json')
if dest.exists():raise RuntimeError('refuse overwrite')
dest.write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(cases=len(out),rows=sum(r['accepted_rows'] for r in out),frames=sum(r['frames'] for r in out),result='PASS')))
