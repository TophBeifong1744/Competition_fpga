"""Fixed subband/leave-one-band diagnostic on pinned real frames."""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np

def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m

def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    root=a.repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918';cp=root/'checkpoint-20260923';seal=load(cp/'SNAPSHOT-SHA256.json')['files'];pins={}
    def frozen(p):
        h=sha(p);assert h==seal[p.relative_to(root).as_posix()];pins[p.relative_to(a.repo).as_posix()]=h;return load(p)
    summary=frozen(cp/'evidence/run01/summary.json');chosen=frozen(root/'closeout-0918-20260921/acoustic/pairs01/frames.json')
    deps=load(cp/'dependencies.json')
    for path,h in deps.items():assert sha(a.repo/path)==h,path
    diag=module('frequency_diag',a.repo/'task-packages/PKG-B-ALG/tasks/c-board-algorithm-01/run.py')
    band=np.array(diag.chain.BAND,dtype=bool);assert np.flatnonzero(band).tolist()==list(range(7,86))
    ranges={'low':(7,32),'mid':(33,58),'high':(59,85)}
    masks={'full':band.copy()}
    for name,(lo,hi) in ranges.items():
        mask=np.zeros(513,dtype=bool);mask[lo:hi+1]=True;masks['only_'+name]=mask;masks['drop_'+name]=band&~mask
    protocol=dict(bins=ranges,bin_hz=46.875,relative_mask='freeze full-band 0.02 mask for every variant; no per-band renormalization',min_bins=12,projection='unchanged RMS<=0.5,norm[0.1,1.3]',selection='frozen320 selected target frames plus all1122 background frames',no_sweep=True,not_independent=True,background_gate='frozen candidate gate, never recalibrated',scope='diagnostic only; no candidate selection using nominal angles')
    dump(a.out/'protocol.json',protocol)
    selected={}
    for r in chosen:selected.setdefault(r['capture'],set()).add(r['start'])
    output=[];fft=ifft=0
    for path in sorted((cp/'evidence/run01').glob('*-frames.json')):
        rows=frozen(path);name=path.name[:-12];background='_bg_' in name
        raw=next(p for p in summary['pins'] if p.endswith('/'+name+'/raw.bin'))
        assert sha(a.repo/raw)==summary['pins'][raw];pins[raw]=summary['pins'][raw]
        meta_path=(a.repo/raw).with_name('metadata.json');rel=meta_path.relative_to(a.repo).as_posix();assert sha(meta_path)==summary['pins'][rel];pins[rel]=sha(meta_path)
        meta=load(meta_path);pos=np.array(meta['coordinates_m']);assert pos.tolist()==[[0,0,0],[.04,0,0],[.04,.04,0],[0,.04,0]]
        assert meta['sample_rate_hz']==48000 and meta['channel_order']==['mic0','mic1','mic2','mic3']
        bounds=[np.linalg.norm(pos[j]-pos[i])*48000/343 for i,j in diag.PAIRS]
        pcm=np.fromfile(a.repo/raw,dtype='<u4').reshape(-1,8)[:,2:6].view('<i4')
        for row in rows:
            if not background and row['start'] not in selected[name]:continue
            x=pcm[row['start']:row['stop']];sp=np.fft.rfft(x.T/2**23*np.hanning(1024),axis=1);fft+=4
            variants={k:[] for k in masks};energies=[]
            for k,(i,j) in enumerate(diag.PAIRS):
                z=sp[i]*sp[j].conj();amp=np.abs(z);active=band&(amp>=.02*max(float(amp[band].max()),1e-15))
                energies.append({n:dict(bins=int((active&masks['only_'+n]).sum()),cross_amp_sum=float(amp[masks['only_'+n]].sum())) for n in ranges})
                for name_mode,filter_mask in masks.items():
                    kept=active&filter_mask;pr=dict(valid=False,reason='FEWER_THAN_12_BINS',bins=int(kept.sum()))
                    if kept.sum()>=12:
                        corr=np.fft.irfft(np.where(kept,z/np.maximum(amp,1e-15),0),n=1024);ifft+=1
                        pr.update(diag.quality(corr,bounds[k],False))
                    variants[name_mode].append(pr)
            results={}
            for mode,pairs in variants.items():
                projection=diag.projection(pairs,pos,48000,343);good=[(k,p) for k,p in enumerate(pairs) if p['valid']];cycle=None
                if len(good)>=3:
                    g=np.zeros((len(good),4));tau=[]
                    for j,(k,pr) in enumerate(good):u,v=diag.PAIRS[k];g[j,u]=-1;g[j,v]=1;tau.append(pr['tau_samples'])
                    tau=np.array(tau);fitted=g[:,1:]@np.linalg.lstsq(g[:,1:],tau,rcond=None)[0];cycle=float(np.sqrt(np.mean((tau-fitted)**2)))
                valid=projection.get('advisory_consistent',False)
                results[mode]=dict(valid=valid,angle=projection.get('advisory_azimuth_deg') if valid else None,norm=projection.get('projection_norm'),residual=projection.get('residual_samples'),cycle=cycle,pair_reasons=[p['reason'] for p in pairs],taus=[p.get('tau_samples') for p in pairs],retained_bins=[p['bins'] for p in pairs])
            full=results['full'];old=row['projection']
            assert full['valid']==old.get('advisory_consistent',False) and full['pair_reasons']==row['pair_reasons']
            if full['valid']:assert np.isclose(full['angle'],row['numeric_angle'],rtol=1e-12,atol=1e-10)
            for key,oldkey in [('norm','projection_norm'),('residual','residual_samples')]:
                if oldkey in old:assert np.isclose(full[key],old[oldkey],rtol=1e-12,atol=1e-10)
            output.append(dict(capture=name,start=row['start'],background=background,marker_excluded=row['marker_excluded'],gate=row['candidates']['band_calibrated_duration'],variants=results,frequency_features=energies))
    counts={}
    for group,rows in [('selected_target',[r for r in output if not r['background']]),('selected_nonmarker',[r for r in output if not r['background'] and not r['marker_excluded']]),('background',[r for r in output if r['background']])]:
        counts[group]={}
        for mode in masks:
            valid=[r for r in rows if r['variants'][mode]['valid']]
            seq=sorted(rows,key=lambda r:(r['capture'],r['start']));jumps=[]
            for left,right in zip(seq,seq[1:]):
                l=left['variants'][mode];r=right['variants'][mode]
                if left['capture']==right['capture'] and right['start']-left['start']==512 and l['valid'] and r['valid']:jumps.append(abs((r['angle']-l['angle']+180)%360-180))
            counts[group][mode]=dict(frames=len(rows),valid=len(valid),newly_accepted=sum(not r['variants']['full']['valid'] for r in valid),lost=sum(r['variants']['full']['valid'] and not r['variants'][mode]['valid'] for r in rows),gate_and_cone=sum(r['gate'] and abs(r['variants'][mode]['angle'])<=60+1e-10 for r in valid),cycle_fail=sum(r['variants'][mode]['cycle'] is not None and r['variants'][mode]['cycle']>.5 for r in rows),adjacent_both_valid=len(jumps),jump_gt8=sum(j>8 for j in jumps),jump_p50=None if not jumps else float(np.median(jumps)))
    dump(a.out/'frames.json',output);dump(a.out/'result.json',dict(protocol=protocol,pins=pins,dependency_pins=deps,counts=counts,fft_calls=fft,ifft_calls=ifft,matched_original_full_frames=len(output),source_sha256=sha(Path(__file__)),not_adopted=True))
    print(json.dumps(counts,indent=2))
if __name__=='__main__':main()
