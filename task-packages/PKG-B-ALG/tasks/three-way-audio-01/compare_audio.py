"""Same-input three-way comparison; truth only enters manual reference branch."""
import importlib.util,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'tracked-audio-01'))
spec=importlib.util.spec_from_file_location('previous_tracked_runner',HERE.parent/'tracked-audio-01/run_task.py')
previous=importlib.util.module_from_spec(spec);spec.loader.exec_module(previous)
from tracked_audio import TrackedAudio
from fixed_das import FixedDAS

def fixed(samples,direction,origin,block=512):
    b=FixedDAS(direction);out=[];valid=[]
    for start in range(0,len(samples),block):
        y,v=b.process(samples[start:start+block],first_sample_id=origin+start);out.append(y);valid.append(v)
    return np.concatenate(out),np.concatenate(valid)

def single(samples):
    y=np.zeros(len(samples));y[4:]=samples[:-4,0];return y

def compare(segment,manual_direction):
    # No truth argument or modified metadata goes into the automatic entry.
    auto,auto_valid,rows,modes,events=previous.execute(segment)
    manual,manual_valid=fixed(segment.samples,manual_direction,int(segment.sample_ids[0]))
    return dict(single=single(segment.samples),manual=manual,auto=auto),auto_valid&manual_valid,rows,modes,events

def replay(samples,origin,rows):
    """Replay MIXTURE-derived control on known components; never relocalize them."""
    b=TrackedAudio('single',480,sample_origin=origin);out=[];start=0;pending=None
    for row in rows:
        stop=row['frame_stop']
        if stop>start:
            y,_,_=b.process(samples[start:stop],first_sample_id=origin+start,tracking=pending);out.append(y);start=stop
        pending=row['tracking']
    if start<len(samples):
        y,_,_=b.process(samples[start:],first_sample_id=origin+start,tracking=pending);out.append(y)
    return np.concatenate(out)

def metrics(signals,mask):
    if not np.any(mask):raise ValueError('no shared evaluation samples')
    manual=signals['manual'][mask];power=float(np.mean(manual**2));result={}
    for key,y in signals.items():
        z=y[mask];err=float(np.mean((z-manual)**2))
        result[key]=dict(rms=float(np.sqrt(np.mean(z*z))),peak=float(np.max(np.abs(y))),
            rms_difference_from_manual=float(np.sqrt(err)),normalized_error_to_manual=err/power if power>1e-20 else None)
    return result
