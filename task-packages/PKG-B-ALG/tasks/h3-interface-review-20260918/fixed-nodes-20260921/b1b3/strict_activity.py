"""Input-contract candidate only; delegates unchanged arithmetic/state transitions."""
from numbers import Integral
import numpy as np

def checked_power(half,window,original_node):
    half=np.asarray(half);window=np.asarray(window)
    if half.shape!=(4,513,2) or not np.issubdtype(half.dtype,np.integer) or np.any(half < -2**24) or np.any(half >= 2**24):
        raise ValueError('half spectrum must be 4x513x2 signed25 integer codes')
    if window.shape!=(1024,) or not np.issubdtype(window.dtype,np.integer) or np.any(window<0) or np.any(window>2**17) or not np.any(window):
        raise ValueError('window must be nonzero 1024 integer Hann codes in [0,2**17]')
    return original_node(half,window)

def integer(value):
    return isinstance(value,Integral) and not isinstance(value,bool)

def u64_vector(values,label):
    try: values=list(values)
    except TypeError as exc: raise ValueError(label+' must contain four U64 integers') from exc
    if len(values)!=4 or any(not integer(v) or not 0<=v<2**64 for v in values):
        raise ValueError(label+' must contain four U64 integers (no floats/bools)')
    return [int(v) for v in values]

class StrictActivity:
    def __init__(self,legacy_class,noise,cfg):
        expected=dict(on_power_ratio=4,off_power_ratio=2,attack_frames=3,release_frames=3,minimum_active_channels=3)
        if any(k not in cfg or not integer(cfg[k]) or cfg[k]!=v for k,v in expected.items()):
            raise ValueError('unsupported typed integer configuration')
        floor=cfg.get('band_rms_floor_codes')
        if not integer(floor) or not 0<=floor<2**32:raise ValueError('floor must be nonnegative integer with U64 square')
        self.impl=legacy_class(u64_vector(noise,'noise'),dict(cfg))

    def reset(self):self.impl.reset()

    def update(self,power,invalid=False):
        if type(invalid) is not bool:raise ValueError('invalid flag must be bool')
        # Retain legacy validation-before-invalid order. Malformed input is an API error.
        return self.impl.update(u64_vector(power,'power'),invalid)

    @property
    def state(self):return (self.impl.active,self.impl.attack,self.impl.release)
