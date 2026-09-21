"""Unintegrated S23 input / canonical Q8 angle candidate; reuses frozen CORDIC.

Exact common left shift prevents loss of tiny input vectors. This changes the
numeric profile and needs independent review; it does not change the DOA gate.
"""
from numbers import Integral


def normalized_atan2_q8(y, x, original):
    if any(isinstance(v, bool) or not isinstance(v, Integral) for v in (x, y)):
        raise ValueError('integer S23 vector required')
    x, y = int(x), int(y)
    if any(v < -(1 << 22) or v >= (1 << 22) for v in (x, y)):
        raise ValueError('outside S23')
    magnitude = max(abs(x), abs(y))
    if not magnitude:
        raise ValueError('zero vector')
    shift = 24 - magnitude.bit_length()
    angle = original(y << shift, x << shift)
    return (angle + 180 * 256) % (360 * 256) - 180 * 256
