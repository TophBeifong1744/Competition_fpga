"""Unfrozen integer PHAT candidate, keeping baseline masks on quantized inputs."""
from fractions import Fraction
from math import isqrt

EPSILON_CODES = Fraction(2**26, 10**15)  # 1e-15 * 2^-20 * 2^46
MAG_FRAC = 16
RECIP_FRAC = 30
OUTPUT_FRAC = 23

def rne_ratio(n, d):
    if d <= 0: raise ValueError('positive denominator required')
    q,r=divmod(n,d)
    return q+int(2*r>d or (2*r==d and q%2))

def rne_shift(n, shift):
    return rne_ratio(n,1<<shift) if shift>=0 else n<<(-shift)

def sqrt_rne(n):
    if n<0: raise ValueError('negative square')
    lo=isqrt(n)
    # Compare sqrt(n) with lo+1/2 without a float conversion.
    return lo+int(4*n>(2*lo+1)**2)

RECIP_LUT = tuple(rne_ratio((1<<RECIP_FRAC)*512,513+2*k) for k in range(256))

def reciprocal(magnitude_q16):
    if magnitude_q16 <= 0: raise ValueError('zero magnitude is invalid')
    exponent=magnitude_q16.bit_length()-1
    mantissa=rne_shift(magnitude_q16,exponent-RECIP_FRAC)
    index=min(255,max(0,(mantissa-(1<<RECIP_FRAC))>>22))
    r=RECIP_LUT[index]
    for _ in range(2):
        mr=rne_shift(mantissa*r,RECIP_FRAC)
        r=rne_shift(r*((2<<RECIP_FRAC)-mr),RECIP_FRAC)
    return r,exponent

def cross(a,b):
    ar,ai=a; br,bi=b
    if any(not -(1<<24)<=v<(1<<24) for v in (ar,ai,br,bi)):
        raise ValueError('FFT code outside signed25')
    return ar*br+ai*bi, ai*br-ar*bi

def normalize(z):
    re,im=z
    square=re*re+im*im
    if square==0: return (0,0),dict(valid=False,magnitude_q16=0)
    magnitude=sqrt_rne(square<<(2*MAG_FRAC))
    r,e=reciprocal(magnitude)
    values=tuple(rne_shift(v*r,e+RECIP_FRAC-MAG_FRAC-OUTPUT_FRAC) for v in z)
    if any(not -(1<<24)<=v<(1<<24) for v in values):
        raise OverflowError('PHAT output outside S25F23; reject pair')
    return values,dict(valid=True,magnitude_q16=magnitude,reciprocal_q30=r,exponent=e)

def mask_for(crosses,band):
    squares=[r*r+i*i for r,i in crosses]
    maximum=max((v for v,keep in zip(squares,band,strict=True) if keep),default=0)
    # For integer cross codes: every nonzero amplitude >=1 > epsilon.
    # Exact squared form of amp >= 0.02 * max(amp_band_max, epsilon).
    return [keep and square>0 and 2500*square>=maximum
            for square,keep in zip(squares,band,strict=True)]

def phat_pair(a,b,band,ip_overflow=False):
    if not(len(a)==len(b)==len(band)==513): raise ValueError('513 bins required')
    if ip_overflow:
        return dict(valid=False,reason='UPSTREAM_IP_OVERFLOW',mask=[False]*513,output=[(0,0)]*513)
    z=[cross(x,y) for x,y in zip(a,b)]
    mask=mask_for(z,band)
    if sum(mask)<12:
        return dict(valid=False,reason='FEWER_THAN_12_BINS',mask=mask,output=[(0,0)]*513)
    output=[normalize(value)[0] if keep else (0,0) for value,keep in zip(z,mask)]
    return dict(valid=True,reason='VALID_QUANTIZED_INPUT_PAIR',mask=mask,output=output)
