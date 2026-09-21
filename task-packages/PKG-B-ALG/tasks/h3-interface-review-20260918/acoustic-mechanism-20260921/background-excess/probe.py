"""Frozen pre-background spectral excess; fixed candidate on all eight captures."""
import argparse,hashlib,importlib.util,json,math,sys
from pathlib import Path
import numpy as np
def load(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,v):p.write_text(json.dumps(v,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def excess(power,reference):
    return np.clip(1-reference/np.maximum(power,1e-30),0,1)
def gate_weight(power,reference,i,j):return np.sqrt(excess(power[i],reference[i])*excess(power[j],reference[j]))
def main():
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
    repo=a.repo.resolve();root=repo/'task-packages/PKG-B-ALG/tasks/h3-interface-review-20260918';cp=root/'checkpoint-20260923';seal=load(cp/'SNAPSHOT-SHA256.json')['files'];pins={}
    def frozen(p):
        h=sha(p);assert h==seal[p.relative_to(root).as_posix()];pins[p.relative_to(repo).as_posix()]=h;return load(p)
    config=frozen(cp/'config.json');summary=frozen(cp/'evidence/run01/summary.json');deps=load(cp/'dependencies.json')
    for p,h in deps.items():assert sha(repo/p)==h,p
    diag=module('excess_diag',repo/'task-packages/PKG-B-ALG/tasks/c-board-algorithm-01/run.py');track=module('excess_tracker',repo/'task-packages/PKG-B-ALG/payload/model/python/sector_tracker.py')
    marker_path=repo/'docs/reviews/eight-94b5fe7/markers/results.json';assert sha(marker_path)==deps[marker_path.relative_to(repo).as_posix()]
    markers={r['capture']:r for r in load(marker_path)['captures']}
    protocol=dict(reference_capture=config['calibration_run'],reference='per-channel per-bin linear percentile95 of uncentered Hann1024 spectrum power',weight='sqrt(max(0,1-N95/Pi)*max(0,1-N95/Pj))',band=[7,85],mask='original full-band2percent unchanged',min_positive_weight_bins=12,activity='frozen calibrated gate unchanged',tracker='unchanged cone60/acquire5/spread8/hold200ms',sweep=False,all_eight_already_inspected=True,independent_validation=False)
    dump(a.out/'protocol.json',protocol)
    positions=np.array([[0,0,0],[.04,0,0],[.04,.04,0],[0,.04,0]]);bounds=[np.linalg.norm(positions[j]-positions[i])*48000/343 for i,j in diag.PAIRS];band=np.array(diag.chain.BAND,dtype=bool)
    def inputs(name):
        path=next(p for p in summary['pins'] if p.endswith('/'+name+'/raw.bin'));assert sha(repo/path)==summary['pins'][path];pins[path]=summary['pins'][path]
        mp=(repo/path).with_name('metadata.json');rel=mp.relative_to(repo).as_posix();assert sha(mp)==summary['pins'][rel];pins[rel]=sha(mp);meta=load(mp)
        assert meta['coordinates_m']==positions.tolist() and meta['sample_rate_hz']==48000 and meta['channel_order']==['mic0','mic1','mic2','mic3']
        pcm=np.fromfile(repo/path,dtype='<u4').reshape(-1,8)[:,2:6].view('<i4');rows=frozen(cp/('evidence/run01/'+name+'-frames.json'));return pcm,rows
    pre,pre_rows=inputs(config['calibration_run']);window=np.hanning(1024)
    spectra=np.array([np.fft.rfft(pre[r['start']:r['stop']].T/2**23*window,axis=1) for r in pre_rows]);reference=np.percentile(np.abs(spectra)**2,95,axis=0);frozen_reference=reference.copy();np.save(a.out/'pre-noise-p95.npy',reference,allow_pickle=False)
    captures=[];output=[];forward=4*len(pre_rows);inverse=0;baseline_checks=0
    originals={r['capture']:r for r in summary['reports']}
    for name in sorted(originals):
        pcm,rows=inputs(name);background=name not in markers;tracker=track.Tracker(track.Config(cone_half_angle_deg=60));newrows=[]
        for idx,row in enumerate(rows):
            if name==config['calibration_run']:sp=spectra[idx]
            else:sp=np.fft.rfft(pcm[row['start']:row['stop']].T/2**23*window,axis=1);forward+=4
            power=np.abs(sp)**2;ratio=power[:,7:86]/np.maximum(reference[:,7:86],1e-30);per_bin=np.sort(ratio,axis=0)[1]
            pairrows={k:[] for k in ('full','excess')};effective=[]
            for k,(i,j) in enumerate(diag.PAIRS):
                z=sp[i]*sp[j].conj();amp=np.abs(z);mask=band&(amp>=.02*max(float(amp[band].max()),1e-15));w=gate_weight(power,reference,i,j)*mask
                effective.append(float(w.sum()**2/(w@w)) if w@w>0 else 0.)
                for mode in pairrows:
                    weights=mask.astype(float) if mode=='full' else w;count=int(np.count_nonzero(weights));pr=dict(valid=False,reason='FEWER_THAN_12_BINS',bins=count)
                    if count>=12:
                        corr=np.fft.irfft(z/np.maximum(amp,1e-15)*weights,n=1024);inverse+=1;pr.update(diag.quality(corr,bounds[k],False))
                    pairrows[mode].append(pr)
            full=diag.projection(pairrows['full'],positions,48000,343);old=row['projection'];assert [p['reason'] for p in pairrows['full']]==row['pair_reasons'];assert full.get('advisory_consistent',False)==old.get('advisory_consistent',False)
            for key in ('projection_norm','residual_samples','advisory_azimuth_deg'):
                if key in old:assert np.isclose(full[key],old[key],rtol=1e-12,atol=1e-10)
            baseline_checks+=1;new=diag.projection(pairrows['excess'],positions,48000,343);valid=new.get('advisory_consistent',False);angle=new.get('advisory_azimuth_deg') if valid else None;gate=row['candidates']['band_calibrated_duration']
            if not gate:tracker.reset()
            vec=None if angle is None else [math.cos(math.radians(angle)),math.sin(math.radians(angle)),0]
            state=tracker.update(row['stop']/48,vec,valid and gate)
            r=dict(capture=name,start=row['start'],stop=row['stop'],background=background,marker_excluded=row['marker_excluded'],gate=gate,baseline_valid=full.get('advisory_consistent',False),baseline_fresh=row['trackers']['candidate60']['fresh_valid'],new_valid=valid,new_angle=angle,projection=new,tracker=state,three_channel_excess_bins=int(np.count_nonzero(per_bin>1)),three_channel_4x_bins=int(np.count_nonzero(per_bin>=4)),median_effective_pair_bins=float(np.median(effective)),pair_reasons=[p['reason'] for p in pairrows['excess']])
            newrows.append(r);output.append(r)
        groups={'whole_recording':newrows}
        if not background:
            core=markers[name]['common_source_mapped_interval_samples']
            for ms in (100,200,300):groups[str(ms)]=[r for r in newrows if r['start']>=math.ceil(core[0]+ms*48) and r['stop']<=math.floor(core[1]-ms*48) and not r['marker_excluded']]
        result={}
        for group,chosen in groups.items():
            prior_group='reported_background' if background else group
            if prior_group in originals[name]['sensitivity']:assert len(chosen)==originals[name]['sensitivity'][prior_group]['frames']
            angles=[math.degrees(math.atan2(r['tracker']['direction'][1],r['tracker']['direction'][0])) for r in chosen if r['tracker']['fresh_valid']];nominal=originals[name]['nominal_deg'];errors=[] if nominal is None else [abs((x-nominal+180)%360-180) for x in angles]
            result[group]=dict(frames=len(chosen),gate=sum(r['gate'] for r in chosen),baseline_valid=sum(r['baseline_valid'] for r in chosen),new_valid=sum(r['new_valid'] for r in chosen),newly_accepted=sum(r['new_valid'] and not r['baseline_valid'] for r in chosen),lost=sum(r['baseline_valid'] and not r['new_valid'] for r in chosen),gate_cone=sum(r['new_valid'] and r['gate'] and abs(r['new_angle'])<=60+1e-10 for r in chosen),fresh=len(angles),max_acquire=max((r['tracker']['acquire_count'] for r in chosen),default=0),nominal_deviation_median=None if not errors else float(np.median(errors)),nominal_gt15=sum(v>15 for v in errors) if errors else None,three_channel_excess_bins_median=float(np.median([r['three_channel_excess_bins'] for r in chosen])) if chosen else None,three_channel_4x_bins_median=float(np.median([r['three_channel_4x_bins'] for r in chosen])) if chosen else None,median_effective_pair_bins=float(np.median([r['median_effective_pair_bins'] for r in chosen])) if chosen else None)
        captures.append(dict(capture=name,background=background,split=originals[name]['split'],groups=result));print(name,result.get('200',result['whole_recording']),flush=True)
    assert np.array_equal(reference,frozen_reference)
    dump(a.out/'frames.json',output);dump(a.out/'result.json',dict(protocol=protocol,pins=pins,dependencies=deps,captures=captures,forward_fft_channels=forward,inverse_fft_pairs=inverse,baseline_frames_matched=baseline_checks,reference_sha256=sha(a.out/'pre-noise-p95.npy'),source_sha256=sha(Path(__file__)),formal_acceptance=False))
if __name__=='__main__':main()
