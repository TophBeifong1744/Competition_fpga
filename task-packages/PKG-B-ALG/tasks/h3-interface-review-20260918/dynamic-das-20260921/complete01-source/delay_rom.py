"""Strict integer lookup candidate; SHA binds generated ROM, no runtime trig."""
import hashlib
from numbers import Integral
import numpy as np


class DelayROM:
    def __init__(self, path, expected_sha256):
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected_sha256:
            raise ValueError('delay ROM byte identity mismatch')
        self.codes=np.load(path,allow_pickle=False)
        if self.codes.shape!=(92160,3) or self.codes.dtype!=np.dtype('<i2'):
            raise ValueError('ROM requires 92160 x 3 little-endian S16')
        self.codes.flags.writeable=False

    def lookup(self, angle_q8):
        if not isinstance(angle_q8,Integral) or isinstance(angle_q8,(bool,np.bool_)) or not -46080<=angle_q8<46080:
            raise ValueError('canonical Q8 angle required in [-180,180) degrees')
        return (0,*(int(x) for x in self.codes[int(angle_q8)+46080]))
