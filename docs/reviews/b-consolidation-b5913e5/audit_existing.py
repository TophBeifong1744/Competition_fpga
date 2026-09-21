"""A independent postprocessing: no FFT, audio generation or new algorithm."""
import collections
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import numpy as np

root, repo, output = map(Path, sys.argv[1:4])
cp = root/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918/checkpoint-20260923'
pkg = cp.parent/'closeout-0918-20260921'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
old = subprocess.check_output(['git', '-C', str(repo), 'cat-file', 'blob',
    'fe67547635ff254f9f91c7f917e8dedb6daf3363:'+str(cp.relative_to(root)).replace('\\','/')+'/SNAPSHOT-SHA256.json'])
assert old == (pkg/'SNAPSHOT-before-consolidation.json').read_bytes()
rows = {p.name.removesuffix('-frames.json'):read(p) for p in (cp/'evidence/run01').glob('*-frames.json')}
pairs = read(pkg/'acoustic/pairs01/frames.json')
pair_map = {(r['capture'],r['index']):r for r in pairs}
expected = set()
rejections = collections.Counter()
totals = collections.Counter()
for name, frames in rows.items():
    anchors = {i for i,r in enumerate(frames) if r['trackers']['candidate60']['state']=='ACQUIRE'}
    expected.update((name,j) for i in anchors for j in [i-1,i,i+1] if 0<=j<len(frames))
    totals['old_acquire'] += len(anchors)
    for r in frames:
        totals['frames'] += 1
        if not r['candidates']['band_calibrated_duration']: continue
        pr=r['projection']
        why = 'consistent' if pr.get('advisory_consistent',False) else 'insufficient_pairs' if pr['valid_pairs']<3 else '+'.join(k for k,v in [('residual',pr.get('residual_samples',0)>.5),('norm',not .1<=pr.get('projection_norm',0)<=1.3)] if v)
        rejections[why]+=1
assert expected==set(pair_map) and len(pairs)==320
assert dict(rejections)==read(pkg/'acoustic/pairs01/result.json')['all_787_gate_frames_projection']
anchor_reasons=collections.Counter()
for (name,i), r in pair_map.items():
    original=rows[name][i]
    assert (r['start'],r['stop'],r['first_id'],r['tracker'])==(original['start'],original['stop'],original['first_id'],original['trackers']['candidate60'])
    assert [p['reason'] for p in r['pairs']]==original['pair_reasons']
    if r['anchor']: anchor_reasons.update(p['reason'] for p in r['pairs'])
assert dict(anchor_reasons)=={'VALID':777,'FEWER_THAN_12_BINS':39,'TAU_BOUND':6}
restarts=read(pkg/'acoustic/pairs01/spread-restarts.json')
assert len(restarts)==27
for r in restarts:
    name,i=r['capture'],r['current_index']
    a,b=pair_map[name,i],pair_map[name,i-1]
    changes=sum(x.get('peak')!=y.get('peak') for x,y in zip(a['pairs'],b['pairs'],strict=True))
    assert changes==r['pairs_changed_integer_peak'] and changes>0
    angle=rows[name][i]['numeric_angle']
    delta=max(abs((angle-rows[name][j]['numeric_angle']+180)%360-180) for j in r['previous_indices'])
    assert abs(delta-r['max_angle_change_deg'])<1e-12 and delta>8
for p in (pkg/'acoustic/joint01').glob('*-frames.json'):
    name=p.name.removesuffix('-frames.json')
    for a,b in zip(rows[name],read(p),strict=True):
        assert (a['start'],a['stop'],a['candidates']['band_calibrated_duration'])==(b['start'],b['stop'],b['gate'])
        totals['new_acquire']+=b['trackers']['joint_gated']['state']=='ACQUIRE'
        totals['joint_gated_fresh']+=b['trackers']['joint_gated']['fresh_valid']
        totals['joint_ungated_fresh']+=b['trackers']['joint_ungated']['fresh_valid']
assert totals==dict(frames=4488,old_acquire=137,new_acquire=120,joint_gated_fresh=0,joint_ungated_fresh=0)
checks=read(pkg/'fixed/checks-02/frozen-array-checks.json')
assert len(checks)==120
for r in checks:
    with np.load(cp/'evidence/golden02'/(r['capture']+'.npz'),allow_pickle=False) as z:
        a=z[r['key']]
        assert str(a.dtype)==r['dtype'] and list(a.shape)==r['shape'] and r['match'] is True
result=dict(status='A_INDEPENDENT_POSTPROCESS_PASS',totals=dict(totals),gate_projection=dict(rejections),
    selected_frames=len(pairs),selected_pairs=len(pairs)*6,anchor_pair_reasons=dict(anchor_reasons),
    restart_count=len(restarts),frozen_array_descriptors=120,old_snapshot_bytes_equal=True,
    fft_rerun=False,production_approval=False)
with output.open('x',encoding='utf-8') as f: json.dump(result,f,indent=2)
print(json.dumps(result))
