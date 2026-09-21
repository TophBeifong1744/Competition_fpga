import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import numpy as np
from dynamic_das import DynamicDAS

Q = 4096
A = (0, 22928, 32425, -22928)
B = (0, -32768, 32768, 1)
C = (0, 1234, -5678, 999)


def offline(pcm, rows, fade):
    """Independent full-record Fraction oracle and scheduled transition segments."""
    size = pcm.shape[1]+8
    requested = []
    target, deadline = None, None
    for t in range(size):
        event = rows.get(t)
        if event:
            if event['state'] == 'LOCKED':
                target, deadline = tuple(event['delays']), event['valid_through']
            elif event['state'] in ('SEARCH', 'STOP'):
                target, deadline = None, None
        if deadline is not None and deadline < t:
            target, deadline = None, None
        requested.append(target)
    segments = []
    stable, t = None, 0
    while t < size:
        if requested[t] == stable:
            t += 1
            continue
        selected = requested[t]
        segments.append((t, stable, selected))
        stable = selected
        t += fade
    def value(target, n):
        if n < 0:
            return 0
        if target is None:
            return int(pcm[0, n]) if n < pcm.shape[1] else 0
        total = Fraction(0)
        for ch, d in enumerate(target):
            pos = Fraction(n)-Fraction(d, Q)
            left = pos.numerator//pos.denominator
            f = pos-left
            a = int(pcm[ch, left]) if 0 <= left < pcm.shape[1] else 0
            b = int(pcm[ch, left+1]) if 0 <= left+1 < pcm.shape[1] else 0
            total += a*(1-f)+b*f
        return round(total/4)
    result = []
    k = -1
    for t in range(size):
        if k+1 < len(segments) and segments[k+1][0] == t:
            k += 1
        if k < 0:
            result.append(value(None, t-8)); continue
        start, old, new = segments[k]
        alpha = min(Q, round(Fraction((t-start)*Q, fade)))
        result.append(round(Fraction(value(old,t-8)*(Q-alpha)+value(new,t-8)*alpha,Q)))
    return np.array(result,dtype=np.int64),segments


def run_stream(pcm, rows, chunk, fade):
    engine = DynamicDAS(fade)
    output, traces = [], []
    t = 0
    while t < pcm.shape[1]:
        if t in rows:
            engine.control(**rows[t])
        boundary = min([v for v in rows if v > t]+[pcm.shape[1]])
        stop = min(t+chunk,boundary,pcm.shape[1])
        y, trace = engine.push(pcm[:,t:stop], final=stop==pcm.shape[1])
        output.extend(y);traces.extend(trace);t=stop
    return np.array(output,dtype=np.int64),traces,engine


def main():
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    a.out.mkdir(parents=True,exist_ok=False)
    rng=np.random.default_rng(2026092107)
    pcm=rng.integers(-2**23,2**23,size=(4,2100),dtype=np.int64)
    locked=lambda d,ttl:dict(state='LOCKED',delays=d,valid_through=ttl)
    cases={
        'fallback':{},
        'hold_expiry':{11:locked(A,530),100:dict(state='HOLD'),530:dict(state='HOLD')},
        'rapid_latest':{11:locked(A,1900),12:locked(B,1900),13:locked(C,1900),490:locked(B,1900),492:locked(C,1900),800:dict(state='SEARCH')},
        'stop_during_fade':{11:locked(A,1900),21:dict(state='STOP')},
        'expiry_and_fresh':{11:locked(A,600),601:locked(B,1400)},
        'pending_expires':{11:locked(A,1900),12:locked(B,13)},
        'same_target_refresh':{11:locked(A,600),500:locked(A,1100)},
        'all_delays_extreme':{0:locked(B,2000)},
    }
    reports=[]
    for name,rows in cases.items():
        expected,segments=offline(pcm,rows,480)
        for chunk in (1,7,64,513):
            actual,traces,e=run_stream(pcm,rows,chunk,480)
            assert np.array_equal(actual,expected),(name,chunk)
            assert e.max_history<=17 and e.max_beams<=2
            actual_starts=[x['emit'] for x in e.events if x['kind']=='FADE_START']
            assert actual_starts==[x[0] for x in segments]
            assert all(0<=r['alpha']<=Q for r in traces)
            reports.append(dict(case=name,chunk=chunk,samples=len(actual),max_history=e.max_history,max_beams=e.max_beams,fade_starts=actual_starts,sha256=hashlib.sha256(actual.astype('<i4').tobytes()).hexdigest()))
        if name=='hold_expiry':
            assert next(x['emit'] for x in e.events if x['kind']=='TTL_EXPIRED')==531
        if name=='pending_expires':
            assert all(B not in (x[1],x[2]) for x in segments)
        if name=='expiry_and_fresh':
            assert not any(x['emit']==601 and x['kind']=='TTL_EXPIRED' for x in e.events)
    # PCM endpoint domain and short records incl EOF; no acoustic simulation.
    edgecases=0
    for length in (1,7,8,9,17,97):
        for v in (-2**23,0,2**23-1):
            x=np.full((4,length),v,dtype=np.int64)
            rows={0:locked(B,1000)}
            expected,_=offline(x,rows,3)
            got,_,e=run_stream(x,rows,7,3)
            assert np.array_equal(got,expected)
            edgecases+=1
    # Future control and future PCM cannot influence an earlier emission.
    base={11:locked(A,1900)}; changed={**base,900:locked(B,1900)}
    y,_,_=run_stream(pcm,base,64,480); z,_,_=run_stream(pcm,changed,64,480)
    assert np.array_equal(y[:900],z[:900])
    modified=pcm.copy();modified[:,900:]=0
    z,_,_=run_stream(modified,base,64,480)
    assert np.array_equal(y[:900],z[:900])
    rejects=0
    for row in [dict(state='HOLD',valid_through=5),locked(A,-1),locked((0,0,0,32769),5),dict(state='BOGUS'),locked(A,True)]:
        e=DynamicDAS()
        try:e.control(**row)
        except ValueError:rejects+=1
        else:raise AssertionError(row)
    e=DynamicDAS();e.control(state='SEARCH')
    try:e.control(state='SEARCH')
    except ValueError:rejects+=1
    else:raise AssertionError('duplicate accepted')
    e=DynamicDAS();e.push(pcm[:,:1],final=True)
    for call in (lambda:e.control(state='SEARCH'),lambda:e.push(pcm[:,:1])):
        try:call()
        except ValueError:rejects+=1
        else:raise AssertionError('closed accepted')
    pcm_rejects=0
    for bad in (np.zeros((3,2),dtype=np.int64),np.zeros((4,2),dtype=float),
                np.zeros((4,2),dtype=bool),np.full((4,2),2**23,dtype=np.int64),
                np.full((4,2),-2**23-1,dtype=np.int64)):
        e=DynamicDAS()
        try:e.push(bad)
        except ValueError:pcm_rejects+=1
        else:raise AssertionError('invalid PCM accepted')
        assert e.time==0 and not e.samples
    # Exhaust every cancellation offset within one small fade: serialized policy
    # must be entirely mono within 2*fade, though not necessarily within one.
    fallback_checks=0;worst=0
    for offset in range(1,18):
        rows={0:locked(A,200),offset:dict(state='STOP')}
        _,trace,_=run_stream(pcm[:,:100],rows,7,17)
        settled=next(r['emit'] for r in trace if r['emit']>=offset and r['endpoints']==(None,))
        wait=settled-offset;assert wait<=34
        worst=max(worst,wait);fallback_checks+=1
    # Sustained faster-than-fade updates cannot increase beam/history bank count.
    rows={t:locked((A,B,C)[t%3],2000) for t in range(800)}
    expected,_=offline(pcm,rows,480)
    actual,_,burst=run_stream(pcm,rows,64,480)
    assert np.array_equal(actual,expected) and burst.max_beams<=2 and burst.max_history<=17
    (a.out/'cases.json').write_text(json.dumps(reports,indent=2),encoding='utf-8')
    np.savez_compressed(a.out/'mathematical-pcm.npz',pcm=pcm)
    result=dict(status='AUTHOR_NODE_PASS',dynamic_chunk_cases=len(reports),endpoint_short_cases=edgecases,invalid_cases=rejects,invalid_pcm_cases=pcm_rejects,causality_checks=2,fallback_offset_checks=fallback_checks,small_fade_worst_fallback_samples=worst,burst_updates=800,max_beam_banks=2,mono_banks=1,max_history_rows=17,lookahead_samples=8,fade_samples=480,fallback_bound_samples=960,policy='serialized fade, latest pending wins; not original immediate retarget equivalence',hardware=False)
    (a.out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(result)


if __name__=='__main__':main()
