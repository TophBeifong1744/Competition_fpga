"""Candidate symmetric Hann: S24F23 * U18F17 -> RNE -> saturate S24F23.
The resulting integer code is sign-extended to S25F23 without a left shift.
"""
def round_even_shift(value, shift):
    if shift < 0:
        raise ValueError('negative shift')
    divisor = 1 << shift
    q, r = divmod(value, divisor)
    return q + int(2*r > divisor or (2*r == divisor and q % 2 != 0))

def window_sample(pcm, coefficient):
    if not -(1 << 23) <= pcm < (1 << 23):
        raise ValueError('PCM outside signed24')
    if not 0 <= coefficient <= (1 << 17):
        raise ValueError('Hann coefficient outside [0,1]')
    rounded = round_even_shift(pcm * coefficient, 17)
    clipped = max(-(1 << 23), min((1 << 23)-1, rounded))
    return clipped, clipped != rounded

def pack25(real, imag=0):
    if any(not -(1 << 24) <= v < (1 << 24) for v in (real, imag)):
        raise ValueError('outside signed25')
    return ((imag & 0xffffffff) << 32) | (real & 0xffffffff)

def conjugate_complete(half):
    if len(half) != 513 or half[0][1] != 0 or half[-1][1] != 0:
        raise ValueError('require 513 bins and real DC/Nyquist')
    full = list(half) + [(r, -i) for r, i in reversed(half[1:-1])]
    for r, i in full:
        pack25(r, i)  # Includes conjugation overflow rejection.
    return full
