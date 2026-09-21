"""Isolated software boundary candidates, not wired into production or RTL."""
import numpy as np

def checked_adapter(codes,original):
    x=np.asarray(codes)
    if x.shape!=(4,513,2) or not np.issubdtype(x.dtype,np.integer) or np.any(x < -2**28) or np.any(x >= 2**28):
        raise ValueError('four-channel S29 half spectra required')
    return original(x.astype(np.int64))

def checked_conjugate(half,original):
    x=np.asarray(half)
    if x.shape!=(513,2) or not np.issubdtype(x.dtype,np.integer) or np.any(x < -2**24) or np.any(x >= 2**24):
        raise ValueError('S25 half spectrum required')
    if x[0,1]!=0 or x[512,1]!=0:raise ValueError('real IFFT requires real DC/Nyquist')
    if np.any(x[1:512,1]==-2**24):raise ValueError('conjugate negation exceeds S25')
    return original(x)

class FrameGuard:
    """Executable proposed completion protocol; source golden has no such handshake."""
    def __init__(self,frame_id,expected):
        self.frame_id=frame_id;self.expected=set(expected);self.done=set();self.invalid=False;self.committed=False;self.events=[]
    def status(self,frame_id,unit,error=False):
        if frame_id!=self.frame_id or unit not in self.expected:raise ValueError('wrong transaction/status identity')
        if error:
            self.invalid=True;self.events.append('LATE_ERROR_AFTER_COMMIT' if self.committed else 'STATUS_ERROR')
        self.done.add(unit)
    def commit(self,stop=False,error=False):
        if stop or error:self.invalid=True;self.events.append('STOP_OR_ERROR')
        if self.invalid or self.committed or self.done!=self.expected:return False
        self.committed=True;self.events.append('COMMITTED');return True
