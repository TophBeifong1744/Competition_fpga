"""Rebuild PCM using integer-input interpolation and stored coefficients; audit TTL."""
import argparse
import json
from pathlib import Path
import sys
import wave
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
from render_three import ROOT,PARENT,load,sha,dump,verify_inputs,ReaderSession


def decode(path):
    with wave.open(str(path),'rb') as w:
        if (w.getnchannels(),w.getsampwidth(),w.getframerate())!=(1,3,48000):
            raise ValueError('WAV_HEADER_MISMATCH')
        data=w.readframes(w.getnframes())
    return np.array([int.from_bytes(data[i:i+3],'little',signed=True)
                     for i in range(0,len(data),3)],dtype=np.int64)


def linear_codes(pcm,n,delay):
    value=np.zeros(len(n))
    for ch,d in enumerate(delay):
        at=n-d
        left=np.floor(at).astype(np.int64)
        if left.min()<0 or np.ceil(at).max()>=len(pcm): raise ValueError('TAP_OUTSIDE_INTERVAL')
        fraction=at-left
        right=np.minimum(left+1,len(pcm)-1)
        value+=(pcm[left,ch]*(1-fraction)+pcm[right,ch]*fraction)/4
    return value


def check(directory):
    verify_inputs()
    result=load(directory/'result.json');cfg=load(PARENT/'config.json')
    for p,want in result['input_pins'].items():
        if sha(ROOT/p)!=want: raise ValueError('INPUT_HASH_CHANGED: '+p)
    for p,want in result['source_sha256'].items():
        if sha(ROOT/p)!=want: raise ValueError('EXECUTABLE_CHANGED: '+p)
    for p,want in load(directory/'SHA256.json').items():
        if sha(directory/p)!=want: raise ValueError('OUTPUT_HASH_CHANGED: '+p)
    reports=[]
    for row in result['records']:
        item=next(x for x in cfg['recordings'] if x['label']==row['label'])
        rec=ReaderSession().load(ROOT/item['directory'])
        a,b=row['input_rows'];start,stop=[v-a for v in row['reference_rows']]
        pcm=rec.samples[a:b].astype(np.int64)
        n=np.arange(start,stop)
        prefix=row['label']+f'-interval{row["interval"]:02}'
        with np.load(directory/(prefix+'-mix.npz'),allow_pickle=False) as data:
            weights=data['weights']
        if weights.shape!=(len(n),len(row['bank_vectors'])) or not np.isfinite(weights).all() or np.any(weights<0):
            raise ValueError('INVALID_MIX_WEIGHTS')
        np.testing.assert_allclose(weights.sum(axis=1),1,rtol=0,atol=1e-14)
        bank=[pcm[n,0].astype(float)]
        for vector,delay in zip(row['bank_vectors'][1:],row['bank_delays_samples'][1:]):
            expected=(np.array(cfg['positions_m'])-cfg['positions_m'][0])@np.array(vector)*48000/343
            np.testing.assert_allclose(delay,expected,rtol=0,atol=1e-12)
            if np.any(np.ceil(n[:,None]-np.array(delay))>n[:,None]+row['common_availability_delay_samples']):
                raise ValueError('AUDIO_LOOKAHEAD_EXCEEDS_COMMON_LATENCY')
            bank.append(linear_codes(pcm,n,delay))
        expected=dict(single=bank[0],manual=linear_codes(pcm,n,row['manual_delays_samples']),
                      automatic=np.sum(np.array(bank).T*weights,axis=1))
        expires=np.full(weights.shape[1],-np.inf)
        event_pos=0;expired_nonzero=0;unready_nonzero=0
        for k,t in enumerate(n):
            while event_pos<len(row['events']) and row['events'][event_pos]['ready']<=t:
                event=row['events'][event_pos]
                if event['fresh'] and event['target']:
                    expires[event['target']]=event['valid_through']
                event_pos+=1
            unready_nonzero+=int(np.count_nonzero((weights[k,1:]>0)&np.isneginf(expires[1:])))
            expired_nonzero+=int(np.count_nonzero((weights[k,1:]>0)&(expires[1:]<t)))
        if expired_nonzero or unready_nonzero: raise ValueError('DIRECTION_LIFETIME_VIOLATION')
        files=[]
        for entry in row['files']:
            path=directory/entry['file']
            if sha(path)!=entry['sha256']: raise ValueError('WAV_HASH_CHANGED')
            actual=decode(path)
            wanted=np.rint(expected[entry['branch']]*entry['gain'])
            if np.any(wanted<-2**23) or np.any(wanted>2**23-1): raise ValueError('GOLDEN_OVERFLOW')
            wanted=wanted.astype(np.int64)
            if actual.shape!=wanted.shape: raise ValueError('PCM_LENGTH_MISMATCH')
            mismatch=int(np.count_nonzero(actual!=wanted))
            if mismatch: raise ValueError(f'PCM_GOLDEN_MISMATCH: {path.name}: {mismatch}')
            files.append(dict(file=path.name,pcm_values=len(actual),mismatch_count=mismatch,
                              max_abs_code_difference=int(np.max(np.abs(actual-wanted))),
                              max_adjacent_code_step=int(np.max(np.abs(np.diff(actual))))))
        reports.append(dict(label=row['label'],files=files,expired_nonzero_weights=expired_nonzero,
                            unready_nonzero_weights=unready_nonzero))
    return dict(status='AUTHOR_NUMERICAL_AUDIT_PASS',records=reports,
                input_hashes_exact=True,independent_integer_input_pcm_formula=True,
                independent_reviewer=False,listening_completed=False,acoustic_acceptance=False)


if __name__=='__main__':
    ap=argparse.ArgumentParser(__doc__)
    ap.add_argument('--directory',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args()
    if args.out.exists(): raise ValueError('AUDIT_OUTPUT_EXISTS')
    report=check(args.directory)
    dump(args.out,report)
    print('PASS: exact PCM golden, common alignment, no expired/unready beam weight; listening pending.')
