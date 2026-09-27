"""Causal fixed-direction six-microphone DAS, synthetic float64 prototype.

Blocks contain NEW samples (time, 6), not overlapping localization frames.
Array-to-source unit vector, x forward / y left / z up, positions in metres.
"""
import numpy as np

FS=48000
C=343.0
POSITIONS=np.array([[-.020,-.020,0],[.020,-.020,0],[.020,.020,0],[-.020,.020,0],
                    [0,0,np.sqrt(2)*.020],[0,0,-np.sqrt(2)*.020]])
POSITIONS.setflags(write=False)

class FixedDAS:
    """y[n] = mean_m fractional_delay(x_m, L + r_m dot u fs/c).

For plane waves arrival offset is -r dot u fs/c; adding the compensating
positive offset plus fixed L is causal. L=4 samples is relative to the
array-centre plane-wave signal, NOT measured wall-clock latency.
"""
    def __init__(self,direction):
        u=np.asarray(direction,dtype=float)
        if u.shape!=(3,) or not np.isfinite(u).all() or not np.isclose(np.linalg.norm(u),1.,rtol=0,atol=1e-10):
            raise ValueError('direction must be a finite unit vector, array to source')
        self._u=u.copy()/np.linalg.norm(u)
        self.common_delay_samples=int(np.ceil(np.max(np.linalg.norm(POSITIONS,axis=1))*FS/C))
        self._delays=self.common_delay_samples+POSITIONS@self._u*FS/C
        self._whole=np.floor(self._delays).astype(int)
        self._fraction=self._delays-self._whole
        self.history_samples=int(np.ceil(np.max(self._delays)))
        self.reset()

    def reset(self):
        """Explicit start of a new continuous segment; warm-up restarts."""
        self._history=np.zeros((self.history_samples,6))
        self._next=None
        self._seen=0

    def describe(self):
        return dict(sample_rate_hz=FS,positions_m=POSITIONS.tolist(),direction=self._u.tolist(),
                    channel_delay_samples=self._delays.tolist(),common_delay_samples=self.common_delay_samples,
                    common_delay_ms=self.common_delay_samples/FS*1000,history_samples=self.history_samples,
                    interpolation='two-tap linear, causal',output='one sample per input; mean of six channels',
                    timing='output sample ID is processing input ID; source-centre time approximately ID minus common delay',
                    end_policy='no tail flush; output length equals input; final delayed source samples are not emitted')

    def process(self,samples,*,first_sample_id):
        """Return (mono, valid_mask). Invalid warm-up is kept, never scored.

        Missing/duplicate/out-of-order IDs must be resolved by caller; explicit
        reset starts a new segment. Validation failures do not advance state.
        """
        x=np.asarray(samples)
        if x.ndim!=2 or x.shape[1]!=6 or len(x)==0 or x.dtype.kind!='f' or not np.isfinite(x).all():
            raise ValueError('expected nonempty finite floating samples shaped (time, 6)')
        if type(first_sample_id) is not int or not 0<=first_sample_id<=2**64-len(x):
            raise ValueError('sample ID range must fit uint64')
        if self._next is not None and first_sample_id!=self._next:
            raise ValueError('non-contiguous sample IDs: do not repeat overlap or hide gaps; reset explicitly')
        x=np.asarray(x,dtype=np.float64)
        extended=np.concatenate((self._history,x),axis=0)
        index=self.history_samples+np.arange(len(x))
        y=np.zeros(len(x))
        for m,(k,a) in enumerate(zip(self._whole,self._fraction)):
            # Skip the unused second tap for exact integer delays.
            value=(1-a)*extended[index-k,m]
            if a: value=value+a*extended[index-k-1,m]
            y+=value/6
        valid=self._seen+np.arange(len(x))>=self.history_samples
        self._history=extended[-self.history_samples:].copy()
        self._seen+=len(x);self._next=first_sample_id+len(x)
        return y,valid
