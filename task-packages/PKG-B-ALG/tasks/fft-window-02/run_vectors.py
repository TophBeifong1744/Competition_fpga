"""New integer-window/FFT vectors and installed AMD bit-accurate goldens."""
import argparse
import csv
import ctypes as C
from fractions import Fraction
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import random
import numpy as np
from window_model import round_even_shift, window_sample, pack25, conjugate_complete

HERE = Path(__file__).resolve().parent
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--dll', type=Path, required=True)
    parser.add_argument('--dependency-dir', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    # Independent exact rational oracle, including negative ties.
    tested = 0
    for shift in range(1, 19):
        for q in range(-7, 8):
            for offset in (-1, 0, 1):
                value = q*(1 << shift) + (1 << (shift-1)) + offset
                assert round_even_shift(value, shift) == round(Fraction(value, 1 << shift))
                tested += 1
    for pcm in (-(1<<23), -3, -1, 0, 1, 3, (1<<23)-1):
        for coefficient in (0, 1, 65536, 131071, 131072):
            code, saturated = window_sample(pcm, coefficient)
            assert code == round(Fraction(pcm*coefficient, 1<<17)) and not saturated
            tested += 1
    for args_bad in ((1<<23, 1), (0, 131073)):
        try: window_sample(*args_bad)
        except ValueError: pass
        else: raise AssertionError('invalid window argument accepted')
    for half in ([ (0,0) ]*512, [(0,1)] + [(0,0)]*512,
                 [(0,0), (0,-(1<<24))] + [(0,0)]*511):
        try: conjugate_complete(half)
        except ValueError: pass
        else: raise AssertionError('invalid conjugate assembly accepted')
    window = np.hanning(1024)
    coeff = [round(float(v)*2**17) for v in window]
    assert coeff == coeff[::-1] and coeff[0] == coeff[-1] == 0
    (args.out/'hann-u18f17.json').write_text(json.dumps(coeff)+'\n')
    rng = random.Random(2026091101)
    n = np.arange(1024)
    pcms = [[0]*1024, [-(1<<23)]*1024,
        [(1<<23)-1 if k%2 else -(1<<23) for k in range(1024)],
        [((1<<23)-1) if k == 511 else 0 for k in range(1024)],
        [round((2**23-1)*float(v)) for v in np.sin(2*np.pi*37.25*n/1024)],
        [rng.randrange(-(1<<23), 1<<23) for _ in range(1024)]]
    names = ['zero','negative_fullscale_dc','alternating_fullscale','center_impulse','offbin_tone_37.25','random_seed2026091101']
    jobs, stats = [], []
    for pcm, name in zip(pcms, names):
        quantized = [window_sample(x,c) for x,c in zip(pcm,coeff)]
        values = [v for v,s in quantized]
        error = np.array(values)-np.array(pcm)*window
        stats.append(dict(name=name, saturation_count=sum(s for v,s in quantized),
            max_window_error_codes=float(max(abs(error))), rms_window_error_codes=float(np.sqrt(np.mean(error**2)))))
        jobs.append([(v,0) for v in values])
    for index in range(16):
        # Independent random half spectra, bounded components; not computed PHAT.
        local = random.Random(2026091200+index)
        half = [(local.randrange(-2**22,2**22),0)]
        half += [(local.randrange(-2**21,2**21),local.randrange(-2**21,2**21)) for _ in range(511)]
        half += [(local.randrange(-2**22,2**22),0)]
        jobs.append(conjugate_complete(half))
    with (args.out/'inputs.mem').open('w', newline='\n') as f:
        for job in jobs:
            for r,i in job: f.write(f'{pack25(r,i):016x}\n')
    (args.out/'pcm-inputs.json').write_text(json.dumps(pcms)+'\n')
    module_path = HERE/'source-snapshot/cmodel_abi.py'
    spec = importlib.util.spec_from_file_location('fft_window_cmodel_abi',module_path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    handles = [os.add_dll_directory(str(p.resolve())) for p in (args.dll.parent,args.dependency_dir)]
    dll = C.CDLL(str(args.dll.resolve())); prefix='xilinx_ip_xfft_v9_1_'
    create=getattr(dll,prefix+'create_state'); create.argtypes=[m.Generics]; create.restype=C.c_void_p
    sim=getattr(dll,prefix+'bitacc_simulate'); sim.argtypes=[C.c_void_p,m.Inputs,C.POINTER(m.Outputs)];sim.restype=C.c_int
    destroy=getattr(dll,prefix+'destroy_state');destroy.argtypes=[C.c_void_p];destroy.restype=None
    state=create(m.Generics(10,2,0,0,25,24,1,0,1,1,0));assert state
    rows=[]; metrics=[]
    try:
        for job, samples in enumerate(jobs):
            re=(C.c_double*1024)(*[r/2**24 for r,i in samples]);im=(C.c_double*1024)(*[i/2**24 for r,i in samples])
            ro,io=(C.c_double*1024)(),(C.c_double*1024)(); shifts=(C.c_int*10)(*([1]*10))
            output=m.Outputs(ro,1024,io,1024,0,0)
            assert sim(state,m.Inputs(10,re,1024,im,1024,shifts,10,int(job<6)),C.byref(output))==0
            assert not output.overflow and output.xk_re_size==output.xk_im_size==1024
            codes=[]
            for k in range(1024):
                r,i=ro[k]*2**24,io[k]*2**24
                assert r.is_integer() and i.is_integer()
                rows.append((job,k,int(r),int(i)));codes.append(complex(r,i))
            x=np.array([complex(r,i) for r,i in samples])
            reference=np.fft.fft(x)/1024 if job<6 else np.fft.ifft(x)
            error=np.array(codes)-reference
            metrics.append(dict(job=job,overflow=output.overflow,max_component_error_codes=float(max(max(abs(error.real)),max(abs(error.imag)))),
                max_imaginary_output_codes=float(max(abs(np.array(codes).imag))) if job>=6 else None))
    finally:
        destroy(state)
        for h in handles:h.close()
    with (args.out/'model-outputs.csv').open('w',newline='') as f:csv.writer(f,lineterminator='\n').writerows(rows)
    result=dict(status='PASS_WINDOW_UNIT_AND_CMODEL_GENERATION_NOT_RTL',rational_checks=tested,
        rejected_invalid_cases=5, jobs=22,seed_forward=2026091101,seeds_inverse=list(range(2026091200,2026091216)),
        window=stats,transforms=metrics,model_dll_sha256=sha(args.dll),
        dependency_hashes={p.name:sha(p) for p in args.dependency_dir.glob('*.dll')},
        input_sha256=sha(args.out/'inputs.mem'),model_output_sha256=sha(args.out/'model-outputs.csv'),
        source_hashes={str(p.relative_to(HERE)):sha(p) for p in HERE.rglob('*') if p.is_file() and 'evidence' not in p.parts and '__pycache__' not in p.parts},
        python=platform.python_version(),numpy=np.__version__,platform=platform.platform())
    (args.out/'generation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],rational_checks=tested,jobs=22)))

if __name__=='__main__':main()
