"""Offline preparation only; no build, download, capture or modification of projects."""
import argparse
import hashlib
import importlib.util
import json
import shutil
import sys
import traceback
import wave
from pathlib import Path
from types import SimpleNamespace
import numpy as np

HERE = Path(__file__).resolve().parents[1]
PREVIOUS = HERE.parent / 'background-target-stop-20260917'
APP = Path('F:/College/verilog_digital_system/Vitis/four_mic_endurance')
POST = APP / 'scene_checks/20260917_150930_post_63989c521b/result.json'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

def chirp(fs, duration, f0, f1):
    t = np.arange(round(fs*duration))/fs
    phase = 2*np.pi*(f0*t+(f1-f0)/(2*duration)*t*t)
    return np.sin(phase)*np.hanning(len(t))

def write_wav(path, pcm, fs=48000):
    with wave.open(str(path), 'wb') as w:
        w.setparams((1, 2, fs, 0, 'NONE', 'not compressed'))
        w.writeframes(np.asarray(pcm, dtype='<i2').tobytes())

def playback(speech_dir, out):
    out.mkdir(parents=True, exist_ok=False)
    original = speech_dir/'speech-original.wav'
    with wave.open(str(original), 'rb') as w:
        if (w.getnchannels(),w.getsampwidth(),w.getframerate()) != (1,2,48000):
            raise ValueError('Expected 48 kHz mono signed16 speech')
        speech = np.frombuffer(w.readframes(w.getnframes()),dtype='<i2').astype(float)
    active = np.flatnonzero(np.abs(speech)>64)
    if not len(active): raise ValueError('Generated speech is empty')
    # Trim only generated SOURCE silence; never trim, normalize or filter acquired PCM.
    lo=max(0,int(active[0])-480); hi=min(len(speech),int(active[-1])+481)
    phrase=speech[lo:hi]
    if len(phrase)>round(2.2*48000): raise ValueError('Speech exceeds 2.2 s budget')
    phrase=phrase*(0.42*32767/np.max(np.abs(phrase)))
    pcm=np.zeros(round(4.8*48000),dtype=float)
    markers=[]
    for name,start,f0,f1 in [('start',0.2,900,3300),('end',4.45,3300,900)]:
        mark=np.rint(chirp(48000,0.15,f0,f1)*0.25*32767).astype('<i2')
        offset=round(start*48000);pcm[offset:offset+len(mark)]=mark
        write_wav(out/f'marker-{name}.wav', mark)
        markers.append(dict(name=name,start_sample=offset,end_sample_exclusive=offset+len(mark),file=f'marker-{name}.wav'))
    a=48000;pcm[a:a+len(phrase)]=phrase
    audio=np.rint(pcm).astype('<i2');write_wav(out/'soundsight-target-v1.wav',audio)
    with wave.open(str(out/'soundsight-target-v1.wav'),'rb') as w:
        assert w.getnframes()==230400 and w.readframes(w.getnframes())==audio.tobytes()
    shutil.copyfile(original,out/'speech-original.wav')
    shutil.copyfile(speech_dir/'speech-generation.json',out/'speech-generation.json')
    save(out/'timeline.json',dict(sample_rate_hz=48000,duration_seconds=4.8,total_samples=len(audio),
        source_kind='locally synthesized speech plus two distinct tapered chirps',
        markers=markers,speech_source_interval=[a,a+len(phrase)],
        original_speech_sha256=sha(original),original_source_trim_samples=[lo,hi],
        source_speech_peak_fraction=0.42,source_marker_peak_fraction=0.25,
        pcm16_peak=int(np.max(np.abs(audio.astype(int)))),
        marker_guard_seconds_provisional=0.2,
        capture_activity_labels='UNKNOWN until acoustic alignment and waveform review; source schedule is NOT exact acoustic truth',
        score_exclusions='Both markers plus acoustic reverberation guard; extend exclusion if ringing persists',
        no_clean_reference_claim=True))
    save(out/'sha256.json',{p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file()})
    print('PLAYBACK_PREPARED_NOT_ACOUSTICALLY_VALIDATED',out)

def preflight(out):
    out.mkdir(parents=True,exist_ok=False)
    save(out/'request.json',dict(operation='read-only reuse of check_scene.verify(stage=load)',
        app=str(APP),prior_post=str(POST),new_compilation=False,board_run=False,argv=sys.argv))
    try:
        receipt=json.loads(POST.read_text(encoding='utf-8'))
        # Use the frozen original checker unmodified. Call its verification API because
        # its CLI restricts receipts to the previous increment/app. Only output routing differs.
        for name,digest in receipt['verifier_sha256'].items():
            if sha(PREVIOUS/name)!=digest: raise ValueError('Verifier changed: '+name)
        reference=out/'reference-post';reference.mkdir()
        shutil.copyfile(POST,reference/'result.json')
        checker=load_module('trusted_scene_checker',PREVIOUS/'check_scene.py')
        args=SimpleNamespace(stage='load',app=str(APP),platform=str(APP.parent/'continuous_platform'),
            tools_bin='F:/AMD/2025.2/Vitis/gnu/aarch32/nt/gcc-arm-none-eabi/bin',record_root=str(out))
        report=checker.verify(args,out)
        report.update(status='REUSED_S1_LOAD_PREFLIGHT_PASS_NOT_BOARD',new_compilation=False,
            previous_build_receipt_sha256=sha(POST),checker_sha256=sha(PREVIOUS/'check_scene.py'))
        save(out/'result.json',report)
        shutil.copyfile(APP/'_ide/launch.json',out/'launch.json')
        print(report['status'],out)
    except Exception as exc:
        save(out/'failure.json',dict(status='FAILED',error=str(exc),traceback=traceback.format_exc()))
        raise

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('playback');a.add_argument('--speech-dir',type=Path,required=True);a.add_argument('--out',type=Path,required=True)
    a=sub.add_parser('preflight');a.add_argument('--out',type=Path,required=True)
    a=p.parse_args()
    if a.cmd=='playback':playback(a.speech_dir,a.out)
    else:preflight(a.out)

if __name__=='__main__': main()
