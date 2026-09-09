"""Causal audio routing from original tracker events, not from source truth."""
import sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'fixed-das-01'))
from fixed_das import FixedDAS,FS

def beam_weights(u):
    delays=FixedDAS(u).describe()['channel_delay_samples'];w=np.zeros((6,9))
    for m,d in enumerate(delays):
        k=int(np.floor(d));a=d-k;w[m,k]+=(1-a)/6
        if a:w[m,k+1]+=a/6
    return w

class TrackedAudio:
    """10 ms coefficient crossfade; common delay remains four samples.

    Fade blends two filtered outputs, does not interpolate an angle or reset
    the delay history. It may briefly mix directions; it is not a fresh DOA.
    """
    def __init__(self,fallback,fade_samples=480,sample_origin=0):
        if fallback not in ['single','mute']:raise ValueError('fallback: single or mute')
        if type(fade_samples) is not int or fade_samples<1:raise ValueError('positive fade length required')
        if type(sample_origin) is not int or sample_origin<0:raise ValueError('nonnegative sample origin required')
        self.sample_origin=sample_origin
        self.fallback=fallback;self.fade_samples=fade_samples
        self._fallback=np.zeros((6,9))
        if fallback=='single':self._fallback[0,4]=1
        self.reset()

    def reset(self):
        self.history=np.zeros((8,6));self.current=self._fallback.copy();self.goal=self.current.copy()
        self.ramp_from=self.current.copy();self.progress=self.fade_samples
        self.next_id=None;self.seen=0;self.expiry=None;self.mode='FALLBACK';self.events=[]

    def _request(self,weights,mode,sample):
        if not np.array_equal(weights,self.goal):
            self.ramp_from=self.current.copy();self.goal=weights.copy();self.progress=0
        self.mode=mode
        self.events.append(dict(sample_id=sample,mode=mode,fade_samples=self.fade_samples,expiry_sample_exclusive=self.expiry))

    def _decode(self,event,start):
        ready=float(event['timestamp_ms'])*FS/1000
        if not np.isfinite(ready) or abs(ready-(start-self.sample_origin))>1e-7:
            raise ValueError('event must be ready exactly at block start; no look-ahead')
        fresh=event['fresh_valid'];state=event['state'];stale=event['stale']
        if type(fresh) is not bool or type(stale) is not bool:raise ValueError('boolean validity required')
        if fresh and state=='LOCKED' and not stale:
            weights=beam_weights(event['direction']);mode='BEAM'
        elif state=='HOLD' and stale and not fresh:
            weights=beam_weights(event['display_direction']);mode='HOLD'
        elif state in ['SEARCH','ACQUIRE'] and not fresh and not stale:
            return self._fallback.copy(),'FALLBACK',None
        else:raise ValueError('inconsistent tracker state')
        expiry=float(event['display_expires_at_ms'])*FS/1000
        if not np.isfinite(expiry) or expiry<start-self.sample_origin:raise ValueError('expired direction')
        # Tracker remains eligible at t==expiry; release at the first later sample.
        return weights,mode,self.sample_origin+int(np.floor(expiry+1e-8))+1

    def process(self,samples,*,first_sample_id,tracking=None):
        x=np.asarray(samples)
        if x.ndim!=2 or x.shape[1]!=6 or len(x)==0 or x.dtype.kind!='f' or not np.isfinite(x).all():
            raise ValueError('finite floating (new samples,6) required')
        if type(first_sample_id) is not int or not 0<=first_sample_id<=2**64-len(x):raise ValueError('invalid sample IDs')
        if self.next_id is not None and self.next_id!=first_sample_id:raise ValueError('gap/overlap: record and reset explicitly')
        decoded=self._decode(tracking,first_sample_id) if tracking is not None else None
        if decoded is not None:
            weights,mode,self.expiry=decoded;self._request(weights,mode,first_sample_id)
        extended=np.concatenate((self.history,x),axis=0);out=np.empty(len(x));modes=np.empty(len(x),dtype='U8');offset=0
        while offset<len(x):
            now=first_sample_id+offset
            if self.expiry is not None and now>=self.expiry:
                self.expiry=None;self._request(self._fallback,'FALLBACK',now)
            size=len(x)-offset
            if self.expiry is not None:size=min(size,self.expiry-now)
            indices=8+offset+np.arange(size)
            previous=np.zeros(size);desired=np.zeros(size)
            for m in range(6):
                for k in range(9):
                    if self.ramp_from[m,k]:previous+=self.ramp_from[m,k]*extended[indices-k,m]
                    if self.goal[m,k]:desired+=self.goal[m,k]*extended[indices-k,m]
            alpha=np.minimum((self.progress+np.arange(1,size+1))/self.fade_samples,1.)
            out[offset:offset+size]=(1-alpha)*previous+alpha*desired
            modes[offset:offset+size]=self.mode
            self.progress=min(self.progress+size,self.fade_samples)
            self.current=(1-alpha[-1])*self.ramp_from+alpha[-1]*self.goal
            offset+=size
        valid=self.seen+np.arange(len(x))>=8
        self.history=extended[-8:].copy();self.seen+=len(x);self.next_id=first_sample_id+len(x)
        return out,valid,modes
