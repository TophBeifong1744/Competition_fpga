"""Deterministic probe vectors; float reference is not an IP bit-exact model."""
import argparse, cmath, json, random
from pathlib import Path

N = 1024
def fft(x, inverse=False):
    if len(x) == 1:
        return x
    a, b = fft(x[::2], inverse), fft(x[1::2], inverse)
    w = [cmath.exp((2j if inverse else -2j)*cmath.pi*k/len(x))*b[k] for k in range(len(b))]
    return [v+t for v,t in zip(a,w)] + [v-t for v,t in zip(a,w)]

def generate(out):
    out.mkdir(parents=True, exist_ok=False)
    rng = random.Random(20260910)
    vectors=[]
    for job in range(22):
        kind=job%6
        a=2**22
        x=[]
        for n in range(N):
            if kind == 0: z=0j
            elif kind == 1: z=complex(a if n==0 else 0,0)
            elif kind == 2: z=complex(a,0)
            elif kind == 3: z=complex([a,0,-a,0][n%4],0)
            elif kind == 4: z=complex(rng.randrange(-a,a),rng.randrange(-a,a) if job>=6 else 0)
            else: z=complex((2**23-1) if n%2 else -2**23,0)
            x.append(z)
        vectors.append(x)
    with (out/'inputs.mem').open('w',encoding='ascii') as f:
        for x in vectors:
            for z in x:
                f.write(f'{((int(z.imag)&0xffffffff)<<32)|(int(z.real)&0xffffffff):016x}\n')
    (out/'reference.json').write_text(json.dumps([
        [[z.real/N,z.imag/N] for z in fft(x,job>=6)] for job,x in enumerate(vectors)
    ]),encoding='utf-8')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    generate(p.parse_args().out)
