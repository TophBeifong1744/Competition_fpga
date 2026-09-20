"""B descriptive diagnostics with unchanged candidate gate; never validation scores."""
import hashlib,importlib.util,json,math,sys
from pathlib import Path
import numpy as np
ROOT=Path('F:/NUEC/review-worktrees/eight-94b5fe7')
P=ROOT/'task-packages/PKG-A-ACQ/tasks/four-channel-diagnostic-01/batches/trusted-direction-input-20260918'
OUT=Path(__file__).parent
gate_path=ROOT/'task-packages/PKG-B-ALG/tasks/h3-complete-20260918/source/presence.py'
spec=importlib.util.spec_from_file_location('frozen_presence',gate_path)
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
manifest=json.loads((P/'evidence/background-confirmation-20260920-01/CURRENT-DATA-SHA256.json').read_text())
captures=[(P/k).parent for k in manifest if k.endswith('/metadata.json')]
assert len(captures)==8
N=4096;win=np.hanning(N);freq=np.fft.rfftfreq(N,1/48000)
bands=[(0,100),(100,300),(300,3400),(3400,8000),(8000,24001)]
def stats(x):
    if len(x)==0:return None
    z=x-x.mean(axis=0)
    result={'rows':len(x),'mean':x.mean(axis=0).tolist(),'raw_rms':np.sqrt(np.mean(x*x,axis=0)).tolist(),
            'demeaned_rms':np.sqrt(np.mean(z*z,axis=0)).tolist(),'min':x.min(axis=0).tolist(),'max':x.max(axis=0).tolist(),
            'correlation_zero_lag':np.corrcoef(x.T).tolist(),'pairwise_identical':any(np.array_equal(x[:,i],x[:,j]) for i in range(4) for j in range(i))}
    frames=np.stack([x[s:s+N] for s in range(0,len(x)-N+1,2048)])
    frames-=frames.mean(axis=1,keepdims=True)
    power=np.mean(np.abs(np.fft.rfft(frames*win[None,:,None],axis=1))**2,axis=0)
    power[1:-1]*=2
    norm=N*np.sum(win*win)
    result['bands_hz']=bands
    result['band_power_fraction']=[(power[(freq>=a)&(freq<b)].sum(axis=0)/power.sum(axis=0)).tolist() for a,b in bands]
    result['band_rms_codes']=[np.sqrt(power[(freq>=a)&(freq<b)].sum(axis=0)/norm).tolist() for a,b in bands]
    result['dominant_bin_hz']=freq[np.argmax(power,axis=0)].tolist()
    return result

results=[];shorttime={};frames_all={}
for c in sorted(captures):
    name=c.name;print('DIAG',name,flush=True)
    raw=(c/'raw.bin').read_bytes();u=np.frombuffer(raw,dtype='<u4').reshape(-1,8)
    x=u[:,2:6].view('<i4').astype(float);ids=u[:,0].astype(np.uint64)+(u[:,1].astype(np.uint64)<<32)
    assert len(x)==288250 and np.all(np.diff(ids)==1) and not u[:,6:].any()
    alignment=json.loads((c.parent/'alignment.json').read_text())
    background='bg_' in name
    core=None;exclusions=[]
    if not background:
        channels=alignment['channels']
        core=[math.ceil(max(r['speech_interval_source_mapped_samples'][0] for r in channels)),
              math.floor(min(r['speech_interval_source_mapped_samples'][1] for r in channels))]
        for marker in ('start_marker','end_marker'):
            lo=min(r[marker]['index'] for r in channels)-9600
            hi=max(r[marker]['index']+7200*r['source_to_capture_scale'] for r in channels)+9600
            exclusions.append([max(0,math.floor(lo)),min(len(x),math.ceil(hi))])
    rows=[]
    for start in range(0,len(x)-1024+1,512):
        end=start+1024
        marker=any(start<b and end>a for a,b in exclusions)
        category='reported_background' if background else ('marker_or_guard' if marker else 'candidate_speech' if core[0]<=start and end<=core[1] else 'other_nonmarker_unlabelled')
        original=gate.evaluate(x[start:end].astype(np.int32),stream_error=False,clip_flag=False)
        rows.append({'start':start,'stop':end,'category':category,'present':original['present'],'active_channels':original['active_channels'],'reason':original['reason'],'rms_codes_floor':original['rms_codes_floor']})
    counts={}
    for category in sorted(set(r['category'] for r in rows)):
        items=[r for r in rows if r['category']==category]
        counts[category]={'frames':len(items),'gate_pass':sum(r['present'] for r in items),'gate_pass_fraction_descriptive_only':sum(r['present'] for r in items)/len(items)}
    assert len(rows)==561
    frames_all[name]=rows
    z=x[:len(x)//960*960].reshape(-1,960,4);z-=z.mean(axis=1,keepdims=True)
    shorttime[name]={'time_s':((np.arange(len(z))+.5)*.02).tolist(),'rms':np.sqrt(np.mean(z*z,axis=1)).tolist()}
    # Recover x, since the view above deliberately uses a writable array.
    x=u[:,2:6].view('<i4').astype(float)
    result={'capture':name,'path':c.relative_to(P).as_posix(),'raw_sha256':hashlib.sha256(raw).hexdigest(),
            'first_id':str(ids[0]),'last_id':str(ids[-1]),'background_operator_label':background,'full':stats(x),
            'candidate_speech_interval_rows':core,'marker_plus_provisional_0p2s_guard_exclusions':exclusions,
            'candidate_speech':None if core is None else stats(x[core[0]:core[1]]),'unchanged_presence_gate':counts,
            'gate_all_pass':sum(r['present'] for r in rows),'frames':len(rows)}
    results.append(result)
result={'sha':'94b5fe79d87e038e895878fb31030cded469bb33','gate_source_sha256':hashlib.sha256(gate_path.read_bytes()).hexdigest(),
        'gate_parameters':{'rms_min_codes':2048,'peak_min_codes':4096,'minimum_active_channels':3},
        'N':1024,'H':512,'configured_fs':48000,'spectral_N':4096,'spectral_hop':2048,
        'limits':'No tuning, acoustic truth labels, accuracy/FPR/recall or SNR gain. Candidate speech is intersection of author source-mapped intervals, not calibrated onset/offset. Marker 0.2s guard is provisional and not measured decay.',
        'captures':results}
(OUT/'diagnosis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
(OUT/'gate-frames.json').write_text(json.dumps(frames_all,indent=2)+'\n')
(OUT/'short-time.json').write_text(json.dumps(shorttime,indent=2)+'\n')
for r in results:
    print(r['capture'],'RMS',np.round(r['full']['demeaned_rms']).tolist(),'gate',r['gate_all_pass'],'categories',r['unchanged_presence_gate'])
