"""Reuse frozen DAS/WAV/Crossfade, vectorize only the offline mixer arithmetic."""
import sys
import numpy as np
from common import TASKS, module

sys.path.insert(0, str(TASKS/'real-audio-compare-01'))
das = module('checkpoint_das', TASKS/'real-audio-compare-01/render_audio.py')
mixer = module('checkpoint_mixer', TASKS/'four-channel-track-01/audio-01/mixer.py')
POSITIONS = np.array([[0,0,0],[.04,0,0],[.04,.04,0],[0,.04,0]])

def mix_fast(bank, start, stop, events, fade):
    """Same frozen Crossfade states/equations; event boundaries split batches."""
    bank = np.asarray(bank, dtype=float)
    if bank.ndim != 2 or bank.shape[1] != stop-start or not np.isfinite(bank).all():
        raise ValueError('invalid bank')
    if any(a['ready'] >= b['ready'] for a,b in zip(events, events[1:])):
        raise ValueError('event order')
    state = mixer.Crossfade(len(bank), fade)
    weights = np.empty((stop-start,len(bank)))
    pos = 0
    n = start
    while n < stop:
        while pos < len(events) and events[pos]['ready'] <= n:
            e = events[pos]
            if e['fresh'] or e['target'] != state.target:
                state.select(e['target'], e['ready'], e['valid_through'])
            pos += 1
        end = min(stop, events[pos]['ready'] if pos < len(events) else stop)
        clock = np.arange(n,end)
        alpha = np.clip((clock-state.start)/fade,0,1)
        w = (1-alpha[:,None])*state.initial
        guard = np.clip((state.expiries[None,1:]+1-clock[:,None])/fade,0,1)
        ratio = np.divide(guard,state.initial_guard,out=np.zeros_like(guard),where=state.initial_guard>0)
        ratio = np.minimum(ratio,1)
        w[:,0] += np.sum(w[:,1:]*(1-ratio),axis=1)
        w[:,1:] *= ratio
        if state.target:
            g = guard[:,state.target-1]
            w[:,state.target] += alpha*g
            w[:,0] += alpha*(1-g)
        else:
            w[:,0] += alpha
        weights[n-start:end-start] = w
        n = end
    if np.any(weights < -1e-14) or not np.allclose(weights.sum(axis=1),1,atol=1e-14,rtol=0):
        raise RuntimeError('nonconvex mix')
    return np.sum(bank.T*weights,axis=1), weights

def render(pcm, manual_deg, events, cfg):
    x = np.asarray(pcm,dtype=float)/2**23
    start, stop = 8,len(x)-8
    if stop <= start: raise ValueError('too short')
    angles = sorted({e['angle'] for e in events if e['angle'] is not None})
    def beam(angle):
        delay = das.delays_for(POSITIONS,0,angle,0,48000,343)
        _, y,a,b = das.render_interval(x,delay)
        if a > start or b < stop: raise ValueError('crop mismatch')
        return y[start-a:stop-a]
    single = x[start:stop,0].copy()
    bank = np.stack([single]+[beam(a) for a in angles])
    commands = [dict(ready=e['ready'], target=0 if e['angle'] is None else 1+angles.index(e['angle']),
                     fresh=e['fresh'],valid_through=e['valid_through']) for e in events]
    auto, weights = mix_fast(bank,start,stop,commands,cfg['audio_fade_samples'])
    return dict(single=single,manual=beam(manual_deg),automatic=auto), dict(
        reference_rows=[start,stop], physical_emit_rows=[start+8,stop+8],
        common_availability_delay_samples=8, assumed_compute_delay_samples=0,
        bank_angles=angles, single_only_samples=int(np.count_nonzero(weights[:,0] == 1)),
        beam_contribution_samples=int(np.count_nonzero(weights[:,0] < 1)),
        max_weight_step=float(np.max(np.abs(np.diff(weights,axis=0)))),
        runtime_implementation='offline cached bank, not a streaming FPGA memory budget')

def measurements(outputs, selection):
    indices = np.asarray(selection,dtype=int)
    ref = outputs['single'][indices]
    ref_power = float(np.mean(ref**2)) if len(indices) else None
    result = {}
    for name, full in outputs.items():
        y = full[indices]
        power = float(np.mean(y*y)) if len(y) else None
        result[name] = dict(samples=len(y),rms=float(np.sqrt(power)) if power is not None else None,
            peak=float(np.max(np.abs(y))) if len(y) else None,
            output_level_change_db_vs_mic0=float(10*np.log10(power/ref_power)) if power and ref_power else None,
            waveform_difference_rms=float(np.sqrt(np.mean((y-ref)**2))) if len(y) else None,
            snr_gain_db=None, speech_quality_gain=None)
    return result
