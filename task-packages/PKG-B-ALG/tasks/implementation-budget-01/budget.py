"""Source-bound arithmetic/storage ledger and limited quantization risk probes.
No changes to algorithm, tracker or delivered task outputs.
"""
import argparse,hashlib,json,platform,sys,time,importlib.util
from collections import Counter
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'payload/model/python'))
import six_mic_baseline_core as b
import six_mic_localize as localize
from audio_frames import iter_frames,adapt_six_mic_baseline
sys.path.insert(0,str(HERE.parent/'tracked-audio-01'))
from tracked_audio import beam_weights

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
def angle(x,y):
    x=np.asarray(x);y=np.asarray(y);return float(np.degrees(np.arctan2(np.linalg.norm(np.cross(x,y)),x@y)))
def ledger():
    n=b.N;hop=512;channels=len(b.POS);pairs=len(b.PAIRS);fps=b.FS/hop;bins=n//2+1
    freqs=np.fft.rfftfreq(n,1/b.FS);selected=(freqs>=300)&(freqs<=4000)
    bounds=[float(np.linalg.norm(b.POS[i]-b.POS[j])*b.FS/b.C) for i,j in b.PAIRS]
    lag_counts=[2*int(np.ceil(v))+1 for v in bounds]
    tables={}
    for label,real,complex_bytes,pcm in [('float64_current',8,16,8),('illustrative_32bit_components',4,8,4)]:
        tables[label]=dict(input_ring=channels*n*pcm,new_hop_pingpong=2*channels*hop*pcm,
            six_fft_spectra=channels*bins*complex_bytes,pair_cross_and_normalized=2*bins*complex_bytes,
            pair_magnitude=bins*real,pair_mask=bins,pair_correlation=n*real,pair_delays=pairs*real,
            hann=n*real,audio_history=8*channels*pcm,audio_four_weight_arrays=4*channels*9*real,output_hop_pingpong=2*hop*pcm)
    return dict(sample_rate=b.FS,frame=n,hop=hop,channels=channels,pairs=pairs,frames_per_second=fps,
        frame_ms=n/b.FS*1000,hop_ms=hop/b.FS*1000,fft_bins=bins,band_bins=int(selected.sum()),band_bin_indices=[int(np.flatnonzero(selected)[0]),int(np.flatnonzero(selected)[-1])],
        worst_per_frame=dict(rfft_real_1024=channels,irfft_real_1024=pairs,hann_real_mult=channels*n,
            cross_complex_mult=pairs*bins,cross_equivalent_real_mult=4*pairs*bins,cross_equivalent_real_add=2*pairs*bins,
            complex_magnitudes=pairs*bins,complex_by_real_divisions=pairs*bins,physical_lag_peak_candidates=sum(lag_counts)),
        fft_equivalent=dict(transforms_per_second=(channels+pairs)*fps,transform_input_points_per_second=(channels+pairs)*n*fps,
            radix2_full_complex_butterflies_per_frame=(channels+pairs)*(n//2)*int(np.log2(n)),
            warning='Full complex radix-2 surrogate only; NumPy real FFT and selected FPGA IP have different arithmetic and cycle counts.'),
        pair_delay_bounds_samples=bounds,pair_lag_counts=lag_counts,
        transport_bytes_per_second={str(bits):dict(six_channel_input=channels*b.FS*bits//8,mono_output=b.FS*bits//8,analysis_frame_reads=channels*n*fps*bits/8) for bits in [24,32,64]},
        buffer_inventory_bytes=tables,inventory_totals_bytes={k:sum(v.values()) for k,v in tables.items()},
        memory_warning='Explicit engineering inventory, not measured Python RSS or synthesized BRAM. Pingpong and ring separate allocations assumed. Excludes FFT IP internal RAM, DMA alignment, caches, metadata, NumPy temporaries and traces.',
        audio=dict(history_samples=8,common_delay_samples=4,common_delay_ms=4/b.FS*1000,fade_samples=480,fade_ms=10,
            fixed_das_nonzero_taps_max=12,ramp_from_taps_upper_bound=54,goal_taps_upper_bound=12,
            current_audio_filter_mac_upper_bound_per_output=66,blend_real_mult_per_output=2,blend_real_add_per_output=1,
            filter_mac_upper_bound_per_second=66*b.FS,per_audio_subchunk_weight_tests=108,
            warning='Current Python computes both filters even after alpha reaches 1. Interrupted fades may densify old weights. Count excludes alpha division, per-block weight updates and direction-to-delay geometry.'),
        latency=dict(earliest_five_frame_capture_ms=(n+4*hop)/b.FS*1000,hold_ms=200,fade_ms=10,
            note='64 ms is best-case capture from segment start with five consecutive accepted frames; not a worst-case bound. Fallback audio need not wait for lock. Current runner first waits for 1024 points, then hops512. Compute/DMA/PDM delay not included.'))

class Calls:
    def __init__(self):self.count=Counter();self.original=[]
    def __enter__(self):
        for obj,name in [(np.fft,'rfft'),(np.fft,'irfft'),(np.linalg,'matrix_rank'),(np.linalg,'lstsq')]:
            fn=getattr(obj,name);self.original.append((obj,name,fn))
            def wrapped(*args,_name=name,_fn=fn,**kw):
                self.count[_name+'_calls']+=1
                if _name in ['rfft','irfft']:
                    a=np.asarray(args[0]);axis=kw.get('axis',-1);self.count[_name+'_vectors']+=int(a.size/a.shape[axis])
                return _fn(*args,**kw)
            setattr(obj,name,wrapped)
        return self
    def __exit__(self,*exc):
        for obj,name,fn in self.original:setattr(obj,name,fn)

def segments():
    for case in ['stable','drop-return','outside']:
        path=HERE.parent/'tracked-audio-01/evidence/run03'/case/'input'
        segment,_=localize.load_input(path);yield case,segment
    path=HERE.parent/'three-way-audio-01/evidence/run01/directional-interference/input-components.npz'
    with np.load(path,allow_pickle=False) as z:x=z['target']+z['interference']
    yield 'directional-interference',adapt_six_mic_baseline(x.T,sample_rate_hz=48000,positions_m=b.POS,source_id='budget-existing-input',source_sha256=sha(path),first_sample_id=1536)

def quantization(rows):
    result=[]
    for frac in [8,12,16]:
        valid_changed=0;errors=[];maxdelay=0.
        for row in rows:
            tau=np.array([np.nan if v is None else v for v in row['pair_delays_samples']]);q=np.rint(tau*2**frac)/2**frac
            finite=np.isfinite(tau)
            if finite.any():maxdelay=max(maxdelay,float(np.max(np.abs(q[finite]-tau[finite]))))
            solved=localize.solve_delays(q);valid_changed+=solved['valid']!=row['valid']
            if solved['valid'] and row['valid']:errors.append(angle(solved['unit_vector'],row['unit_vector']))
        result.append(dict(delay_fraction_bits=frac,frames=len(rows),candidate_valid_flips=valid_changed,max_delay_error_samples=maxdelay,
            comparable_valid_frames=len(errors),max_direction_change_deg=max(errors,default=None),p95_direction_change_deg=float(np.percentile(errors,95)) if errors else None))
    rng=np.random.default_rng(912);vectors=rng.normal(size=(128,3));vectors/=np.linalg.norm(vectors,axis=1)[:,None]
    weights=[beam_weights(v) for v in vectors];weights+=[.37*weights[i]+.63*weights[i+1] for i in range(0,126,2)]
    coef=[]
    for frac in [15,23]:
        q=[np.rint(w*2**frac)/2**frac for w in weights]
        coef.append(dict(coefficient_fraction_bits=frac,weight_sets=len(weights),max_dc_sum_error=max(abs(float(v.sum())-1) for v in q),
            max_output_error_bound_for_abs_input_le1=max(float(np.abs(a-v).sum()) for a,v in zip(weights,q)),
            universal_54_tap_rounding_bound=54*.5/2**frac))
    return dict(delay_only=result,coefficient_only=coef,scope='Offline sensitivity on existing diagnostic frames and geometry samples only. No FFT/PHAT quantization, tracker replay or end-to-end fixed-point acceptance. Never modifies defaults.')

def run(out):
    out.mkdir(parents=True,exist_ok=False)
    protected={p.relative_to(ROOT).as_posix():sha(p) for name in ['fixed-das-01','tracked-audio-01','three-way-audio-01'] for p in (HERE.parent/name).rglob('*') if p.is_file()}
    protected.update({p.relative_to(ROOT).as_posix():sha(p) for p in (ROOT/'payload/model/python').glob('*.py')})
    theoretical=ledger();observations=[];rows=[]
    for case,segment in segments():
        frames=list(iter_frames(segment));times=[];case_rows=[]
        with Calls() as calls:
            for frame in frames:
                start=time.perf_counter();row=localize.localize_frame(frame);times.append((time.perf_counter()-start)*1000);case_rows.append(row)
        assert calls.count['rfft_vectors']==6*len(frames)
        assert calls.count['irfft_vectors']<=15*len(frames)
        rows.extend(case_rows)
        observations.append(dict(case=case,samples=len(segment.samples),frames=len(frames),valid=sum(r['valid'] for r in case_rows),
            calls=dict(calls.count),input_peak=float(np.max(np.abs(segment.samples))),
            retained_frame_payload_bytes=sum(f.samples.nbytes for f in frames),input_float_payload_bytes=segment.samples.nbytes,
            measured_instrumented_localize_frame_ms=dict(p50=float(np.percentile(times,50)),p95=float(np.percentile(times,95)),max=max(times)),
            scope='Single local instrumented run, includes FFT/GCC/LS and wrapper; excludes input generation, tracking, audio, I/O, DMA and PDM. Not real-time proof.'))
    probes=quantization(rows)
    write(out/'ledger.json',theoretical);write(out/'observations.json',observations);write(out/'quantization-risk.json',probes)
    assert all(sha(ROOT/n)==h for n,h in protected.items())
    write(out/'run.json',dict(status='COMPLETE_BUDGET_NOT_IMPLEMENTATION_ACCEPTANCE',python=sys.version,numpy=np.__version__,platform=platform.platform(),
        baseline='e3f49050cb695beaa8e2ea869ae365a8135a6750 plus three unmerged B audio task folders',source_sha256=sha(Path(__file__)),
        unchanged_files=protected,checks=['6 forward FFT vectors/frame','0..15 inverse FFT vectors/frame','all existing files unchanged'],
        artifacts={p.name:sha(p) for p in out.iterdir() if p.is_file()}))
    print(json.dumps(dict(ledger=theoretical,observations=observations,quantization=probes),ensure_ascii=False))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);run(p.parse_args().out.resolve())
