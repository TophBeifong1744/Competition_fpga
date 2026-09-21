"""Fixed-delay chunk adapter candidate, no direction updates or realtime guarantee."""
from fractions import Fraction
from numbers import Integral
import numpy as np

class StreamDAS:
    def __init__(self,delays):
        if len(delays)!=4 or any(not isinstance(d,Integral) or isinstance(d,bool) or abs(d)>8*4096 for d in delays):
            raise ValueError('four integer Q12 delays within +/-8 samples required')
        self.delays=list(map(int,delays));self.history=max(0,max((d+4095)//4096 for d in self.delays))+1
        self.lookahead=max(0,max((-d+4095)//4096 for d in self.delays))+1
        self.buffer=np.zeros((4,0),dtype=np.int64);self.base=0;self.received=0;self.next=0;self.closed=False

    def push(self,chunk,final=False):
        if self.closed:raise ValueError('stream already finalized')
        x=np.asarray(chunk)
        if x.ndim!=2 or x.shape[0]!=4 or not np.issubdtype(x.dtype,np.integer) or np.any(x < -2**23) or np.any(x>=2**23):
            raise ValueError('S24 four-channel integer chunk required')
        self.buffer=np.concatenate([self.buffer,x.astype(np.int64)],axis=1);self.received+=x.shape[1]
        stop=self.received if final else max(self.next,self.received-self.lookahead)
        output=[]
        for n in range(self.next,stop):
            acc=0
            for ch,d in enumerate(self.delays):
                left,frac=divmod(n*4096-d,4096)
                def sample(index):
                    if index<0 or index>=self.received:return 0
                    if index<self.base:raise AssertionError('released required history')
                    return int(self.buffer[ch,index-self.base])
                acc+=sample(left)*(4096-frac)+sample(left+1)*frac
            value=round(Fraction(acc,16384));assert -2**23<=value<2**23
            output.append(value)
        self.next=stop;release=max(self.base,self.next-self.history)
        self.buffer=self.buffer[:,release-self.base:];self.base=release;self.closed=final
        return np.array(output,dtype=np.int64)
